from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.export import ExportPreviewResponse
from app.services.report_export_service import ReportExportService

router = APIRouter(prefix="/reports/export", tags=["Report Generation & Export"])


@router.get("/preview", response_model=ExportPreviewResponse)
def get_export_preview(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    department: Optional[str] = Query(None, description="Filter by department"),
    refinery_unit: Optional[str] = Query(None, description="Filter by refinery unit"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    action_status: Optional[str] = Query(None, description="Filter by action status"),
    date_from: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Generate telemetry preview of matching reports before downloading.
    """
    return ReportExportService.get_export_preview(
        db=db,
        dataset_id=dataset_id,
        risk_level=risk_level,
        department=department,
        refinery_unit=refinery_unit,
        report_type=report_type,
        action_status=action_status,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/pdf")
def export_pdf_report(
    dataset_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    refinery_unit: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    action_status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Generate and stream Executive Safety Intelligence PDF Report.
    """
    pdf_bytes = ReportExportService.generate_pdf_report(
        db=db,
        dataset_id=dataset_id,
        risk_level=risk_level,
        department=department,
        refinery_unit=refinery_unit,
        report_type=report_type,
        action_status=action_status,
        date_from=date_from,
        date_to=date_to
    )
    filename = f"OIL_Safety_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/excel")
def export_excel_report(
    dataset_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    refinery_unit: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    action_status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Generate and stream Multi-Sheet Excel Safety Workbook (.xlsx).
    """
    excel_bytes = ReportExportService.generate_excel_report(
        db=db,
        dataset_id=dataset_id,
        risk_level=risk_level,
        department=department,
        refinery_unit=refinery_unit,
        report_type=report_type,
        action_status=action_status,
        date_from=date_from,
        date_to=date_to
    )
    filename = f"OIL_Safety_Data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/csv")
def export_csv_report(
    dataset_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    refinery_unit: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    action_status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Generate and stream standard CSV Safety Report.
    """
    csv_text = ReportExportService.generate_csv_report(
        db=db,
        dataset_id=dataset_id,
        risk_level=risk_level,
        department=department,
        refinery_unit=refinery_unit,
        report_type=report_type,
        action_status=action_status,
        date_from=date_from,
        date_to=date_to
    )
    filename = f"OIL_Safety_Export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
