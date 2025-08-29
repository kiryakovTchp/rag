from services.chunking.headers import MarkdownHeaderSplitter
from services.chunking.semantic import SemanticSplitter
from services.chunking.token import TokenTextSplitter


class ChunkingPipeline:
    def __init__(self) -> None:
        self.header_splitter = MarkdownHeaderSplitter()
        self.token_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=75)
        self.semantic_splitter = SemanticSplitter()

    def build_chunks(self, elements: list[dict]) -> list[dict]:
        """Build chunks from elements using the full pipeline."""
        chunks: list[dict] = []

        # Separate tables from other elements
        tables = [e for e in elements if e["type"] == "table"]
        other_elements = [e for e in elements if e["type"] != "table"]

        # Process non-table elements
        if other_elements:
            # Split by headers
            sections = self.header_splitter.split_by_headers(other_elements)

            for section in sections:
                # Combine all text in section
                section_text = " ".join([e["text"] for e in section["elements"]])

                # Split by tokens
                text_chunks = self.token_splitter.split_text(section_text)

                # Create chunks
                for _i, chunk_text in enumerate(text_chunks):
                    chunk = {
                        "level": "section",
                        "header_path": section["header_path"],
                        "text": chunk_text,
                        "token_count": self.token_splitter.count_tokens(chunk_text),
                        "page": section["elements"][0].get("page") if section["elements"] else None,
                        "element_id": (
                            section["elements"][0].get("id") if section["elements"] else None
                        ),
                    }
                    chunks.append(chunk)

        # Process tables
        for table in tables:
            table_chunks = self._process_table(table)
            chunks.extend(table_chunks)

        return chunks

    def _process_table(self, table: dict) -> list[dict]:
        """Process table into chunks."""
        table_text = table["text"]
        lines = table_text.split("\n")

        if len(lines) <= 3:  # Small table, keep as one chunk
            return [
                {
                    "level": "table",
                    "header_path": [],
                    "text": table_text,
                    "token_count": self.token_splitter.count_tokens(table_text),
                    "page": table.get("page"),
                    "element_id": table.get("id"),
                    "table_meta": {
                        "table_id": table.get("table_id"),
                        "rows": len(lines) - 2,  # Exclude header and separator
                    },
                }
            ]

        # Large table, split into groups of 20-60 rows
        chunks: list[dict] = []
        header = lines[0]
        separator = lines[1]
        data_lines = lines[2:]

        chunk_size = 40  # Target chunk size
        for i in range(0, len(data_lines), chunk_size):
            chunk_lines = data_lines[i : i + chunk_size]
            chunk_text = "\n".join([header, separator] + chunk_lines)

            chunks.append(
                {
                    "level": "table",
                    "header_path": [],
                    "text": chunk_text,
                    "token_count": self.token_splitter.count_tokens(chunk_text),
                    "page": table.get("page"),
                    "element_id": table.get("id"),
                    "table_meta": {
                        "table_id": table.get("table_id"),
                        "rows": len(chunk_lines),
                        "start_row": i + 1,
                        "end_row": i + len(chunk_lines),
                    },
                }
            )

        return chunks
