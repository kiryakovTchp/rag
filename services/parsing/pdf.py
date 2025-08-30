import re

import pymupdf4llm


class PDFParser:
    def __init__(self) -> None:
        pass

    def parse_to_elements(self, file_path: str) -> list[dict]:
        """Parse PDF file into elements."""
        try:
            # Parse PDF to markdown
            markdown_content = pymupdf4llm.to_markdown(
                file_path, page_chunks=True, include_images=False
            )

            elements = []

            # Process each page
            for page_num, page_content in enumerate(markdown_content, 1):
                # Split content by headers and paragraphs
                lines = page_content.split("\n")
                current_text = ""
                current_type = "text"

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Check if it's a header
                    if line.startswith("#"):
                        # Save previous text if any
                        if current_text:
                            elements.append(
                                {
                                    "type": current_type,
                                    "text": self._normalize_text(current_text.strip()),
                                    "page": page_num,
                                    "bbox": None,
                                }
                            )

                        # Determine header level
                        header_level = len(line) - len(line.lstrip("#"))
                        current_type = f"h{min(header_level, 6)}"
                        current_text = line.lstrip("#").strip()
                    else:
                        # Regular text
                        if current_type.startswith("h"):
                            # Save header
                            if current_text:
                                elements.append(
                                    {
                                        "type": current_type,
                                        "text": self._normalize_text(current_text.strip()),
                                        "page": page_num,
                                        "bbox": None,
                                    }
                                )
                            current_type = "text"
                            current_text = line
                        else:
                            # Continue text
                            if current_text:
                                current_text += " " + line
                            else:
                                current_text = line

                # Save last element
                if current_text:
                    elements.append(
                        {
                            "type": current_type,
                            "text": self._normalize_text(current_text.strip()),
                            "page": page_num,
                            "bbox": None,
                        }
                    )

            return elements

        except Exception as e:
            raise Exception(f"Failed to parse PDF: {e}") from e

    def _normalize_text(self, text: str) -> str:
        """Normalize text: remove extra spaces, fix line breaks."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Fix line breaks
        text = text.replace("\n", " ").replace("\r", " ")
        # Remove hyphens at line breaks
        text = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)
        return text.strip()
