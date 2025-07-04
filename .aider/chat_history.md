
# aider chat started at 2025-06-27 20:41:40


#### Implement Project DNA Fingerprinting system for Task 4 in the UCKN framework:  
####   
#### REQUIREMENTS:  
#### 1. Create a new atom file `project_dna_fingerprinter.py` in `src/uckn/core/atoms/`  
#### 2. Implement DNA fingerprinting that takes TechStackDetector output and generates weighted feature vectors  
#### 3. Create compatibility matrix between technology combinations  
#### 4. Calculate similarity scores between projects  
#### 5. Implement serialization/deserialization for DNA fingerprints  
#### 6. Create comprehensive test suite in `tests/unit/atoms/test_project_dna_fingerprinter.py`  
####   
#### IMPLEMENTATION DETAILS:  
#### - DNA fingerprint should include: primary languages/versions, build systems, testing frameworks, CI/CD systems, libraries/dependencies, architecture patterns  
#### - Use weighted feature vectors for representation  
#### - Implement similarity scoring using cosine similarity or similar metric  
#### - Store fingerprints in queryable format compatible with ChromaDB  
#### - Follow existing atomic design patterns in the codebase  
#### - Include proper error handling and logging  
#### - Add comprehensive docstrings following existing patterns  
####   
#### INTEGRATION:  
#### - Import and use TechStackDetector from existing atoms  
#### - Follow the established project structure and coding conventions  
#### - Ensure compatibility with existing knowledge management system  
#### - Make it easily integrable with the KnowledgeManager organism  
####   
#### TEST STRATEGY:  
#### - Test fingerprint generation with various technology combinations  
#### - Verify similarity scoring between related projects    
#### - Test serialization/deserialization  
#### - Benchmark performance for large projects  
#### - Validate compatibility matrix against known technology relationships  
> Tags cache error: no such column: "size" - should this be a string literal in single-quotes?  
> Unable to use tags cache at /home/memento/ClaudeCode/claude-code-knowledge-framework/.aider.tags.cache.v4, falling back to memory cache  
> Cache recreation error: no such column: "size" - should this be a string literal in single-quotes?  

