from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.data_quality import DataQualityResponse
from app.services.quality_service import QualityService

router = APIRouter(prefix="/data-quality", tags=["Data Quality & Profiling Engine"])


@router.get("/{dataset_id}", response_model=DataQualityResponse)
def get_dataset_quality(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve automated data quality scorecard for a dataset, including completeness, 
    duplicate counts, invalid dates, constant fields, and column-by-column metrics.
    """
    quality = QualityService.get_quality_by_dataset_id(db=db, dataset_id=dataset_id)
    if not quality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data quality summary not found for dataset {dataset_id}"
        )
    return quality
