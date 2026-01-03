"""
UCKN ML Environment Manager

Provides environment-aware ML dependency loading with graceful fallbacks.
Automatically detects CI vs production environments and loads appropriate dependencies.
"""

import importlib.util
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class MLEnvironment(Enum):
    """ML environment types with different capability levels."""

    DISABLED = "disabled"  # UCKN_DISABLE_TORCH=1 or explicit disable
    CI_MINIMAL = "ci_minimal"  # CI environment with fallbacks only
    DEVELOPMENT = "development"  # Dev environment with optional ML
    PRODUCTION = "production"  # Full ML capabilities required


@dataclass
class MLCapabilities:
    """Available ML capabilities in current environment."""

    sentence_transformers: bool = False
    transformers: bool = False
    chromadb: bool = False
    torch: bool = False
    has_gpu: bool = False
    environment: MLEnvironment = MLEnvironment.DISABLED
    fallback_embeddings: bool = True  # Always available


class MLEnvironmentManager:
    """
    Manages ML dependency loading based on environment detection.

    Environment Detection Logic:
    1. UCKN_DISABLE_TORCH=1 -> DISABLED
    2. CI=true or GITHUB_ACTIONS=true -> CI_MINIMAL
    3. pixi ml-heavy features available -> PRODUCTION
    4. pixi ml features available -> DEVELOPMENT
    5. Default -> CI_MINIMAL (safe fallback)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._capabilities: MLCapabilities | None = None
        self._imports: dict[str, Any] = {}

    @property
    def capabilities(self) -> MLCapabilities:
        """Get current ML capabilities (cached after first detection)."""
        if self._capabilities is None:
            self._capabilities = self._detect_environment()
        return self._capabilities

    def _detect_environment(self) -> MLCapabilities:
        """Detect current environment and available ML capabilities."""

        # Check for explicit disable
        if os.environ.get("UCKN_DISABLE_TORCH", "0") == "1":
            self.logger.info(
                "ML functionality explicitly disabled via UCKN_DISABLE_TORCH"
            )
            return MLCapabilities(environment=MLEnvironment.DISABLED)

        # Check for CI environment
        is_ci = (
            os.environ.get("CI", "").lower() == "true"
            or os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
            or os.environ.get("CONTINUOUS_INTEGRATION", "").lower() == "true"
        )

        if is_ci:
            self.logger.info("CI environment detected - using minimal ML fallbacks")
            return MLCapabilities(environment=MLEnvironment.CI_MINIMAL)

        # Detect available ML packages
        capabilities = MLCapabilities()

        # Test sentence-transformers availability
        if self._test_import("sentence_transformers"):
            capabilities.sentence_transformers = True
            self.logger.debug("sentence-transformers available")

        # Test transformers availability
        if self._test_import("transformers"):
            capabilities.transformers = True
            self.logger.debug("transformers available")

        # Test ChromaDB availability
        if self._test_import("chromadb"):
            capabilities.chromadb = True
            self.logger.debug("chromadb available")

        # Test PyTorch availability
        if self._test_import("torch"):
            capabilities.torch = True
            # Test GPU availability
            try:
                torch = self._get_import("torch")
                if torch and hasattr(torch, "cuda") and torch.cuda.is_available():
                    capabilities.has_gpu = True
                    self.logger.debug("GPU acceleration available")
            except Exception:
                pass

        # Determine environment level
        if (
            capabilities.sentence_transformers
            and capabilities.chromadb
            and capabilities.torch
        ):
            capabilities.environment = MLEnvironment.PRODUCTION
            self.logger.info("Production ML environment detected - full capabilities")
        elif capabilities.sentence_transformers or capabilities.transformers:
            capabilities.environment = MLEnvironment.DEVELOPMENT
            self.logger.info(
                "Development ML environment detected - partial capabilities"
            )
        else:
            capabilities.environment = MLEnvironment.CI_MINIMAL
            self.logger.info("Minimal ML environment detected - fallbacks only")

        return capabilities

    def _test_import(self, module_name: str) -> bool:
        """Test if a module can be imported successfully."""
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return False
            # Try actual import to catch import-time errors
            module = importlib.import_module(module_name)
            self._imports[module_name] = module
            return True
        except Exception as e:
            self.logger.debug(f"Import test failed for {module_name}: {e}")
            return False

    def _get_import(self, module_name: str) -> Any | None:
        """Get cached import or attempt import."""
        if module_name in self._imports:
            return self._imports[module_name]
        if self._test_import(module_name):
            return self._imports[module_name]
        return None

    def get_sentence_transformer(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> Any | None:
        """Get SentenceTransformer model if available."""
        if not self.capabilities.sentence_transformers:
            return None

        try:
            SentenceTransformer = self._get_import(
                "sentence_transformers"
            ).SentenceTransformer
            device = "cuda" if self.capabilities.has_gpu else "cpu"
            return SentenceTransformer(model_name, device=device)
        except Exception as e:
            self.logger.error(
                f"Failed to load SentenceTransformer model {model_name}: {e}"
            )
            return None

    def get_transformers_model(self, model_name: str) -> tuple[Any | None, Any | None]:
        """Get transformers AutoModel and AutoTokenizer if available."""
        if not self.capabilities.transformers:
            return None, None

        try:
            transformers = self._get_import("transformers")
            AutoModel = transformers.AutoModel
            AutoTokenizer = transformers.AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            device = "cuda" if self.capabilities.has_gpu else "cpu"
            model = AutoModel.from_pretrained(model_name).to(device)

            return model, tokenizer
        except Exception as e:
            self.logger.error(f"Failed to load transformers model {model_name}: {e}")
            return None, None

    def get_chromadb_client(self, persist_directory: str) -> Any | None:
        """Get ChromaDB client if available."""
        if not self.capabilities.chromadb:
            return None

        try:
            chromadb = self._get_import("chromadb")
            return chromadb.PersistentClient(
                path=persist_directory,
                settings=chromadb.config.Settings(anonymized_telemetry=False),
            )
        except Exception as e:
            self.logger.error(f"Failed to create ChromaDB client: {e}")
            return None

    def should_use_real_ml(self) -> bool:
        """Determine if real ML models should be used vs fallbacks."""
        return self.capabilities.environment in [
            MLEnvironment.DEVELOPMENT,
            MLEnvironment.PRODUCTION,
        ]

    def should_download_models(self) -> bool:
        """Determine if model downloading is allowed (avoid in CI)."""
        return self.capabilities.environment == MLEnvironment.PRODUCTION

    def get_device(self) -> str:
        """Get recommended device for ML operations."""
        if self.capabilities.has_gpu:
            return "cuda"
        return "cpu"

    def get_environment_info(self) -> dict[str, Any]:
        """Get detailed environment information for debugging."""
        caps = self.capabilities
        return {
            "environment": caps.environment.value,
            "sentence_transformers": caps.sentence_transformers,
            "transformers": caps.transformers,
            "chromadb": caps.chromadb,
            "torch": caps.torch,
            "has_gpu": caps.has_gpu,
            "fallback_embeddings": caps.fallback_embeddings,
            "device": self.get_device(),
            "should_use_real_ml": self.should_use_real_ml(),
            "should_download_models": self.should_download_models(),
            "ci_detected": os.environ.get("CI", "false").lower() == "true",
            "torch_disabled": os.environ.get("UCKN_DISABLE_TORCH", "0") == "1",
        }


# Global instance
_ml_manager = None


def get_ml_manager() -> MLEnvironmentManager:
    """Get global ML environment manager instance."""
    global _ml_manager
    if _ml_manager is None:
        _ml_manager = MLEnvironmentManager()
    return _ml_manager


def is_ml_available() -> bool:
    """Quick check if any ML functionality is available."""
    return get_ml_manager().should_use_real_ml()


def get_ml_environment() -> MLEnvironment:
    """Get current ML environment type."""
    return get_ml_manager().capabilities.environment
