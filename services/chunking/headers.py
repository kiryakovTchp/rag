class MarkdownHeaderSplitter:
    def __init__(self) -> None:
        pass

    def split_by_headers(self, elements: list[dict]) -> list[dict]:
        """Split elements by headers and build header paths."""
        sections: list[dict] = []
        current_section: list[dict] = []
        current_header_path: list[str] = []

        for element in elements:
            if element["type"].startswith("h"):
                # Save current section if not empty
                if current_section:
                    sections.append(
                        {"elements": current_section, "header_path": current_header_path.copy()}
                    )

                # Start new section
                header_level = int(element["type"][1])
                header_text = element["text"]

                # Update header path
                while len(current_header_path) >= header_level:
                    current_header_path.pop()
                current_header_path.append(header_text)

                current_section = [element]
            else:
                # Add to current section
                current_section.append(element)

        # Add last section
        if current_section:
            sections.append(
                {"elements": current_section, "header_path": current_header_path.copy()}
            )

        return sections