src/uckn/core/atoms/project_dna_fingerprinter.py
```python
<<<<<<< SEARCH
=======
"""
UCKN Project DNA Fingerprinter Atom

Implements project DNA fingerprinting for technology stack analysis,
similarity scoring, and compatibility matrix generation.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .tech_stack_detector import TechStackDetector

class ProjectDNAFingerprinter:
    """
    Generates and compares DNA fingerprints for software projects based on their technology stack.
    """

    # Define all possible features and their weights
    FEATURE_WEIGHTS = {
        "languages": 3.0,
        "language_versions": 2.0,
        "package_managers": 2.0,
        "frameworks": 2.5,
        "testing": 1.5,
        "ci_cd": 1.0,
        "libraries": 2.0,
        "architecture": 2.5,
    }

    # Compatibility matrix for some common tech combinations (expand as needed)
    COMPATIBILITY_MATRIX = {
        ("Python", "pytest"): 0.9,
        ("Python", "pip"): 0.95,
        ("Python", "poetry"): 0.95,
        ("Python", "Django"): 0.8,
        ("JavaScript", "npm"): 0.95,
        ("JavaScript", "Jest"): 0.85,
        ("Node.js", "npm"): 0.98,
        ("React", "Jest"): 0.9,
        ("GitHub Actions", "pytest"): 0.7,
        # Add more as needed
    }

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.tech_detector = TechStackDetector()

    def generate_fingerprint(self, project_path: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a DNA fingerprint for a project at the given path.
        """
        try:
            stack = self.tech_detector.analyze_project(project_path)
            fingerprint = {
                "languages": stack.get("languages", []),
                "language_versions": stack.get("language_versions", []),
                "package_managers": stack.get("package_managers", []),
                "frameworks": stack.get("frameworks", []),
                "testing": stack.get("testing", []),
                "ci_cd": stack.get("ci_cd", []),
                "libraries": stack.get("libraries", []),
                "architecture": stack.get("architecture", []),
            }
            if extra_metadata:
                fingerprint.update(extra_metadata)
            fingerprint["vector"] = self._to_weighted_vector(fingerprint)
            return fingerprint
        except Exception as e:
            self._logger.error(f"Failed to generate fingerprint: {e}")
            return {}

    def _to_weighted_vector(self, fingerprint: Dict[str, Any]) -> List[float]:
        """
        Convert fingerprint dict to a weighted feature vector.
        """
        # Build a global feature list for all possible values
        features = self._get_global_feature_list(fingerprint)
        vector = []
        for feature in features:
            present = self._feature_present(feature, fingerprint)
            weight = self._get_feature_weight(feature)
            vector.append(weight if present else 0.0)
        return vector

    def _get_global_feature_list(self, fingerprint: Dict[str, Any]) -> List[str]:
        """
        Build a sorted list of all features present in the fingerprint.
        """
        features = []
        for key in self.FEATURE_WEIGHTS.keys():
            values = fingerprint.get(key, [])
            if isinstance(values, list):
                features.extend(values)
            elif isinstance(values, str):
                features.append(values)
        return sorted(set(features))

    def _feature_present(self, feature: str, fingerprint: Dict[str, Any]) -> bool:
        """
        Check if a feature is present in any fingerprint category.
        """
        for key in self.FEATURE_WEIGHTS.keys():
            values = fingerprint.get(key, [])
            if isinstance(values, list) and feature in values:
                return True
            elif isinstance(values, str) and feature == values:
                return True
        return False

    def _get_feature_weight(self, feature: str) -> float:
        """
        Get the weight for a feature based on its category.
        """
        for key, weight in self.FEATURE_WEIGHTS.items():
            if feature.lower() in key.lower():
                return weight
        # Default: try to infer from known mappings
        for (a, b), compat in self.COMPATIBILITY_MATRIX.items():
            if feature in (a, b):
                return 2.0
        return 1.0

    def compute_similarity(self, fp1: Dict[str, Any], fp2: Dict[str, Any]) -> float:
        """
        Compute similarity score between two fingerprints using cosine similarity.
        """
        try:
            features = sorted(set(self._get_global_feature_list(fp1) + self._get_global_feature_list(fp2)))
            v1 = np.array([self._get_feature_weight(f) if self._feature_present(f, fp1) else 0.0 for f in features])
            v2 = np.array([self._get_feature_weight(f) if self._feature_present(f, fp2) else 0.0 for f in features])
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                return 0.0
            cosine_sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
            # Adjust with compatibility matrix
            compat_bonus = self._compatibility_bonus(fp1, fp2)
            return min(1.0, cosine_sim + compat_bonus)
        except Exception as e:
            self._logger.error(f"Failed to compute similarity: {e}")
            return 0.0

    def _compatibility_bonus(self, fp1: Dict[str, Any], fp2: Dict[str, Any]) -> float:
        """
        Add bonus to similarity based on known compatible tech pairs.
        """
        bonus = 0.0
        for (a, b), score in self.COMPATIBILITY_MATRIX.items():
            if (self._feature_present(a, fp1) and self._feature_present(b, fp2)) or \
               (self._feature_present(b, fp1) and self._feature_present(a, fp2)):
                bonus += score * 0.05  # small bonus per compatible pair
        return bonus

    def generate_compatibility_matrix(self, fingerprints: List[Dict[str, Any]]) -> List[List[float]]:
        """
        Generate a compatibility matrix for a list of project fingerprints.
        """
        n = len(fingerprints)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    matrix[i][j] = self.compute_similarity(fingerprints[i], fingerprints[j])
        return matrix

    def serialize_fingerprint(self, fingerprint: Dict[str, Any]) -> str:
        """
        Serialize a fingerprint to a JSON string.
        """
        try:
            return json.dumps(fingerprint, sort_keys=True)
        except Exception as e:
            self._logger.error(f"Failed to serialize fingerprint: {e}")
            return ""

    def deserialize_fingerprint(self, data: str) -> Dict[str, Any]:
        """
        Deserialize a fingerprint from a JSON string.
        """
        try:
            return json.loads(data)
        except Exception as e:
            self._logger.error(f"Failed to deserialize fingerprint: {e}")
            return {}

>>>>>>> REPLACE
```

