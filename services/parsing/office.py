import re

from unstructured.partition.auto import partition


class OfficeParser:
    def __init__(self) -> None:
        pass

    def parse_to_elements(self, file_path: str) -> list[dict]:
        """Parse office documents into elements."""
        try:
            # Use unstructured's auto partition
            elements_raw = partition(filename=file_path)

            elements = []
            for element in elements_raw:
                element_type = self._determine_element_type(element)
                text = self._normalize_text(str(element))

                if text.strip():
                    elements.append(
                        {
                            "type": element_type,
                            "text": text,
                            "page": getattr(element, "metadata", {}).get("page_number"),
                            "bbox": None,
                        }
                    )

            return elements

        except Exception as e:
            raise Exception(f"Failed to parse office document: {e}") from e

    def _determine_element_type(self, element) -> str:
        """Determine element type based on unstructured element."""
        element_str = str(element)

        # Check for headers (lines starting with # or all caps)
        if element_str.startswith("#") or (
            element_str.isupper() and len(element_str.split()) <= 10
        ):
            return "title"

        # Check for lists
        if element_str.startswith(("-", "*", "•", "1.", "2.", "3.")):
            return "list"

        # Check for code blocks
        if "```" in element_str or element_str.count("{") > 2:
            return "code"

        # Default to text
        return "text"

    def _normalize_text(self, text: str) -> str:
        """Normalize text: remove extra spaces, fix line breaks."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Fix line breaks
        text = text.replace("\n", " ").replace("\r", " ")
        # Remove hyphens at line breaks
        text = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)
        return text.strip()
