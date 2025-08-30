"""Workers AI reranker service."""

import os
import time
from typing import List, Tuple

import requests


class WorkersAIReranker:
    """Workers AI reranker using bge-reranker-v2-m3."""
    
    def __init__(self):
        """Initialize Workers AI reranker."""
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.base_url = "https://api.cloudflare.com/client/v4/ai/run/@cf/baai/bge-reranker-v2-m3"
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    def rerank(self, pairs: List[Tuple[str, str]], top_k: int) -> List[int]:
        """Rerank query-document pairs.
        
        Args:
            pairs: List of (query, document) pairs
            top_k: Number of top results to return
            
        Returns:
            List of indices in order of relevance
        """
        if not self.api_token:
            print("⚠️ Workers AI reranker not available: no API token")
            return list(range(min(top_k, len(pairs))))
        
        if not pairs:
            return []
        
        # Prepare request
        documents = [doc for _, doc in pairs]
        
        payload = {
            "texts": documents,
            "query": pairs[0][0],  # Use first query
            "top_k": top_k
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        # Extract indices from response
                        indices = result.get("result", {}).get("indices", [])
                        return indices[:top_k]
                    else:
                        print(f"⚠️ Workers AI reranker failed: {result.get('errors', [])}")
                        break
                elif response.status_code == 429:
                    # Rate limit, wait and retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                else:
                    print(f"⚠️ Workers AI reranker error: {response.status_code}")
                    break
                    
            except requests.RequestException as e:
                print(f"⚠️ Workers AI reranker request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                break
        
        # Fallback to original order
        return list(range(min(top_k, len(pairs))))