src/uckn/core/atoms/__init__.py
```python
<<<<<<< SEARCH
=======
from .project_dna_fingerprinter import ProjectDNAFingerprinter
>>>>>>> REPLACE
```

tests/unit/atoms/test_project_dna_fingerprinter.py
```python
<<<<<<< SEARCH
=======
import os
import tempfile
import json
import pytest
from src.uckn.core.atoms.project_dna_fingerprinter import ProjectDNAFingerprinter

class DummyTechStackDetector:
    """
    Dummy TechStackDetector for controlled test input.
    """
    def __init__(self, stack):
        self._stack = stack

    def analyze_project(self, project_path):
        return self._stack

@pytest.fixture
def fingerprinter():
    fp = ProjectDNAFingerprinter()
    return fp

def test_fingerprint_generation_python(fingerprinter, monkeypatch):
    stack = {
        "languages": ["Python"],
        "language_versions": ["3.10"],
        "package_managers": ["pip"],
        "frameworks": ["Django"],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["numpy", "pandas"],
        "architecture": ["MVC"]
    }
    # Patch tech_detector
    fingerprinter.tech_detector = DummyTechStackDetector(stack)
    with tempfile.TemporaryDirectory() as tmpdir:
        fp = fingerprinter.generate_fingerprint(tmpdir)
        assert "languages" in fp
        assert "vector" in fp
        assert "Python" in fp["languages"]
        assert isinstance(fp["vector"], list)
        assert any(x > 0 for x in fp["vector"])

def test_fingerprint_generation_javascript(fingerprinter, monkeypatch):
    stack = {
        "languages": ["JavaScript"],
        "language_versions": ["ES6"],
        "package_managers": ["npm"],
        "frameworks": ["React"],
        "testing": ["Jest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["lodash"],
        "architecture": ["SPA"]
    }
    fingerprinter.tech_detector = DummyTechStackDetector(stack)
    with tempfile.TemporaryDirectory() as tmpdir:
        fp = fingerprinter.generate_fingerprint(tmpdir)
        assert "JavaScript" in fp["languages"]
        assert "vector" in fp

def test_similarity_score_related_projects(fingerprinter):
    fp1 = {
        "languages": ["Python"],
        "language_versions": ["3.10"],
        "package_managers": ["pip"],
        "frameworks": ["Django"],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["numpy"],
        "architecture": ["MVC"]
    }
    fp2 = {
        "languages": ["Python"],
        "language_versions": ["3.11"],
        "package_managers": ["pip"],
        "frameworks": ["Flask"],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["pandas"],
        "architecture": ["MVC"]
    }
    fingerprinter.tech_detector = DummyTechStackDetector(fp1)
    v1 = fingerprinter.generate_fingerprint("dummy1")
    fingerprinter.tech_detector = DummyTechStackDetector(fp2)
    v2 = fingerprinter.generate_fingerprint("dummy2")
    sim = fingerprinter.compute_similarity(v1, v2)
    assert 0.5 < sim <= 1.0

def test_similarity_score_unrelated_projects(fingerprinter):
    fp1 = {
        "languages": ["Python"],
        "language_versions": ["3.10"],
        "package_managers": ["pip"],
        "frameworks": ["Django"],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["numpy"],
        "architecture": ["MVC"]
    }
    fp2 = {
        "languages": ["JavaScript"],
        "language_versions": ["ES6"],
        "package_managers": ["npm"],
        "frameworks": ["React"],
        "testing": ["Jest"],
        "ci_cd": ["CircleCI"],
        "libraries": ["lodash"],
        "architecture": ["SPA"]
    }
    fingerprinter.tech_detector = DummyTechStackDetector(fp1)
    v1 = fingerprinter.generate_fingerprint("dummy1")
    fingerprinter.tech_detector = DummyTechStackDetector(fp2)
    v2 = fingerprinter.generate_fingerprint("dummy2")
    sim = fingerprinter.compute_similarity(v1, v2)
    assert 0.0 <= sim < 0.5

def test_serialization_deserialization(fingerprinter):
    fp = {
        "languages": ["Python"],
        "language_versions": ["3.10"],
        "package_managers": ["pip"],
        "frameworks": ["Django"],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["numpy"],
        "architecture": ["MVC"],
        "vector": [1.0, 2.0, 3.0]
    }
    s = fingerprinter.serialize_fingerprint(fp)
    assert isinstance(s, str)
    fp2 = fingerprinter.deserialize_fingerprint(s)
    assert fp2["languages"] == ["Python"]
    assert fp2["vector"] == [1.0, 2.0, 3.0]

def test_compatibility_matrix(fingerprinter):
    fp1 = {
        "languages": ["Python"],
        "language_versions": ["3.10"],
        "package_managers": ["pip"],
        "frameworks": ["Django"],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["numpy"],
        "architecture": ["MVC"]
    }
    fp2 = {
        "languages": ["JavaScript"],
        "language_versions": ["ES6"],
        "package_managers": ["npm"],
        "frameworks": ["React"],
        "testing": ["Jest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["lodash"],
        "architecture": ["SPA"]
    }
    fingerprinter.tech_detector = DummyTechStackDetector(fp1)
    v1 = fingerprinter.generate_fingerprint("dummy1")
    fingerprinter.tech_detector = DummyTechStackDetector(fp2)
    v2 = fingerprinter.generate_fingerprint("dummy2")
    matrix = fingerprinter.generate_compatibility_matrix([v1, v2])
    assert len(matrix) == 2
    assert matrix[0][0] == 1.0
    assert 0.0 <= matrix[0][1] <= 1.0
    assert 0.0 <= matrix[1][0] <= 1.0
    assert matrix[1][1] == 1.0

def test_performance_large_project(monkeypatch, fingerprinter):
    # Simulate a large project with many libraries and frameworks
    stack = {
        "languages": ["Python"],
        "language_versions": ["3.10"],
        "package_managers": ["pip"],
        "frameworks": ["Django", "Flask", "FastAPI", "Tornado"],
        "testing": ["pytest", "unittest", "nose"],
        "ci_cd": ["GitHub Actions", "TravisCI", "CircleCI"],
        "libraries": [f"lib{i}" for i in range(1000)],
        "architecture": ["MVC", "Microservices"]
    }
    fingerprinter.tech_detector = DummyTechStackDetector(stack)
    with tempfile.TemporaryDirectory() as tmpdir:
        fp = fingerprinter.generate_fingerprint(tmpdir)
        assert "vector" in fp
        assert len(fp["vector"]) > 1000

>>>>>>> REPLACE
```


