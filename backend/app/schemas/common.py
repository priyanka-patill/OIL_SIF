from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    total_datasets: int
    total_reports: int
