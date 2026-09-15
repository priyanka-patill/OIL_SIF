from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.factor_service import FactorService
from app.schemas.factors import (
    FactorSummaryResponse,
    FactorCombinationsResponse,
    DatasetComparisonResponse,
    HighPotentialIntelligenceResponse
)

router = APIRouter(prefix="/factors", tags=["Safety Factors & Combinations"])


@router.get(
    "/summary",
    response_model=FactorSummaryResponse,
    summary="Get overall safety factor summary and frequencies"
)
def get_factor_summary(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    return FactorService.get_factor_summary(db=db, dataset_id=dataset_id)


@router.get(
    "/combinations",
    response_model=FactorCombinationsResponse,
    summary="Get 1-factor, 2-factor, 3-factor, 4-factor combinations and danger ranking"
)
def get_factor_combinations(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    db: Session = Depends(get_db)
):
    return FactorService.get_factor_combinations(db=db, dataset_id=dataset_id)


@router.get(
    "/high-potential",
    response_model=HighPotentialIntelligenceResponse,
    summary="Get dedicated High Potential Near Miss intelligence and multi-barrier failure patterns"
)
def get_high_potential_intelligence(
    db: Session = Depends(get_db)
):
    return FactorService.get_high_potential_intelligence(db=db)