# aider chat started at 2025-07-01 10:59:30


#### Complete the documentation website implementation by creating the missing files:  
####   
#### 1. Create docs/version.json for version management  
#### 2. Create docs/multimedia/video-tutorials.md with placeholder content for future video tutorials  
#### 3. Create docs/multimedia/demos.md with placeholder content for interactive demos  
#### 4. Create docs/assets/ directory structure for logo and favicon placeholders  
#### 5. Update the navigation in mkdocs.yml to include all existing docs properly  
#### 6. Ensure the existing SYSTEM_DESIGN.md and performance_optimizations.md are included in navigation  
####   
#### Make sure all content is professional and ready for production use.  
> Tags cache error: no such column: "size" - should this be a string literal in single-quotes?  
> Unable to use tags cache at /home/memento/ClaudeCode/claude-code-knowledge-framework/.aider.tags.cache.v4, falling back to memory cache  
> Cache recreation error: Cannot call rmtree on a symbolic link  

# aider chat started at 2025-07-03 21:12:07


#### Fix the PyTorch docstring conflict error that's causing CI test failures. The error "RuntimeError: function '_has_torch_function' already has a docstring" is a known PyTorch issue.  
####   
#### UCKN Context:  
#### - Error: PyTorch docstring conflict in torch/overrides.py  
#### - Impact: 14 MCP server tests failing due to import issues  
#### - Root Cause: PyTorch dependency loading conflict with sentence-transformers  
#### - Solution Priority: HIGH (blocking all CI)  
####   
#### Apply defensive programming solution:  
#### 1. Add try/catch around torch imports in multi_modal_embeddings.py  
#### 2. Make torch/sentence-transformers imports optional with graceful fallback  
#### 3. Add environment variable to control torch usage in tests  
#### 4. Ensure tests can run without PyTorch dependencies  
####   
#### The fix should allow tests to run even if PyTorch has issues, while maintaining functionality when PyTorch works correctly.  
####   
#### Requirements:  
#### - Maintain backward compatibility  
#### - Allow tests to pass without PyTorch  
#### - Keep full functionality when PyTorch is available  
#### - Add defensive imports with fallbacks  
> Tags cache error: no such column: "size" - should this be a string literal in single-quotes?  
> Unable to use tags cache at /home/memento/ClaudeCode/claude-code-knowledge-framework/.aider.tags.cache.v4, falling back to memory cache  
> Cache recreation error: Cannot call rmtree on a symbolic link  

