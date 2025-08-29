import io
import uuid

import pandas as pd


class TableParser:
    def __init__(self) -> None:
        pass

    def extract_tables(self, file_path: str, mime_type: str) -> list[dict]:
        """Extract tables from document."""
        tables = []

        try:
            if mime_type == "application/pdf":
                # For PDFs, we'll use a simple approach for now
                # In production, you'd use pdfplumber or camelot
                pass
            elif mime_type in [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/csv",
            ]:
                # For Excel/CSV files, extract tables
                if mime_type == "text/csv":
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                if not df.empty:
                    table_id = str(uuid.uuid4())
                    table_text = self._dataframe_to_text(df)

                    tables.append(
                        {
                            "type": "table",
                            "text": table_text,
                            "page": 1,
                            "bbox": None,
                            "table_id": table_id,
                        }
                    )

            return tables

        except Exception as e:
            print(f"Warning: Failed to extract tables: {e}")
            return []

    def _dataframe_to_text(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to readable text format."""
        # Convert to CSV string
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
