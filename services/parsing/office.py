import re

from unstructured.partition.auto import partition


class OfficeParser:
    def __init__(self) -> None:
        pass

    def parse_to_elements(self, file_path: str) -> list[dict]:
        """Parse office documents into elements."""
        try:
            # Check if it's a plain text file
            if file_path.endswith(".txt"):
                return self._parse_plain_text(file_path)

            # Use unstructured's auto partition for other file types
            try:
                elements_raw = partition(filename=file_path)
            except Exception:
                # If unstructured fails, try plain text parsing
                return self._parse_plain_text(file_path)

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

    def _parse_plain_text(self, file_path: str) -> list[dict]:
        """Parse plain text files into elements."""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Split by paragraphs (double newlines)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        elements = []
        for _i, paragraph in enumerate(paragraphs):
            element_type = self._determine_element_type(paragraph)
            text = self._normalize_text(paragraph)

            if text.strip():
                elements.append(
                    {
                        "type": element_type,
                        "text": text,
                        "page": 1,  # Plain text is single page
                        "bbox": None,
                    }
                )

        return elements

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
