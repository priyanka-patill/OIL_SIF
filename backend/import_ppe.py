import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.session import SessionLocal, init_db
from app.services.dataset_service import DatasetService
from app.services.quality_service import QualityService


def import_ppe_dataset(file_path: str = None):
    if not file_path:
        # Check standard relative path or user downloads
        candidates = [
            os.path.join(os.path.dirname(backend_dir), "data", "datasets", "PPE_Noncomplaince.xlsx"),
            os.path.join(os.path.dirname(backend_dir), "PPE_Noncomplaince.xlsx"),
            r"C:\Users\sahan\Downloads\PPE_Noncomplaince.xlsx"
        ]
        for c in candidates:
            if os.path.exists(c):
                file_path = c
                break

    if not file_path or not os.path.exists(file_path):
        print(f"[ERROR] Could not find PPE_Noncomplaince.xlsx at {file_path}")
        return None

    print(f"[*] Initializing Database...")
    init_db()

    db = SessionLocal()
    try:
        print(f"[*] Reading dataset file from: {file_path}")
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        filename = os.path.basename(file_path)
        print(f"[*] Ingesting dataset '{filename}' ({len(file_bytes)} bytes)...")

        dataset = DatasetService.ingest_dataset(
            db=db,
            file_bytes=file_bytes,
            filename=filename,
            file_type="xlsx",
            dataset_name="PPE Non-Compliance Near-Miss Dataset",
            description="Official OIL Near-Miss and Unsafe Act dataset for PPE non-compliance records.",
            client_host="cli_importer"
        )

        print("\n" + "=" * 60)
        print("  PPE DATASET INGESTION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Dataset ID:         {dataset.id}")
        print(f"Dataset Name:       {dataset.dataset_name}")
        print(f"Original Filename:  {dataset.original_filename}")
        print(f"Row Count:          {dataset.row_count} records")
        print(f"Column Count:       {dataset.column_count} columns")
        print(f"Status:             {dataset.status}")

        # Fetch Schema info
        schema_info = DatasetService.get_dataset_schema(db, dataset.id)
        print("\n--- DETECTED SCHEMA & SEMANTIC MAPPING ---")
        for col in schema_info["columns"]:
            const_flag = f"[CONSTANT = {col.constant_value}]" if col.is_constant else ""
            mapped_str = f"-> canonical '{col.mapped_canonical_field}'" if col.mapped_canonical_field else "[unmapped]"
            print(f"  * {col.original_name:30} | Type: {col.detected_data_type:8} | Semantic: {col.semantic_type:10} {mapped_str} {const_flag}")

        print(f"\n--- CONSTANT FIELDS DETECTED ({len(schema_info['constant_fields'])}) ---")
        for cfield in schema_info["constant_fields"]:
            print(f"  * {cfield.original_name}: constant value = '{cfield.constant_value}' (unique count: {cfield.unique_count})")

        # Fetch Quality info
        quality = QualityService.get_quality_by_dataset_id(db, dataset.id)
        if quality:
            print("\n--- DATA QUALITY SCORECARD ---")
            print(f"Overall Health Score:  {quality['data_quality_score']}%")
            print(f"Valid Records:         {quality['valid_records_count']} / {quality['total_rows']}")
            print(f"Missing Values:        {quality['missing_values_count']}")
            print(f"Duplicate IDs:         {quality['duplicate_ids_count']}")
            print(f"Invalid Dates:         {quality['invalid_dates_count']}")
            print(f"Date Span:             {quality['date_range_start']} to {quality['date_range_end']}")
            print("Summary Notes:")
            for note in quality['summary_notes']:
                print(f"  - {note}")

        print("=" * 60 + "\n")
        return dataset

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Ingestion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else None
    import_ppe_dataset(target_file)
