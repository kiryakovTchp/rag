"""Context builder for assembling relevant chunks."""

from services.chunking.token import TokenTextSplitter
from services.retrieve.types import ChunkWithScore


class ContextBuilder:
    """Build compact context from retrieved chunks."""

    def __init__(self):
        self.token_splitter = TokenTextSplitter()

    def build(
        self, matches: list[ChunkWithScore], max_ctx_tokens: int
    ) -> list[ChunkWithScore]:
        """Build compact context from matches.

        Args:
            matches: List of chunk matches with scores
            max_ctx_tokens: Maximum tokens allowed

        Returns:
            Filtered and optimized chunk list
        """
        if not matches:
            return []

        # Remove duplicates and merge neighbors
        unique_matches = self._remove_duplicates(matches)
        merged_matches = self._merge_neighbors(unique_matches)

        # Filter by token limit
        filtered_matches = self._filter_by_tokens(merged_matches, max_ctx_tokens)

        # Ensure we don't exceed reasonable chunk count
        if len(filtered_matches) > 6:
            filtered_matches = filtered_matches[:6]  # Max 6 chunks

        return filtered_matches

    def _remove_duplicates(self, matches: list[ChunkWithScore]) -> list[ChunkWithScore]:
        """Remove duplicate chunks by chunk_id."""
        seen = set()
        unique_matches = []

        for match in matches:
            if match["chunk_id"] not in seen:
                seen.add(match["chunk_id"])
                unique_matches.append(match)

        return unique_matches

    def _merge_neighbors(self, matches: list[ChunkWithScore]) -> list[ChunkWithScore]:
        """Merge neighboring chunks from same document/page."""
        if not matches:
            return []

        # Group by document and page
        groups = {}
        for match in matches:
            key = (match["doc_id"], match["page"])
            if key not in groups:
                groups[key] = []
            groups[key].append(match)

        # Merge each group
        merged = []
        for group in groups.values():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Sort by chunk_id to maintain order
                group.sort(key=lambda x: x["chunk_id"])
                merged_chunk = self._merge_chunk_group(group)
                merged.append(merged_chunk)

        return merged

    def _merge_chunk_group(self, group: list[ChunkWithScore]) -> ChunkWithScore:
        """Merge a group of chunks into one."""
        if len(group) == 1:
            return group[0]

        # Combine text and breadcrumbs
        combined_text = " ".join(chunk["snippet"] for chunk in group)
        combined_breadcrumbs = []
        for chunk in group:
            combined_breadcrumbs.extend(chunk["breadcrumbs"])

        # Use highest score
        best_score = max(chunk["score"] for chunk in group)

        # Use first chunk as base
        base_chunk = group[0]
        return ChunkWithScore(
            chunk_id=base_chunk["chunk_id"],
            doc_id=base_chunk["doc_id"],
            page=base_chunk["page"],
            score=best_score,
            snippet=combined_text,
            breadcrumbs=combined_breadcrumbs,
        )

    def _filter_by_tokens(
        self, matches: list[ChunkWithScore], max_tokens: int
    ) -> list[ChunkWithScore]:
        """Filter matches by token limit."""
        filtered = []
        current_tokens = 0

        for match in matches:
            chunk_tokens = self.token_splitter.count_tokens(match["snippet"])
            if current_tokens + chunk_tokens <= max_tokens:
                filtered.append(match)
                current_tokens += chunk_tokens
            else:
                break

        return filtered
