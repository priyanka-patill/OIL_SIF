import io
import json
import pandas as pd
from typing import Tuple, List, Dict, Any
from fastapi import HTTPException, status


class FileReader:
    """Reads uploaded files (Excel, CSV, JSON) into standardized pandas DataFrames."""

    @staticmethod
    def read_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        filename_lower = filename.lower()
        try:
            if filename_lower.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            elif filename_lower.endswith(".csv"):
                # Handle possible encodings
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
            elif filename_lower.endswith(".json"):
                data = json.loads(file_bytes.decode("utf-8"))
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict) and "records" in data:
                    df = pd.DataFrame(data["records"])
                elif isinstance(data, dict) and "data" in data:
                    df = pd.DataFrame(data["data"])
                else:
                    df = pd.DataFrame([data])
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type for {filename}"
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse file '{filename}': {str(e)}"
            )

        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset contains no data rows"
            )

        # Standardize column headers: remove leading/trailing whitespace
        df.columns = [str(col).strip() for col in df.columns]
        return df

    @staticmethod
    def read_workbook_sheets(file_bytes: bytes, filename: str) -> Dict[str, pd.DataFrame]:
        """Reads all sheets from an Excel workbook and returns a dictionary of sheet_name -> DataFrame."""
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
            sheets_dict = {}
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                df.columns = [str(col).strip() for col in df.columns]
                sheets_dict[sheet_name] = df
            return sheets_dict
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to read workbook sheets from '{filename}': {str(e)}"
            )

    @staticmethod
    def read_from_path(file_path: str) -> pd.DataFrame:
        with open(file_path, "rb") as f:
            content = f.read()
        return FileReader.read_file(content, file_path)

    @staticmethod
    def read_sheets_from_path(file_path: str) -> Dict[str, pd.DataFrame]:
        with open(file_path, "rb") as f:
            content = f.read()
        return FileReader.read_workbook_sheets(content, file_path)

