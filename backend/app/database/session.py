from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
from app.database.base import Base

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables and run lightweight migrations for new columns."""
    # Ensure all models are imported before creating tables
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    # Run lightweight column migration for existing SQLite databases
    from sqlalchemy import inspect, text
    with engine.connect() as conn:
        inspector = inspect(conn)
        
        # 1. safety_reports migration
        if "safety_reports" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("safety_reports")}
            new_report_columns = [
                ("action_status", "VARCHAR(100) DEFAULT 'Open'"),
                ("assigned_to", "VARCHAR(255)"),
                ("assigned_department", "VARCHAR(255)"),
                ("due_date", "DATETIME"),
                ("completion_date", "DATETIME"),
                ("closure_verified_by", "VARCHAR(255)"),
                ("closure_verified_at", "DATETIME"),
                ("action_comments", "TEXT"),
                ("source_dataset", "VARCHAR(255)"),
                ("analysis_status", "VARCHAR(50) DEFAULT 'COMPLETED'"),
                ("submitting_user", "VARCHAR(255)"),
                ("submitting_role", "VARCHAR(100)"),
                ("detected_factors", "TEXT DEFAULT '[]'"),
                ("factor_count", "INTEGER DEFAULT 0"),
                ("relationship_type", "VARCHAR(50) DEFAULT 'independent_observation'"),
                ("related_report_ids", "TEXT DEFAULT '[]'"),
                ("created_at", "DATETIME"),
                ("updated_at", "DATETIME"),
            ]
            for col_name, col_type in new_report_columns:
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE safety_reports ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass

        # 2. datasets migration
        if "datasets" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("datasets")}
            new_dataset_columns = [
                ("sheet_name", "VARCHAR(255)"),
                ("dataset_type", "VARCHAR(50) DEFAULT 'single_factor'"),
                ("factor_count", "INTEGER DEFAULT 0"),
                ("factor_names", "TEXT DEFAULT '[]'"),
                ("data_quality_status", "VARCHAR(50) DEFAULT 'PASSED'"),
                ("duplicate_count", "INTEGER DEFAULT 0"),
                ("is_derived_dataset", "BOOLEAN DEFAULT 0"),
                ("parent_dataset", "VARCHAR(255)"),
            ]
            for col_name, col_type in new_dataset_columns:
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE datasets ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass

        # 3. safety_actions migration
        if "safety_actions" in inspector.get_table_names():
            existing_act_cols = {col["name"] for col in inspector.get_columns("safety_actions")}
            new_action_columns = [
                ("sla_minutes", "INTEGER DEFAULT 1440"),
                ("sla_deadline", "DATETIME"),
                ("sla_state", "VARCHAR(50) DEFAULT 'NORMAL'"),
                ("escalation_level", "INTEGER DEFAULT 0"),
                ("approval_status", "VARCHAR(50) DEFAULT 'PENDING'"),
                ("approved_by", "VARCHAR(100)"),
                ("approved_at", "DATETIME"),
                ("rejection_reason", "TEXT"),
                ("acknowledged_at", "DATETIME"),
                ("containment_started_at", "DATETIME"),
                ("remediation_completed_at", "DATETIME"),
                ("completed_at", "DATETIME"),
                ("verified_at", "DATETIME"),
                ("verified_by", "VARCHAR(100)"),
                ("closed_at", "DATETIME"),
            ]
            for col_name, col_type in new_action_columns:
                if col_name not in existing_act_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE safety_actions ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass

        # 4. report_analyses migration
        if "report_analyses" in inspector.get_table_names():
            existing_ana_cols = {col["name"] for col in inspector.get_columns("report_analyses")}
            new_ana_columns = [
                ("iogp_rule", "VARCHAR(100) DEFAULT 'No clear Life-Saving Rule match'"),
                ("secondary_iogp_rules", "TEXT DEFAULT '[]'"),
                ("iogp_confidence", "FLOAT DEFAULT 0.0"),
                ("iogp_reasoning", "TEXT"),
                ("barrier_failure", "TEXT"),
                ("missing_control", "TEXT"),
                ("existing_barrier", "TEXT"),
                ("human_overridden", "BOOLEAN DEFAULT 0"),
                ("human_risk_level", "VARCHAR(50)"),
                ("human_sif_precursor", "VARCHAR(50)"),
                ("human_feedback_reason", "TEXT"),
            ]
            for col_name, col_type in new_ana_columns:
                if col_name not in existing_ana_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE report_analyses ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass

    # 5. Backfill missing risk_level on existing SafetyReport records
    try:
        from sqlalchemy import select, or_
        from app.models.safety_report import SafetyReport
        from app.utils.risk_classifier import normalize_risk_level
        with SessionLocal() as db_session:
            unclassified = db_session.scalars(
                select(SafetyReport).where(or_(SafetyReport.risk_level == None, SafetyReport.risk_level == ""))
            ).all()
            if unclassified:
                for rep in unclassified:
                    rep.risk_level = normalize_risk_level(rep.risk_level, fallback_item=rep.raw_data)
                db_session.commit()
    except Exception as ex:
        print(f"Risk level backfill notice: {ex}")



