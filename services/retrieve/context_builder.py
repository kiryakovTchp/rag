"""Context builder for assembling relevant chunks."""

from typing import List

from services.chunking.token_splitter import TokenSplitter
from services.retrieve.types import ChunkWithScore


class ContextBuilder:
    """Builds compact context from retrieved chunks."""
    
    def __init__(self):
        """Initialize context builder."""
        self.token_splitter = TokenSplitter()
    
    def build(self, matches: List[ChunkWithScore], max_ctx_tokens: int) -> List[ChunkWithScore]:
        """Build compact context from matches.
        
        Args:
            matches: List of chunks with scores
            max_ctx_tokens: Maximum context tokens
            
        Returns:
            Filtered and merged chunks for context
        """
        if not matches:
            return []
        
        # Remove duplicates by element_id/table_id
        unique_matches = self._remove_duplicates(matches)
        
        # Merge neighboring chunks from same document/page
        merged_matches = self._merge_neighbors(unique_matches)
        
        # Filter by token limit
        filtered_matches = self._filter_by_tokens(merged_matches, max_ctx_tokens)
        
        return filtered_matches[:6]  # Max 6 chunks
    
    def _remove_duplicates(self, matches: List[ChunkWithScore]) -> List[ChunkWithScore]:
        """Remove duplicate chunks by element_id/table_id."""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Create unique key based on doc_id, page, and breadcrumbs
            key = (match["doc_id"], match["page"], tuple(match["breadcrumbs"]))
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    def _merge_neighbors(self, matches: List[ChunkWithScore]) -> List[ChunkWithScore]:
        """Merge neighboring chunks from same document/page."""
        if not matches:
            return matches
        
        merged = []
        current_group = [matches[0]]
        
        for match in matches[1:]:
            # Check if chunks are from same document and page
            if (match["doc_id"] == current_group[0]["doc_id"] and 
                match["page"] == current_group[0]["page"]):
                current_group.append(match)
            else:
                # Merge current group
                if current_group:
                    merged.append(self._merge_chunk_group(current_group))
                current_group = [match]
        
        # Merge last group
        if current_group:
            merged.append(self._merge_chunk_group(current_group))
        
        return merged
    
    def _merge_chunk_group(self, group: List[ChunkWithScore]) -> ChunkWithScore:
        """Merge a group of chunks into one."""
        if len(group) == 1:
            return group[0]
        
        # Use the highest scoring chunk as base
        base = max(group, key=lambda x: x["score"])
        
        # Combine snippets
        combined_snippet = " ".join(chunk["snippet"] for chunk in group)
        
        # Count tokens
        total_tokens = sum(self.token_splitter.count_tokens(chunk["snippet"]) for chunk in group)
        
        # Truncate if too long
        if total_tokens > 400:  # Reasonable limit for merged chunks
            combined_snippet = self._truncate_snippet(combined_snippet, 400)
        
        return ChunkWithScore(
            chunk_id=base["chunk_id"],
            doc_id=base["doc_id"],
            page=base["page"],
            score=base["score"],
            snippet=combined_snippet,
            breadcrumbs=base["breadcrumbs"]
        )
    
    def _filter_by_tokens(self, matches: List[ChunkWithScore], max_tokens: int) -> List[ChunkWithScore]:
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
    
    def _truncate_snippet(self, snippet: str, max_tokens: int) -> str:
        """Truncate snippet to token limit."""
        tokens = self.token_splitter.split_text(snippet)
        if len(tokens) <= max_tokens:
            return snippet
        
        # Truncate and try to end at sentence boundary
        truncated_tokens = tokens[:max_tokens]
        truncated_text = " ".join(truncated_tokens)
        
        # Find last sentence boundary
        for i in range(len(truncated_text) - 1, 0, -1):
            if truncated_text[i] in '.!?':
                return truncated_text[:i + 1].strip()
        
        return truncated_text.strip()
