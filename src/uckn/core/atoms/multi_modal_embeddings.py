"""
UCKN Multi-Modal Embeddings Atom

Provides unified embedding generation for code, text, configuration files, and error messages.
Handles model loading, caching, batch processing, and multi-modal search combination.
"""

from typing import List, Dict, Optional, Any, Union
import logging
import hashlib
import threading
import numpy as np
import os

# Defensive import logic for torch and sentence-transformers
SENTENCE_TRANSFORMERS_AVAILABLE = False
TRANSFORMERS_AVAILABLE = False
SentenceTransformer = None
AutoTokenizer = None
AutoModel = None
torch = None

_DISABLE_TORCH = os.environ.get("UCKN_DISABLE_TORCH", "0") == "1"

if not _DISABLE_TORCH:
    # Try importing torch and transformers defensively
    try:
        try:
            import torch
        except Exception as torch_exc:
            torch = None
            # Log or print for debugging, but do not raise
        else:
            try:
                from transformers import AutoTokenizer, AutoModel
                TRANSFORMERS_AVAILABLE = True
            except Exception as tf_exc:
                AutoTokenizer = None
                AutoModel = None
                TRANSFORMERS_AVAILABLE = False
    except Exception:
        torch = None
        AutoTokenizer = None
        AutoModel = None
        TRANSFORMERS_AVAILABLE = False

    # Try importing sentence-transformers defensively
    try:
        from sentence_transformers import SentenceTransformer
        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except Exception as st_exc:
        SentenceTransformer = None
        SENTENCE_TRANSFORMERS_AVAILABLE = False
