import io
import csv
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)

from app.models.safety_report import SafetyReport
from app.models.report_analysis import ReportAnalysis
from app.services.sif_service import SIFService
from app.schemas.export import ExportPreviewResponse


class ReportExportService:
    @staticmethod
    def _get_filtered_query(
        db: Session,
        dataset_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        department: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        report_type: Optional[str] = None,
        action_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ):
        query = select(SafetyReport)
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)
        if risk_level:
            query = query.where(func.lower(SafetyReport.risk_level) == risk_level.lower())
        if department:
            query = query.where(func.lower(SafetyReport.department) == department.lower())
        if refinery_unit:
            query = query.where(func.lower(SafetyReport.refinery_unit) == refinery_unit.lower())
        if report_type:
            query = query.where(func.lower(SafetyReport.report_type) == report_type.lower())
        if action_status:
            query = query.where(func.lower(SafetyReport.action_status) == action_status.lower())
        if date_from:
            query = query.where(SafetyReport.report_date >= date_from)
        if date_to:
            query = query.where(SafetyReport.report_date <= date_to)

        return query

    @staticmethod
    def get_export_preview(
        db: Session,
        dataset_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        department: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        report_type: Optional[str] = None,
        action_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> ExportPreviewResponse:
        q = ReportExportService._get_filtered_query(
            db, dataset_id, risk_level, department, refinery_unit, report_type, action_status, date_from, date_to
        )
        reports = list(db.scalars(q).all())
        total = len(reports)

        by_risk: Dict[str, int] = {}
        by_dept: Dict[str, int] = {}
        by_unit: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        sif_cnt = 0
        overdue_cnt = 0

        for r in reports:
            rk = r.risk_level or "Unassigned"
            by_risk[rk] = by_risk.get(rk, 0) + 1

            dp = r.department or "Unassigned"
            by_dept[dp] = by_dept.get(dp, 0) + 1

            un = r.refinery_unit or "Unassigned"
            by_unit[un] = by_unit.get(un, 0) + 1

            st = r.action_status or "Open"
            by_status[st] = by_status.get(st, 0) + 1

            if (r.sif_precursor is True) or ((r.risk_level or "").lower() == "high"):
                sif_cnt += 1
            if (r.action_status or "").lower() == "overdue":
                overdue_cnt += 1

        active_filters = {}
        if dataset_id: active_filters["dataset_id"] = dataset_id
        if risk_level: active_filters["risk_level"] = risk_level
        if department: active_filters["department"] = department
        if refinery_unit: active_filters["refinery_unit"] = refinery_unit
        if report_type: active_filters["report_type"] = report_type
        if action_status: active_filters["action_status"] = action_status
        if date_from: active_filters["date_from"] = date_from.isoformat()
        if date_to: active_filters["date_to"] = date_to.isoformat()

        return ExportPreviewResponse(
            total_matching_reports=total,
            by_risk_level=by_risk,
            by_department=by_dept,
            by_refinery_unit=by_unit,
            by_action_status=by_status,
            sif_precursor_count=sif_cnt,
            overdue_count=overdue_cnt,
            active_filters_applied=active_filters
        )

    # -------------------------------------------------------------
    # 1. PDF GENERATION (ReportLab)
    # -------------------------------------------------------------
    @staticmethod
    def generate_pdf_report(
        db: Session,
        dataset_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        department: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        report_type: Optional[str] = None,
        action_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> bytes:
        q = ReportExportService._get_filtered_query(
            db, dataset_id, risk_level, department, refinery_unit, report_type, action_status, date_from, date_to
        )
        reports = list(db.scalars(q.order_by(SafetyReport.report_date.desc().nullslast())).all())
        sif_summary = SIFService.get_sif_summary(db, dataset_id)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )
        h2_style = ParagraphStyle(
            'H2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#0284C7'),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#1E293B')
        )
        callout_style = ParagraphStyle(
            'Callout',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        table_hdr_style = ParagraphStyle(
            'TableHdr',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white
        )
        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )

        story = []

        # --- HEADER & TITLE ---
        story.append(Paragraph("OIL REFINERY SAFETY & SIF INTELLIGENCE REPORT", title_style))
        gen_time = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")
        story.append(Paragraph(f"Executive Safety Governance & Incident Precursor Analysis • Generated on {gen_time}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceBefore=0, spaceAfter=12))

        # --- SECTION 1: EXECUTIVE SUMMARY ---
        story.append(Paragraph("1. Executive Summary & Operational Safety Telemetry", h2_style))
        total_reports = len(reports)
        high_risk_cnt = sum(1 for r in reports if (r.risk_level or "").lower() == "high")
        overdue_cnt = sum(1 for r in reports if (r.action_status or "").lower() == "overdue")
        open_cnt = sum(1 for r in reports if (r.action_status or "").lower() == "open")

        exec_text = (
            f"This safety intelligence report analyzes <b>{total_reports} safety reports</b>. "
            f"There are currently <b>{high_risk_cnt} High-Risk events</b> flagged across active process units. "
            f"Corrective action governance indicates <b>{overdue_cnt} Overdue Action Items</b> requiring immediate escalation, "
            f"and <b>{open_cnt} Open Actions</b> undergoing field mitigation. "
            f"SIF Precursor intelligence models evaluated an overall precursor detection rate of <b>{sif_summary.get('sif_precursor_rate_percentage', 0)}%</b>."
        )
        story.append(Paragraph(exec_text, body_style))
        story.append(Spacer(1, 8))

        # KPI Summary Table
        kpi_data = [
            [
                Paragraph("<b>Total Filtered Reports</b>", table_cell_style),
                Paragraph("<b>High-Risk Observations</b>", table_cell_style),
                Paragraph("<b>Overdue Actions</b>", table_cell_style),
                Paragraph("<b>SIF Precursors Detected</b>", table_cell_style)
            ],
            [
                Paragraph(f"<font size=12 color='#0284C7'><b>{total_reports}</b></font>", table_cell_style),
                Paragraph(f"<font size=12 color='#DC2626'><b>{high_risk_cnt}</b></font>", table_cell_style),
                Paragraph(f"<font size=12 color='#EA580C'><b>{overdue_cnt}</b></font>", table_cell_style),
                Paragraph(f"<font size=12 color='#7C3AED'><b>{sif_summary.get('sif_precursors_detected', 0)}</b></font>", table_cell_style)
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[130, 130, 130, 150])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 12))

        # --- SECTION 2: RISK DISTRIBUTION ---
        risk_counts: Dict[str, int] = {}
        for r in reports:
            rk = r.risk_level or "Unassigned"
            risk_counts[rk] = risk_counts.get(rk, 0) + 1

        if risk_counts:
            story.append(Paragraph("2. Risk Level Distribution", h2_style))
            risk_table_data = [[
                Paragraph("<b>Risk Category</b>", table_hdr_style),
                Paragraph("<b>Report Count</b>", table_hdr_style),
                Paragraph("<b>Percentage</b>", table_hdr_style)
            ]]
            for rk, count in sorted(risk_counts.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_reports * 100) if total_reports > 0 else 0
                risk_table_data.append([
                    Paragraph(rk, table_cell_style),
                    Paragraph(str(count), table_cell_style),
                    Paragraph(f"{pct:.1f}%", table_cell_style)
                ])
            risk_table = Table(risk_table_data, colWidths=[200, 170, 170])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(risk_table)
            story.append(Spacer(1, 10))

        # --- SECTION 3: REFINERY UNIT ANALYSIS ---
        unit_counts: Dict[str, int] = {}
        for r in reports:
            if r.refinery_unit:
                unit_counts[r.refinery_unit] = unit_counts.get(r.refinery_unit, 0) + 1

        if unit_counts:
            story.append(Paragraph("3. Refinery Process Unit Analysis", h2_style))
            unit_table_data = [[
                Paragraph("<b>Refinery Unit</b>", table_hdr_style),
                Paragraph("<b>Total Reports</b>", table_hdr_style),
                Paragraph("<b>High-Risk Observations</b>", table_hdr_style)
            ]]
            for u, cnt in sorted(unit_counts.items(), key=lambda x: x[1], reverse=True)[:8]:
                u_high = sum(1 for r in reports if r.refinery_unit == u and (r.risk_level or "").lower() == "high")
                unit_table_data.append([
                    Paragraph(u, table_cell_style),
                    Paragraph(str(cnt), table_cell_style),
                    Paragraph(str(u_high), table_cell_style)
                ])
            unit_table = Table(unit_table_data, colWidths=[240, 150, 150])
            unit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(unit_table)
            story.append(Spacer(1, 10))

        # --- SECTION 4: DEPARTMENT ANALYSIS ---
        dept_counts: Dict[str, int] = {}
        for r in reports:
            if r.department:
                dept_counts[r.department] = dept_counts.get(r.department, 0) + 1

        if dept_counts:
            story.append(Paragraph("4. Department Observation Telemetry", h2_style))
            dept_table_data = [[
                Paragraph("<b>Department</b>", table_hdr_style),
                Paragraph("<b>Observation Count</b>", table_hdr_style),
                Paragraph("<b>Share of Total</b>", table_hdr_style)
            ]]
            for d, cnt in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)[:6]:
                pct = (cnt / total_reports * 100) if total_reports > 0 else 0
                dept_table_data.append([
                    Paragraph(d, table_cell_style),
                    Paragraph(str(cnt), table_cell_style),
                    Paragraph(f"{pct:.1f}%", table_cell_style)
                ])
            dept_table = Table(dept_table_data, colWidths=[240, 150, 150])
            dept_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(dept_table)
            story.append(Spacer(1, 10))

        # --- SECTION 5: TOP IMMEDIATE CAUSES & POTENTIAL CONSEQUENCES ---
        cause_counts: Dict[str, int] = {}
        conseq_counts: Dict[str, int] = {}
        for r in reports:
            if r.immediate_cause:
                cause_counts[r.immediate_cause] = cause_counts.get(r.immediate_cause, 0) + 1
            if r.potential_consequence:
                conseq_counts[r.potential_consequence] = conseq_counts.get(r.potential_consequence, 0) + 1

        if cause_counts or conseq_counts:
            story.append(Paragraph("5. Primary Immediate Causes & Potential Consequences", h2_style))
            cause_table_data = [[
                Paragraph("<b>Top Immediate Causes</b>", table_hdr_style),
                Paragraph("<b>Top Potential Consequences</b>", table_hdr_style)
            ]]
            top_causes = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_conseqs = sorted(conseq_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            max_len = max(len(top_causes), len(top_conseqs), 1)

            for i in range(max_len):
                c_text = f"{top_causes[i][0]} ({top_causes[i][1]})" if i < len(top_causes) else "—"
                q_text = f"{top_conseqs[i][0]} ({top_conseqs[i][1]})" if i < len(top_conseqs) else "—"
                cause_table_data.append([
                    Paragraph(c_text, table_cell_style),
                    Paragraph(q_text, table_cell_style)
                ])

            cause_table = Table(cause_table_data, colWidths=[270, 270])
            cause_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(cause_table)
            story.append(Spacer(1, 10))

        # --- SECTION 6: HIGH-RISK SIF PRECURSOR INCIDENTS ---
        high_risk_reports = [r for r in reports if (r.risk_level or "").lower() == "high"]
        if high_risk_reports:
            story.append(Paragraph(f"6. High-Risk Safety Observations Log ({len(high_risk_reports)} Records)", h2_style))
            hr_table_data = [[
                Paragraph("<b>ID</b>", table_hdr_style),
                Paragraph("<b>Unit / Dept</b>", table_hdr_style),
                Paragraph("<b>Observed Problem</b>", table_hdr_style),
                Paragraph("<b>Potential Consequence</b>", table_hdr_style),
                Paragraph("<b>Status</b>", table_hdr_style)
            ]]
            for r in high_risk_reports[:8]:
                hr_table_data.append([
                    Paragraph(r.original_id or "—", table_cell_style),
                    Paragraph(f"{r.refinery_unit or '—'}<br/><font color='#64748B'>{r.department or '—'}</font>", table_cell_style),
                    Paragraph(r.description or "—", table_cell_style),
                    Paragraph(r.potential_consequence or "—", table_cell_style),
                    Paragraph(r.action_status or "Open", table_cell_style)
                ])
            hr_table = Table(hr_table_data, colWidths=[65, 95, 190, 130, 60])
            hr_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#991B1B')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(hr_table)
            story.append(Spacer(1, 10))

        # --- SECTION 7: AI PREVENTIVE INTELLIGENCE & RECOMMENDATIONS ---
        story.append(Paragraph("7. AI Preventive Intelligence & Strategic Recommendations", h2_style))
        recs_text = (
            "<b>1. Critical Barrier Integrity:</b> Mandate physical barrier verification for all operations in High-Risk process units.<br/>"
            "<b>2. Overdue Action Enforcement:</b> Immediately assign HSE focal points to close out overdue corrective actions.<br/>"
            "<b>3. Personal Protective Equipment:</b> Audit high-frequency failure points (Eye protection and Head protection) across Maintenance workshops.<br/>"
            "<b>4. Recurrence Elimination:</b> Conduct root cause analysis on units exhibiting recurring precursor patterns."
        )
        story.append(Paragraph(recs_text, body_style))

        # Build document
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # -------------------------------------------------------------
    # 2. EXCEL GENERATION (Pandas / Openpyxl Multi-Sheet)
    # -------------------------------------------------------------
    @staticmethod
    def generate_excel_report(
        db: Session,
        dataset_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        department: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        report_type: Optional[str] = None,
        action_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> bytes:
        q = ReportExportService._get_filtered_query(
            db, dataset_id, risk_level, department, refinery_unit, report_type, action_status, date_from, date_to
        )
        reports = list(db.scalars(q.order_by(SafetyReport.report_date.desc().nullslast())).all())
        sif_summary = SIFService.get_sif_summary(db, dataset_id)

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Calculate live BDI & SIF Density for Excel report
            from app.services.bdi_service import BDIService
            from app.services.sif_density_service import SIFDensityService
            bdi_summary = BDIService.get_bdi_summary(db)
            density_res = SIFDensityService.calculate_sif_density(db, dataset_id)

            # Sheet 1: Executive KPI Summary
            avg_bdi_val = getattr(bdi_summary, "average_bdi", 0.0) if bdi_summary else 0.0
            summary_data = {
                "Metric": [
                    "Total Safety Reports Ingested",
                    "High-Risk Observations",
                    "Medium-Risk Observations",
                    "Low-Risk Observations",
                    "SIF Precursors Detected",
                    "SIF Precursor Percentage Rate",
                    "SIF Precursor Density (%)",
                    "Barrier Degradation Index (BDI Average - Internal Prototype Analytical Index)",
                    "Overdue Actions",
                    "Open Actions",
                    "Closed Actions",
                    "Export Generation Timestamp"
                ],
                "Value": [
                    len(reports),
                    sum(1 for r in reports if (r.risk_level or "").lower() == "high"),
                    sum(1 for r in reports if (r.risk_level or "").lower() == "medium"),
                    sum(1 for r in reports if (r.risk_level or "").lower() == "low"),
                    sif_summary.get("sif_precursors_detected", 0),
                    f"{sif_summary.get('sif_precursor_rate_percentage', 0)}%",
                    f"{density_res.get('sif_precursor_density_percentage', 0.0)}%",
                    f"{avg_bdi_val:.1f} / 100",
                    sum(1 for r in reports if (r.action_status or "").lower() == "overdue"),
                    sum(1 for r in reports if (r.action_status or "").lower() == "open"),
                    sum(1 for r in reports if (r.action_status or "").lower() == "closed"),
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Executive_Summary", index=False)

            # Sheet 2: All Filtered Safety Reports
            reports_data = []
            for r in reports:
                reports_data.append({
                    "Report ID": r.original_id or r.id,
                    "Date": r.report_date.strftime("%Y-%m-%d") if r.report_date else "",
                    "Refinery Unit": r.refinery_unit or "",
                    "Department": r.department or "",
                    "Equipment ID": r.equipment or "",
                    "Work Type": r.work_type or "",
                    "Description": r.description or "",
                    "Risk Level": r.risk_level or "",
                    "Potential Consequence": r.potential_consequence or "",
                    "Immediate Cause": r.immediate_cause or "",
                    "PPE Flag": "YES" if r.ppe_issue else "NO",
                    "Recurring Issue": "YES" if r.repeated_issue or (r.previous_similar_reports or 0) > 0 else "NO",
                    "Prior Similar Reports": r.previous_similar_reports or 0,
                    "Corrective Action": r.corrective_action or "",
                    "Action Status": r.action_status or "Open",
                    "Assigned To": r.assigned_to or "",
                    "Assigned Department": r.assigned_department or "",
                    "Due Date": r.due_date.strftime("%Y-%m-%d") if r.due_date else "",
                    "Completion Date": r.completion_date.strftime("%Y-%m-%d") if r.completion_date else ""
                })
            pd.DataFrame(reports_data).to_excel(writer, sheet_name="Safety_Reports", index=False)

            # Sheet 3: High Risk & SIF Precursor Focus
            high_risk_data = [r for r in reports_data if r["Risk Level"].upper() == "HIGH"]
            pd.DataFrame(high_risk_data).to_excel(writer, sheet_name="High_Risk_SIF", index=False)

            # Sheet 4: Action Items Governance Tracker
            actions_data = [
                {
                    "Report ID": r["Report ID"],
                    "Refinery Unit": r["Refinery Unit"],
                    "Department": r["Department"],
                    "Risk Level": r["Risk Level"],
                    "Corrective Action": r["Corrective Action"],
                    "Action Status": r["Action Status"],
                    "Assigned To": r["Assigned To"],
                    "Due Date": r["Due Date"],
                    "Completion Date": r["Completion Date"]
                }
                for r in reports_data
            ]
            pd.DataFrame(actions_data).to_excel(writer, sheet_name="Action_Items_Tracker", index=False)

        excel_bytes = buffer.getvalue()
        buffer.close()
        return excel_bytes

    # -------------------------------------------------------------
    # 3. CSV GENERATION (RFC-4180 Compliant)
    # -------------------------------------------------------------
    @staticmethod
    def generate_csv_report(
        db: Session,
        dataset_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        department: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        report_type: Optional[str] = None,
        action_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> str:
        q = ReportExportService._get_filtered_query(
            db, dataset_id, risk_level, department, refinery_unit, report_type, action_status, date_from, date_to
        )
        reports = list(db.scalars(q.order_by(SafetyReport.report_date.desc().nullslast())).all())

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header
        writer.writerow([
            "report_id",
            "report_date",
            "refinery_unit",
            "department",
            "equipment",
            "work_type",
            "description",
            "risk_level",
            "potential_consequence",
            "immediate_cause",
            "ppe_issue",
            "previous_similar_reports",
            "repeated_issue",
            "corrective_action",
            "action_status",
            "assigned_to",
            "assigned_department",
            "due_date",
            "completion_date"
        ])

        for r in reports:
            writer.writerow([
                r.original_id or r.id,
                r.report_date.strftime("%Y-%m-%d") if r.report_date else "",
                r.refinery_unit or "",
                r.department or "",
                r.equipment or "",
                r.work_type or "",
                r.description or "",
                r.risk_level or "",
                r.potential_consequence or "",
                r.immediate_cause or "",
                "TRUE" if r.ppe_issue else "FALSE",
                r.previous_similar_reports or 0,
                "TRUE" if r.repeated_issue else "FALSE",
                r.corrective_action or "",
                r.action_status or "Open",
                r.assigned_to or "",
                r.assigned_department or "",
                r.due_date.strftime("%Y-%m-%d") if r.due_date else "",
                r.completion_date.strftime("%Y-%m-%d") if r.completion_date else ""
            ])

        csv_str = output.getvalue()
        output.close()
        return csv_str
