"""Reranking service using Workers AI."""

import logging
import os
import time

import requests

from api.config import get_settings

logger = logging.getLogger(__name__)


class WorkersAIReranker:
    """Reranker using Workers AI API."""

    def __init__(self):
        """Initialize reranker."""
        try:
            settings = get_settings()
            self.api_url = settings.workers_ai_rerank_url or os.getenv(
                "WORKERS_AI_RERANK_URL"
            )
            self.api_key = settings.workers_ai_api_key or os.getenv(
                "WORKERS_AI_API_KEY"
            )
        except Exception:
            self.api_url = os.getenv("WORKERS_AI_RERANK_URL")
            self.api_key = os.getenv("WORKERS_AI_API_KEY")
        self.max_retries = 3
        self.retry_delay = 1

    def rerank(self, pairs: list[tuple[str, str]], top_k: int) -> list[int]:
        """Rerank query-document pairs.

        Args:
            pairs: List of (query, document) pairs
            top_k: Number of top results to return

        Returns:
            List of indices in reranked order
        """
        if not pairs or not self.api_url or not self.api_key:
            # Fallback to original order
            logger.warning(
                "WARNING: Reranking failed, falling back to original order - no reranking applied"
            )
            return list(range(min(top_k, len(pairs))))

        try:
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "query": pairs[0][0],  # Use first query
                "documents": [pair[1] for pair in pairs],
                "top_k": top_k,
            }

            # Make request with retries
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        self.api_url, headers=headers, json=data, timeout=30
                    )
                    response.raise_for_status()

                    result = response.json()
                    if "results" in result:
                        # Extract indices from results
                        indices = []
                        for item in result["results"]:
                            if "index" in item:
                                indices.append(item["index"])

                        # Ensure we have enough results
                        while len(indices) < min(top_k, len(pairs)):
                            # Add remaining indices in order
                            for i in range(len(pairs)):
                                if i not in indices:
                                    indices.append(i)
                                    break

                        return indices[:top_k]

                    break

                except requests.RequestException as e:
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"Reranking request failed after {self.max_retries} attempts: {e}"
                        )
                        break

                    logger.warning(f"Reranking attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff

        except Exception as e:
            logger.error(f"Reranking failed: {e}")

        # Fallback to original order
        logger.warning(
            "WARNING: Reranking failed, falling back to original order - no reranking applied"
        )
        return list(range(min(top_k, len(pairs))))