else:
    # Torch is disabled by environment variable
    torch = None
    AutoTokenizer = None
    AutoModel = None
    SentenceTransformer = None
    TRANSFORMERS_AVAILABLE = False
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class MultiModalEmbeddings:
    """
    Multi-modal embedding system for code, text, config files, and error messages.
    - Code: Uses code-specific models (CodeBERT or fallback)
    - Text: Uses sentence-transformers
    - Config: Specialized tokenization + general embedding
    - Error: Preprocessing + text embedding
    - Caching and batch processing for performance
    """

    _CODE_MODEL_NAME = "microsoft/codebert-base"
    _TEXT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    _CACHE_SIZE = 256

    def __init__(self, device: Optional[str] = None):
        self._logger = logging.getLogger(__name__)
        # Defensive: If torch is unavailable, always use cpu
        if torch is not None and hasattr(torch, "cuda") and callable(getattr(torch.cuda, "is_available", None)):
            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = "cpu"
        self._lock = threading.Lock()

        # Model loading
        self.code_tokenizer = None
        self.code_model = None
        self.text_model = None

        # Only initialize models if not disabled
        if not _DISABLE_TORCH:
            self._init_code_model()
            self._init_text_model()
        else:
            self._logger.warning("Torch and transformers are disabled by environment variable.")

        # In-memory cache for embeddings
        self._embedding_cache = {}

    def _init_code_model(self):
        if not TRANSFORMERS_AVAILABLE or AutoTokenizer is None or AutoModel is None or torch is None:
            self._logger.warning("Transformers not available. Code embedding will fallback to text model.")
            return
        try:
            self.code_tokenizer = AutoTokenizer.from_pretrained(self._CODE_MODEL_NAME)
            self.code_model = AutoModel.from_pretrained(self._CODE_MODEL_NAME).to(self.device)
            self._logger.info(f"Loaded code model: {self._CODE_MODEL_NAME}")
        except Exception as e:
            self._logger.warning(f"Failed to load code model '{self._CODE_MODEL_NAME}': {e}. Falling back to text model.")
            self.code_tokenizer = None
            self.code_model = None

    def _init_text_model(self):
        if not SENTENCE_TRANSFORMERS_AVAILABLE or SentenceTransformer is None:
            self._logger.warning("SentenceTransformers not available. Text embedding will be disabled.")
            return
        try:
            self.text_model = SentenceTransformer(self._TEXT_MODEL_NAME, device=self.device)
            self._logger.info(f"Loaded text model: {self._TEXT_MODEL_NAME}")
        except Exception as e:
            self._logger.error(f"Failed to load text model '{self._TEXT_MODEL_NAME}': {e}")
            self.text_model = None

    def _hash_input(self, data: Any) -> str:
        """Hash input for caching."""
        return hashlib.sha256(str(data).encode("utf-8")).hexdigest()

    def _get_cached_embedding(self, key: str) -> Optional[List[float]]:
        return self._embedding_cache.get(key)

    def _set_cached_embedding(self, key: str, embedding: List[float]):
        if len(self._embedding_cache) >= self._CACHE_SIZE:
            # Remove oldest item (FIFO)
            self._embedding_cache.pop(next(iter(self._embedding_cache)))
        self._embedding_cache[key] = embedding

    def _embed_code(self, code: str) -> Optional[List[float]]:
        key = f"code:{self._hash_input(code)}"
        cached = self._get_cached_embedding(key)
        if cached:
            return cached
        if self.code_model and self.code_tokenizer and torch is not None:
            try:
                inputs = self.code_tokenizer(code, return_tensors="pt", truncation=True, max_length=256)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = self.code_model(**inputs)
                    # Use [CLS] token representation
                    embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
                    embedding = embedding / np.linalg.norm(embedding)
                    embedding = embedding.tolist()
                self._set_cached_embedding(key, embedding)
                return embedding
            except Exception as e:
                self._logger.error(f"Code embedding failed: {e}")
        # Fallback to text embedding
        return self._embed_text(code)

    def _embed_text(self, text: str) -> Optional[List[float]]:
        key = f"text:{self._hash_input(text)}"
        cached = self._get_cached_embedding(key)
        if cached:
            return cached
        if self.text_model:
            try:
                embedding = self.text_model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                embedding = embedding.tolist()
                self._set_cached_embedding(key, embedding)
                return embedding
            except Exception as e:
                self._logger.error(f"Text embedding failed: {e}")
        return None

    def _embed_config(self, config: str) -> Optional[List[float]]:
        # Simple tokenization: split on newlines, colons, equals, etc.
        tokens = []
        for line in config.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens.extend(line.replace("=", " = ").replace(":", " : ").split())
        token_str = " ".join(tokens)
        return self._embed_text(token_str)

    def _embed_error(self, error_msg: str) -> Optional[List[float]]:
        # Preprocess: remove file paths, line numbers, stack traces, etc.
        import re
        cleaned = re.sub(r'File ".*?", line \d+, in .*\n', '', error_msg)
        cleaned = re.sub(r'\s+at\s+.*\n', '', cleaned)
        cleaned = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*\n', '', cleaned)
        cleaned = cleaned.strip()
        return self._embed_text(cleaned)

    def embed(
        self,
        data: Union[str, Dict[str, Any]],
        data_type: str = "auto"
    ) -> Optional[List[float]]:
        """
        Generate embedding for a single data item.
        data_type: 'code', 'text', 'config', 'error', or 'auto'
        """
        if isinstance(data, dict) and "type" in data and "content" in data:
            data_type = data["type"]
            data = data["content"]

        if data_type == "auto":
            # Heuristic: detect type
            if isinstance(data, str):
                if data.strip().startswith("def ") or data.strip().startswith("class "):
                    data_type = "code"
                elif "=" in data and "\n" in data:
                    data_type = "config"
                elif "Traceback" in data or "Exception" in data:
                    data_type = "error"
                else:
                    data_type = "text"
            else:
                data_type = "text"

        if data_type == "code":
            return self._embed_code(data)
        elif data_type == "text":
            return self._embed_text(data)
        elif data_type == "config":
            return self._embed_config(data)
        elif data_type == "error":
            return self._embed_error(data)
        else:
            self._logger.warning(f"Unknown data_type '{data_type}', defaulting to text embedding.")
            return self._embed_text(str(data))

    def embed_batch(
        self,
        items: List[Union[str, Dict[str, Any]]],
        data_type: str = "auto"
    ) -> List[Optional[List[float]]]:
        """
        Batch embedding for a list of items.
        Returns list of embeddings (None if failed).
        """
        embeddings = []
        for item in items:
            embeddings.append(self.embed(item, data_type=data_type))
        return embeddings

    def combine_embeddings(
        self,
        embeddings: List[List[float]],
        method: str = "mean"
    ) -> Optional[List[float]]:
        """
        Combine multiple embeddings into a single vector.
        method: 'mean' (default), 'concat'
        """
        if not embeddings:
            return None
        arrs = [np.array(e) for e in embeddings if e is not None]
        if not arrs:
            return None
            
        # Ensure all embeddings have the same dimension for mean
        if method == "mean":
            # Check if all arrays have the same shape
            shapes = [arr.shape for arr in arrs]
            if len(set(shapes)) > 1:
                # Pad to maximum dimension
                max_dim = max(shape[0] for shape in shapes)
                padded_arrs = []
                for arr in arrs:
                    if arr.shape[0] < max_dim:
                        padded = np.zeros(max_dim)
                        padded[:arr.shape[0]] = arr
                        padded_arrs.append(padded)
                    else:
                        padded_arrs.append(arr)
                arrs = padded_arrs
            combined = np.mean(arrs, axis=0)
        elif method == "concat":
            combined = np.concatenate(arrs)
        else:
            self._logger.warning(f"Unknown combine method '{method}', using mean.")
            # Same padding logic for fallback
            shapes = [arr.shape for arr in arrs]
            if len(set(shapes)) > 1:
                max_dim = max(shape[0] for shape in shapes)
                padded_arrs = []
                for arr in arrs:
                    if arr.shape[0] < max_dim:
                        padded = np.zeros(max_dim)
                        padded[:arr.shape[0]] = arr
                        padded_arrs.append(padded)
                    else:
                        padded_arrs.append(arr)
                arrs = padded_arrs
            combined = np.mean(arrs, axis=0)
        combined = combined / np.linalg.norm(combined)
        return combined.tolist()

    def multi_modal_embed(
        self,
        code: Optional[str] = None,
        text: Optional[str] = None,
        config: Optional[str] = None,
        error: Optional[str] = None,
        combine_method: str = "mean"
    ) -> Optional[List[float]]:
        """
        Generate a multi-modal embedding from any combination of code, text, config, and error.
        """
        embeddings = []
        if code:
            e = self._embed_code(code)
            if e is not None:
                embeddings.append(e)
        if text:
            e = self._embed_text(text)
            if e is not None:
                embeddings.append(e)
        if config:
            e = self._embed_config(config)
            if e is not None:
                embeddings.append(e)
        if error:
            e = self._embed_error(error)
            if e is not None:
                embeddings.append(e)
        return self.combine_embeddings(embeddings, method=combine_method)

    def search(
        self,
        query: Dict[str, Optional[str]],
        collection_name: str,
        chroma_connector: Any,
        limit: int = 10,
        min_similarity: float = 0.7,
        combine_method: str = "mean",
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Multi-modal search: embed query, search ChromaDB, return results.
        query: dict with any of 'code', 'text', 'config', 'error'
        """
        query_embedding = self.multi_modal_embed(
            code=query.get("code"),
            text=query.get("text"),
            config=query.get("config"),
            error=query.get("error"),
            combine_method=combine_method
        )
        if query_embedding is None:
            self._logger.warning("Failed to generate query embedding for multi-modal search.")
            return []
        # Defensive: If chroma_connector is None, return empty
        if chroma_connector is None:
            self._logger.warning("No chroma_connector provided for search.")
            return []
        return chroma_connector.search_documents(
            collection_name=collection_name,
            query_embedding=query_embedding,
            n_results=limit,
            min_similarity=min_similarity,
            where_clause=metadata_filter
        )
