import uuid
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
import pandas as pd

from app.models.dataset import Dataset
from app.models.dataset_column import DatasetColumn
from app.models.safety_report import SafetyReport
from app.models.data_quality import DataQualitySummary
from app.ingestion.file_reader import FileReader
from app.ingestion.schema_detector import SchemaDetector
from app.ingestion.semantic_mapper import SemanticMapper
from app.ingestion.normalizer import DataNormalizer
from app.analytics.profiler import DataQualityEngine
from app.services.audit_service import AuditService


class DatasetService:
    @staticmethod
    def classify_dataset(
        sheet_name: str,
        df: pd.DataFrame
    ) -> Tuple[str, int, List[str], bool, bool]:
        """
        Classifies sheet into (dataset_type, factor_count, factor_names, is_derived, is_summary).
        """
        clean_sheet = sheet_name.strip()
        if "summary" in clean_sheet.lower() or clean_sheet == "00_Summary":
            return "summary", 0, [], False, True

        # Detect active factors in this dataset
        active_factors = []
        standard_factor_cols = [
            "PPE_NonCompliance", "Supervisor_Negligence", 
            "Maintenance_Delay_or_Issue", "Repeated_Issue_Ignored"
        ]
        for col in standard_factor_cols:
            if col in df.columns:
                # Check if any True / truthy value in series
                try:
                    s_bool = df[col].astype(str).str.strip().str.lower()
                    if (s_bool.isin(["true", "1", "yes", "t"])).any():
                        active_factors.append(col)
                except Exception:
                    pass

        # Check for dynamic factor columns (e.g. Permit_Violation, Isolation_Failure)
        for col in df.columns:
            if col not in standard_factor_cols and col not in ["High_Potential_Near_Miss", "Previous_Similar_Reports"]:
                if any(term in col.lower() for term in ["violation", "failure", "negligence", "delay", "hazard_factor", "factor"]):
                    try:
                        s_bool = df[col].astype(str).str.strip().str.lower()
                        if (s_bool.isin(["true", "1", "yes", "t"])).any():
                            active_factors.append(col)
                    except Exception:
                        pass

        factor_count = len(active_factors)

        if "high_potential" in clean_sheet.lower() or clean_sheet.startswith("12_"):
            return "high_potential", factor_count, active_factors, True, False

        if factor_count <= 1:
            return "single_factor", factor_count, active_factors, False, False

        return "multi_factor", factor_count, active_factors, True, False

    @staticmethod
    def ingest_dataset(
        db: Session,
        file_bytes: bytes,
        filename: str,
        file_type: str,
        dataset_name: Optional[str] = None,
        description: Optional[str] = None,
        client_host: Optional[str] = None
    ) -> Dataset:
        if not dataset_name:
            dataset_name = filename.rsplit(".", 1)[0]

        # 1. Read file into DataFrame
        df = FileReader.read_file(file_bytes, filename)
        row_count = len(df)
        column_count = len(df.columns)
        file_size = len(file_bytes)

        # 2. Classify Dataset Hierarchy
        ds_type, factor_cnt, factor_names, is_derived, is_summary = DatasetService.classify_dataset(dataset_name, df)

        # 3. Dynamic Schema Detection
        raw_columns_meta = SchemaDetector.analyze_schema(df)
        
        # 4. Semantic Mapping & Metadata Enrichment
        columns_meta = [
            SemanticMapper.enrich_column_metadata(col_meta)
            for col_meta in raw_columns_meta
        ]

        # 5. Create Dataset entity
        dataset_id = str(uuid.uuid4())
        dataset = Dataset(
            id=dataset_id,
            dataset_name=dataset_name,
            original_filename=filename,
            sheet_name=dataset_name,
            file_type=file_type,
            dataset_type=ds_type,
            factor_count=factor_cnt,
            factor_names=factor_names,
            file_size_bytes=file_size,
            row_count=row_count,
            column_count=column_count,
            status="ready",
            data_quality_status="PASSED",
            is_derived_dataset=is_derived,
            is_summary_dataset=is_summary,
            description=description,
            is_active=True
        )
        db.add(dataset)
        db.flush()

        # 6. Persist Dataset Columns
        for col_info in columns_meta:
            col_record = DatasetColumn(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                column_index=col_info["column_index"],
                original_name=col_info["original_name"],
                sanitized_name=col_info["sanitized_name"],
                detected_data_type=col_info["detected_data_type"],
                semantic_type=col_info["semantic_type"],
                is_nullable=col_info["is_nullable"],
                null_count=col_info["null_count"],
                unique_count=col_info["unique_count"],
                is_constant=col_info["is_constant"],
                constant_value=col_info["constant_value"],
                sample_values=col_info["sample_values"],
                mapped_canonical_field=col_info["mapped_canonical_field"]
            )
            db.add(col_record)

        # 7. Normalize & Persist Safety Reports (Skip if summary sheet)
        if not is_summary:
            reports = DataNormalizer.normalize_dataframe(
                df=df,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                columns_meta=columns_meta
            )
            for report in reports:
                db.add(report)

        # 8. Calculate & Persist Data Quality Profile
        quality_summary = DataQualityEngine.calculate_quality_summary(
            df=df,
            dataset_id=dataset_id,
            columns_meta=columns_meta
        )
        db.add(quality_summary)

        # Commit everything in a clean atomic transaction
        db.commit()
        # 9. Trigger Multi-Factor Correlation Computation
        if not is_summary and row_count > 0:
            try:
                from app.services.correlation_service import CorrelationService
                CorrelationService.batch_compute_correlations(db=db, dataset_id=dataset_id)
            except Exception as ex:
                print(f"Correlation computation notice: {ex}")

        # 10. Audit Log
        AuditService.log_action(
            db=db,
            action_type="DATASET_INGESTION_COMPLETED",
            entity_type="DATASET",
            entity_id=dataset_id,
            details={
                "dataset_name": dataset_name,
                "filename": filename,
                "rows": row_count,
                "columns": column_count,
                "dataset_type": ds_type,
                "factors": factor_names,
                "quality_score": quality_summary.data_quality_score
            },
            client_host=client_host
        )

        return dataset

    @staticmethod
    def ingest_multi_sheet_workbook(
        db: Session,
        file_bytes: bytes,
        filename: str,
        client_host: Optional[str] = None
    ) -> List[Dataset]:
        """
        Ingests an entire multi-sheet Excel workbook (e.g. Indian_Refinery_Near_Miss_Datasets.xlsx),
        preserving sheet identity, factor classifications, summary segregation, and triggering batch AI analysis.
        """
        # 1. Idempotency Check: if sheets for this workbook already exist, return them
        existing = list(db.scalars(
            select(Dataset).where(Dataset.parent_dataset == filename, Dataset.is_active == True)
        ).all())
        if existing and len(existing) >= 12:
            return existing

        sheets_dict = FileReader.read_workbook_sheets(file_bytes, filename)
        created_datasets: List[Dataset] = []
        file_size = len(file_bytes)

        # Import SIFService lazily to avoid circular import
        from app.services.sif_service import SIFService

        for sheet_name, df in sheets_dict.items():
            # Check if this specific sheet is already ingested
            existing_sheet = db.scalar(
                select(Dataset).where(
                    Dataset.parent_dataset == filename,
                    Dataset.sheet_name == sheet_name,
                    Dataset.is_active == True
                )
            )
            if existing_sheet:
                created_datasets.append(existing_sheet)
                continue

            row_count = len(df)
            column_count = len(df.columns)
            ds_type, factor_cnt, factor_names, is_derived, is_summary = DatasetService.classify_dataset(sheet_name, df)

            raw_columns_meta = SchemaDetector.analyze_schema(df)
            columns_meta = [
                SemanticMapper.enrich_column_metadata(col_meta)
                for col_meta in raw_columns_meta
            ]

            dataset_id = str(uuid.uuid4())
            dataset = Dataset(
                id=dataset_id,
                dataset_name=sheet_name,
                original_filename=filename,
                sheet_name=sheet_name,
                file_type="xlsx",
                dataset_type=ds_type,
                factor_count=factor_cnt,
                factor_names=factor_names,
                file_size_bytes=file_size,
                row_count=row_count,
                column_count=column_count,
                status="ready",
                data_quality_status="PASSED",
                is_derived_dataset=is_derived,
                is_summary_dataset=is_summary,
                parent_dataset=filename,
                description=f"Automated ingestion of sheet '{sheet_name}' from {filename}",
                is_active=True
            )
            db.add(dataset)
            db.flush()

            # Persist column definitions
            for col_info in columns_meta:
                col_record = DatasetColumn(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset_id,
                    column_index=col_info["column_index"],
                    original_name=col_info["original_name"],
                    sanitized_name=col_info["sanitized_name"],
                    detected_data_type=col_info["detected_data_type"],
                    semantic_type=col_info["semantic_type"],
                    is_nullable=col_info["is_nullable"],
                    null_count=col_info["null_count"],
                    unique_count=col_info["unique_count"],
                    is_constant=col_info["is_constant"],
                    constant_value=col_info["constant_value"],
                    sample_values=col_info["sample_values"],
                    mapped_canonical_field=col_info["mapped_canonical_field"]
                )
                db.add(col_record)

            # Persist safety reports (only for operational sheets, NOT summary)
            if not is_summary:
                reports = DataNormalizer.normalize_dataframe(
                    df=df,
                    dataset_id=dataset_id,
                    dataset_name=sheet_name,
                    columns_meta=columns_meta
                )
                for report in reports:
                    db.add(report)

            # Calculate and persist data quality
            quality_summary = DataQualityEngine.calculate_quality_summary(
                df=df,
                dataset_id=dataset_id,
                columns_meta=columns_meta
            )
            db.add(quality_summary)

            db.commit()
            db.refresh(dataset)
            created_datasets.append(dataset)

            # Automatically run batch AI SIF analysis & correlation computation on operational dataset
            if not is_summary and row_count > 0:
                try:
                    SIFService.batch_analyze_dataset(db=db, dataset_id=dataset.id)
                except Exception as ex:
                    print(f"Batch analysis notice for {sheet_name}: {ex}")
                try:
                    from app.services.correlation_service import CorrelationService
                    CorrelationService.batch_compute_correlations(db=db, dataset_id=dataset.id)
                except Exception as ex:
                    print(f"Correlation computation notice for {sheet_name}: {ex}")

        # Audit log for entire workbook ingestion
        AuditService.log_action(
            db=db,
            action_type="MULTI_DATASET_WORKBOOK_INGESTED",
            entity_type="DATASET_CORPUS",
            entity_id=filename,
            details={
                "filename": filename,
                "sheets_ingested": len(created_datasets),
                "total_operational_sheets": sum(1 for d in created_datasets if not d.is_summary_dataset)
            },
            client_host=client_host
        )

        return created_datasets


    @staticmethod
    def get_datasets(
        db: Session,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dataset], int]:
        query = select(Dataset).where(Dataset.is_active == True).order_by(desc(Dataset.created_at))
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        offset = (page - 1) * page_size
        items = list(db.scalars(query.offset(offset).limit(page_size)).all())
        return items, total

    @staticmethod
    def get_dataset_by_id(db: Session, dataset_id: str) -> Optional[Dataset]:
        return db.scalar(select(Dataset).where(Dataset.id == dataset_id, Dataset.is_active == True))

    @staticmethod
    def get_dataset_schema(db: Session, dataset_id: str) -> Optional[Dict[str, Any]]:
        dataset = db.scalar(select(Dataset).where(Dataset.id == dataset_id, Dataset.is_active == True))
        if not dataset:
            return None
        
        columns = list(db.scalars(
            select(DatasetColumn)
            .where(DatasetColumn.dataset_id == dataset_id)
            .order_by(DatasetColumn.column_index)
        ).all())

        constant_fields = [col for col in columns if col.is_constant]
        mapped_count = sum(1 for col in columns if col.mapped_canonical_field is not None)
        unmapped_count = len(columns) - mapped_count

        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.dataset_name,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "columns": columns,
            "constant_fields": constant_fields,
            "mapped_fields_count": mapped_count,
            "unmapped_fields_count": unmapped_count
        }

    @staticmethod
    def delete_dataset(db: Session, dataset_id: str, client_host: Optional[str] = None) -> bool:
        dataset = db.scalar(select(Dataset).where(Dataset.id == dataset_id))
        if not dataset:
            return False
        db.delete(dataset)
        db.commit()

        AuditService.log_action(
            db=db,
            action_type="DATASET_DELETED",
            entity_type="DATASET",
            entity_id=dataset_id,
            client_host=client_host
        )
        return True
