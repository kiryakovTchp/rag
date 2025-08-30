import io
import uuid

import camelot
import pandas as pd
import pdfplumber

from storage.r2 import ObjectStore


class TableParser:
    def __init__(self) -> None:
        self.storage = ObjectStore()

    def extract_tables(self, file_path: str, mime_type: str) -> list[dict]:
        """Extract tables from document."""
        tables = []

        try:
            if mime_type == "application/pdf":
                # Use pdfplumber and camelot for PDF tables
                tables.extend(self._extract_pdf_tables(file_path))
            elif mime_type in [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/csv",
            ]:
                # For Excel/CSV files, extract tables
                tables.extend(self._extract_office_tables(file_path, mime_type))

            return tables

        except Exception as e:
            print(f"Warning: Failed to extract tables: {e}")
            return []

    def _extract_pdf_tables(self, file_path: str) -> list[dict]:
        """Extract tables from PDF using pdfplumber and camelot."""
        tables = []

        # Try pdfplumber first
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    for table_num, table_data in enumerate(page_tables, 1):
                        if table_data and len(table_data) > 1:  # At least header + 1 row
                            table_id = f"pdfplumber_{page_num}_{table_num}"
                            table_text = self._format_table_as_markdown(table_data)

                            # Save table artifact to S3
                            artifact_key = f"artifacts/tables/{table_id}.md"
                            self._save_table_artifact(table_text, artifact_key)

                            tables.append(
                                {
                                    "type": "table",
                                    "text": table_text,
                                    "page": page_num,
                                    "bbox": None,
                                    "table_id": table_id,
                                }
                            )
        except Exception as e:
            print(f"pdfplumber failed: {e}")

        # Try camelot as backup
        try:
            camelot_tables = camelot.read_pdf(file_path, pages="all")
            for table_num, table in enumerate(camelot_tables, 1):
                if table.df.shape[0] > 1:  # At least header + 1 row
                    table_id = f"camelot_{table_num}"
                    table_text = self._dataframe_to_markdown(table.df)

                    # Save table artifact to S3
                    artifact_key = f"artifacts/tables/{table_id}.md"
                    self._save_table_artifact(table_text, artifact_key)

                    tables.append(
                        {
                            "type": "table",
                            "text": table_text,
                            "page": table.page,
                            "bbox": None,
                            "table_id": table_id,
                        }
                    )
        except Exception as e:
            print(f"camelot failed: {e}")

        return tables

    def _extract_office_tables(self, file_path: str, mime_type: str) -> list[dict]:
        """Extract tables from Office documents."""
        tables = []

        try:
            if mime_type == "text/csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            if not df.empty:
                table_id = str(uuid.uuid4())
                table_text = self._dataframe_to_markdown(df)

                # Save table artifact to S3
                artifact_key = f"artifacts/tables/{table_id}.md"
                self._save_table_artifact(table_text, artifact_key)

                tables.append(
                    {
                        "type": "table",
                        "text": table_text,
                        "page": 1,
                        "bbox": None,
                        "table_id": table_id,
                    }
                )

        except Exception as e:
            print(f"Failed to extract office table: {e}")

        return tables

    def _format_table_as_markdown(self, table_data: list) -> str:
        """Format table data as markdown table."""
        if not table_data or len(table_data) < 2:
            return ""

        # Header
        header = table_data[0]
        separator = "|" + "|".join(["---"] * len(header)) + "|"

        # Format as markdown
        markdown_lines = []
        markdown_lines.append("|" + "|".join(str(cell) for cell in header) + "|")
        markdown_lines.append(separator)

        # Data rows
        for row in table_data[1:]:
            markdown_lines.append("|" + "|".join(str(cell) for cell in row) + "|")

        return "\n".join(markdown_lines)

    def _dataframe_to_markdown(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to markdown table format."""
        # Convert to CSV string first
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_text = csv_buffer.getvalue()

        # Format as markdown table
        lines = csv_text.strip().split("\n")
        if len(lines) < 2:
            return csv_text

        # Header
        header = lines[0]
        separator = "|" + "|".join(["---"] * len(header.split(","))) + "|"

        # Format as markdown
        markdown_lines = []
        markdown_lines.append("|" + "|".join(header.split(",")) + "|")
        markdown_lines.append(separator)

        # Data rows
        for line in lines[1:]:
            markdown_lines.append("|" + "|".join(line.split(",")) + "|")

        return "\n".join(markdown_lines)

    def _save_table_artifact(self, table_text: str, artifact_key: str) -> None:
        """Save table artifact to S3."""
        try:
            data_stream = io.BytesIO(table_text.encode("utf-8"))
            self.storage.put_data(data_stream, artifact_key)
        except Exception as e:
            print(f"Failed to save table artifact: {e}")