src/uckn/core/atoms/multi_modal_embeddings.py
```python
<<<<<<< SEARCH
from typing import List, Dict, Optional, Any, Union
import logging
import hashlib
import threading
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    AutoTokenizer = None
    AutoModel = None
    torch = None
    TRANSFORMERS_AVAILABLE = False
=======
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
>>>>>>> REPLACE
```

src/uckn/core/atoms/multi_modal_embeddings.py
```python
<<<<<<< SEARCH
    def __init__(self, device: Optional[str] = None):
        self._logger = logging.getLogger(__name__)
        self.device = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")
        self._lock = threading.Lock()

        # Model loading
        self.code_tokenizer = None
        self.code_model = None
        self.text_model = None

        self._init_code_model()
        self._init_text_model()

        # In-memory cache for embeddings
        self._embedding_cache = {}
=======
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
>>>>>>> REPLACE
```

src/uckn/core/atoms/multi_modal_embeddings.py
```python
<<<<<<< SEARCH
    def _init_code_model(self):
        if not TRANSFORMERS_AVAILABLE:
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
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self._logger.warning("SentenceTransformers not available. Text embedding will be disabled.")
            return
        try:
            self.text_model = SentenceTransformer(self._TEXT_MODEL_NAME, device=self.device)
            self._logger.info(f"Loaded text model: {self._TEXT_MODEL_NAME}")
        except Exception as e:
            self._logger.error(f"Failed to load text model '{self._TEXT_MODEL_NAME}': {e}")
            self.text_model = None
=======
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
>>>>>>> REPLACE
```

src/uckn/core/atoms/multi_modal_embeddings.py
```python
<<<<<<< SEARCH
    def _embed_code(self, code: str) -> Optional[List[float]]:
        key = f"code:{self._hash_input(code)}"
        cached = self._get_cached_embedding(key)
        if cached:
            return cached
        if self.code_model and self.code_tokenizer:
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
=======
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
>>>>>>> REPLACE
```

src/uckn/core/atoms/multi_modal_embeddings.py
```python
<<<<<<< SEARCH
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
=======
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
>>>>>>> REPLACE
```

src/uckn/core/atoms/multi_modal_embeddings.py
```python
<<<<<<< SEARCH
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
        return chroma_connector.search_documents(
            collection_name=collection_name,
            query_embedding=query_embedding,
            n_results=limit,
            min_similarity=min_similarity,
            where_clause=metadata_filter
        )
=======
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
>>>>>>> REPLACE
```

