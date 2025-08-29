import tiktoken


class TokenTextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 75) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks based on token count."""
        tokens = self.encoding.encode(text)

        if len(tokens) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(tokens):
                break

        return chunks

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
