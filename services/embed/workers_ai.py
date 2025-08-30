"""Workers AI embedder service."""

import os
import time
from typing import List

import numpy as np
import requests


class WorkersAIEmbedder:
    """Workers AI embedder using Cloudflare Workers AI."""
    
    def __init__(self, api_token: str = None, batch_size: int = 64):
        """Initialize Workers AI embedder.
        
        Args:
            api_token: Cloudflare Workers AI API token
            batch_size: Batch size for embedding generation
        """
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN")
        self.batch_size = batch_size
        self.dimension = 1024
        self.base_url = "https://api.cloudflare.com/client/v4/ai/run/@cf/baai/bge-m3"
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts using Workers AI.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Numpy array of embeddings (n_texts, 1024)
        """
        if not self.api_token:
            raise ValueError("Cloudflare API token not provided")
        
        if not texts:
            return np.array([])
        
        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.append(batch_embeddings)
        
        # Concatenate all batches
        if all_embeddings:
            return np.vstack(all_embeddings)
        else:
            return np.array([])
    
    def _embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Numpy array of embeddings (n_texts, 1024)
        """
        payload = {
            "texts": texts
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
                        # Extract embeddings from response
                        embeddings = result.get("result", {}).get("embeddings", [])
                        if embeddings:
                            # Convert to numpy array and normalize
                            embeddings_array = np.array(embeddings, dtype=np.float32)
                            # L2 normalize
                            norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
                            embeddings_array = embeddings_array / (norms + 1e-8)
                            return embeddings_array
                        else:
                            raise ValueError("No embeddings in response")
                    else:
                        raise ValueError(f"API error: {result.get('errors', [])}")
                elif response.status_code == 429:
                    # Rate limit, wait and retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                else:
                    raise ValueError(f"HTTP error: {response.status_code}")
                    
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise
        
        raise RuntimeError("Failed to embed texts after all retries")
    
    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector (1024,)
        """
        return self.embed_texts([text])[0]
    
    def get_dimension(self) -> int:
        """Get embedding dimension.
        
        Returns:
            Embedding dimension (1024)
        """
        return self.dimension
