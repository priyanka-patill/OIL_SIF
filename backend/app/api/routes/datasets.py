from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request, status, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import PaginatedResponse, StatusResponse
from app.schemas.dataset import DatasetResponse, DatasetDetailResponse, DatasetSchemaResponse
from app.schemas.factors import DatasetComparisonResponse
from app.services.dataset_service import DatasetService
from app.utils.validators import validate_file_upload

router = APIRouter(prefix="/datasets", tags=["Dataset Management & Ingestion"])


@router.get("", response_model=PaginatedResponse[DatasetResponse])
def list_datasets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List all registered safety datasets in the platform."""
    items, total = DatasetService.get_datasets(db=db, page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    request: Request,
    file: UploadFile = File(..., description="Dataset file (.xlsx, .csv, .json)"),
    dataset_name: Optional[str] = Form(None, description="Custom dataset display name"),
    description: Optional[str] = Form(None, description="Dataset description"),
    db: Session = Depends(get_db)
):
    """
    Upload a safety dataset. Performs dynamic schema detection, constant-field analysis, 
    canonical normalization, and data quality profiling.
    """
    contents = await file.read()
    file_type, _ = validate_file_upload(file.filename or "", len(contents))
    
    client_host = request.client.host if request.client else None
    
    dataset = DatasetService.ingest_dataset(
        db=db,
        file_bytes=contents,
        filename=file.filename or "uploaded_dataset",
        file_type=file_type,
        dataset_name=dataset_name,
        description=description,
        client_host=client_host
    )
    return dataset


@router.get("/compare", response_model=DatasetComparisonResponse)
def compare_datasets(
    dataset_a: str = Query(..., description="ID of Dataset A"),
    dataset_b: str = Query(..., description="ID of Dataset B"),
    db: Session = Depends(get_db)
):
    """Compare two safety datasets across risk distributions, factors, causes, and consequences."""
    from app.services.factor_service import FactorService
    return FactorService.compare_datasets(db=db, dataset_id_a=dataset_a, dataset_id_b=dataset_b)


@router.post("/ingest-workbook", response_model=list[DatasetResponse], status_code=status.HTTP_201_CREATED)
async def ingest_multi_sheet_workbook(
    request: Request,
    file: UploadFile = File(..., description="Multi-sheet Excel workbook (.xlsx)"),
    db: Session = Depends(get_db)
):
    """
    Ingest a complete multi-dataset Excel workbook (e.g. Indian_Refinery_Near_Miss_Datasets.xlsx).
    Preserves all 13 sheets, detects factors, separates summary metadata, and auto-runs SIF analysis.
    """
    contents = await file.read()
    client_host = request.client.host if request.client else None
    datasets = DatasetService.ingest_multi_sheet_workbook(
        db=db,
        file_bytes=contents,
        filename=file.filename or "multi_dataset_workbook.xlsx",
        client_host=client_host
    )
    return datasets


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve detailed dataset information including columns metadata."""
    dataset = DatasetService.get_dataset_by_id(db=db, dataset_id=dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/factors")
def get_dataset_factors(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve safety factor summary and frequencies specific to a dataset."""
    from app.services.factor_service import FactorService
    return FactorService.get_factor_summary(db=db, dataset_id=dataset_id)


@router.get("/{dataset_id}/risk-summary")
def get_dataset_risk_summary(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve risk breakdown for a specific dataset."""
    from app.services.sif_service import SIFService
    return SIFService.get_sif_summary(db=db, dataset_id=dataset_id)


@router.get("/{dataset_id}/schema", response_model=DatasetSchemaResponse)
def get_dataset_schema(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve dynamically detected schema, column data types, constant fields, 
    and canonical field mappings.
    """
    schema_info = DatasetService.get_dataset_schema(db=db, dataset_id=dataset_id)
    if not schema_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return schema_info


@router.delete("/{dataset_id}", response_model=StatusResponse)
def delete_dataset(
    dataset_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a dataset and all associated columns, reports, and quality summaries."""
    client_host = request.client.host if request.client else None
    success = DatasetService.delete_dataset(db=db, dataset_id=dataset_id, client_host=client_host)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return StatusResponse(
        status="success",
        message=f"Dataset {dataset_id} deleted successfully"
    )

