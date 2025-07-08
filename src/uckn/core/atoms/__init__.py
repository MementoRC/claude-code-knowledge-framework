from .pattern_extractor import PatternExtractor
from .project_dna_fingerprinter import ProjectDNAFingerprinter
from .semantic_search_engine import SemanticSearchEngine

# Import MultiModalEmbeddings defensively to handle PyTorch issues
try:
    from .multi_modal_embeddings import MultiModalEmbeddings
except Exception:
    # If MultiModalEmbeddings fails to import (e.g., PyTorch issues), create a dummy class
    class MultiModalEmbeddings:
        def __init__(self, *args, **kwargs):
            import logging

            logging.warning(
                "MultiModalEmbeddings not available. Falling back to dummy implementation."
            )

        def is_available(self):
            return False


__all__ = [
    "ProjectDNAFingerprinter",
    "MultiModalEmbeddings",
    "SemanticSearchEngine",
    "PatternExtractor",
]
