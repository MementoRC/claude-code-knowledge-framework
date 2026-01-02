"""
Tests for ML Environment Manager

Tests environment detection, capability management, and graceful fallbacks.
Works in both CI (fallback mode) and production (full ML) environments.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.uckn.core.ml_environment_manager import (
    MLCapabilities,
    MLEnvironment,
    MLEnvironmentManager,
    get_ml_environment,
    get_ml_manager,
    is_ml_available,
)


class TestMLEnvironmentManager:
    """Test ML environment detection and capability management."""

    def test_disabled_environment(self):
        """Test explicit disable via environment variable."""
        with patch.dict(os.environ, {"UCKN_DISABLE_TORCH": "1"}):
            manager = MLEnvironmentManager()
            caps = manager.capabilities

            assert caps.environment == MLEnvironment.DISABLED
            assert not caps.sentence_transformers
            assert not caps.transformers
            assert not caps.chromadb
            assert not caps.torch
            assert not caps.has_gpu
            assert caps.fallback_embeddings  # Always available

    def test_ci_environment_detection(self):
        """Test CI environment detection."""
        ci_vars = [
            {"CI": "true"},
            {"GITHUB_ACTIONS": "true"},
            {"CONTINUOUS_INTEGRATION": "true"},
        ]

        for ci_env in ci_vars:
            # Ensure TORCH is not disabled for this test
            env_vars = {**ci_env, "UCKN_DISABLE_TORCH": "0"}
            with patch.dict(os.environ, env_vars, clear=False):
                manager = MLEnvironmentManager()
                caps = manager.capabilities

                assert caps.environment == MLEnvironment.CI_MINIMAL
                assert caps.fallback_embeddings

    def test_production_environment_detection(self):
        """Test production environment with full ML capabilities."""
        # Clear UCKN_DISABLE_TORCH and CI variables to allow production detection
        # Use clear=True to remove CI, GITHUB_ACTIONS, etc.
        minimal_env = {k: v for k, v in os.environ.items()
                       if k not in ("CI", "GITHUB_ACTIONS", "CONTINUOUS_INTEGRATION", "UCKN_DISABLE_TORCH")}
        minimal_env["UCKN_DISABLE_TORCH"] = "0"
        with patch.dict(os.environ, minimal_env, clear=True):
            # Mock all ML packages as available
            with patch.multiple(
                "src.uckn.core.ml_environment_manager.MLEnvironmentManager",
                _test_import=MagicMock(return_value=True),
            ):
                # Mock torch.cuda.is_available
                mock_torch = MagicMock()
                mock_torch.cuda.is_available.return_value = True

                with patch.dict("sys.modules", {"torch": mock_torch}):
                    manager = MLEnvironmentManager()
                    manager._imports["torch"] = mock_torch
                    caps = manager.capabilities

                    assert caps.environment == MLEnvironment.PRODUCTION
                    assert caps.sentence_transformers
                    assert caps.transformers
                    assert caps.chromadb
                    assert caps.torch
                    assert caps.has_gpu

    def test_development_environment_detection(self):
        """Test development environment with partial ML capabilities."""

        def mock_import(module_name):
            return module_name in ["sentence_transformers"]

        # Clear UCKN_DISABLE_TORCH and CI variables to allow development detection
        minimal_env = {k: v for k, v in os.environ.items()
                       if k not in ("CI", "GITHUB_ACTIONS", "CONTINUOUS_INTEGRATION", "UCKN_DISABLE_TORCH")}
        minimal_env["UCKN_DISABLE_TORCH"] = "0"
        with patch.dict(os.environ, minimal_env, clear=True):
            with patch.object(
                MLEnvironmentManager, "_test_import", side_effect=mock_import
            ):
                manager = MLEnvironmentManager()
                caps = manager.capabilities

                assert caps.environment == MLEnvironment.DEVELOPMENT
                assert caps.sentence_transformers
                assert not caps.transformers
                assert not caps.chromadb

    def test_capability_caching(self):
        """Test that capabilities are cached after first detection."""
        manager = MLEnvironmentManager()

        # First call
        caps1 = manager.capabilities

        # Second call should return same object (cached)
        caps2 = manager.capabilities

        assert caps1 is caps2

    def test_model_loading_methods(self):
        """Test model loading methods with proper fallbacks."""
        manager = MLEnvironmentManager()

        # When capabilities not available, should return None
        sentence_model = manager.get_sentence_transformer()
        assert sentence_model is None

        transformers_model, tokenizer = manager.get_transformers_model("test-model")
        assert transformers_model is None
        assert tokenizer is None

        chromadb_client = manager.get_chromadb_client("/tmp/test")
        assert chromadb_client is None

    def test_device_selection(self):
        """Test device selection logic."""
        manager = MLEnvironmentManager()

        # Without GPU, should default to CPU
        device = manager.get_device()
        assert device == "cpu"

    def test_environment_info(self):
        """Test environment info collection."""
        manager = MLEnvironmentManager()
        info = manager.get_environment_info()

        required_keys = [
            "environment",
            "sentence_transformers",
            "transformers",
            "chromadb",
            "torch",
            "has_gpu",
            "fallback_embeddings",
            "device",
            "should_use_real_ml",
            "should_download_models",
            "ci_detected",
            "torch_disabled",
        ]

        for key in required_keys:
            assert key in info

        assert isinstance(info["environment"], str)
        assert isinstance(info["fallback_embeddings"], bool)
        assert info["fallback_embeddings"] is True  # Always available

    def test_should_use_real_ml(self):
        """Test real ML usage decision logic."""
        # Test in CI environment
        with patch.dict(os.environ, {"CI": "true"}):
            manager = MLEnvironmentManager()
            assert not manager.should_use_real_ml()

        # Test in disabled environment
        with patch.dict(os.environ, {"UCKN_DISABLE_TORCH": "1"}):
            manager = MLEnvironmentManager()
            assert not manager.should_use_real_ml()

    def test_should_download_models(self):
        """Test model downloading decision logic."""
        # Only production environment should download models
        with patch.object(MLEnvironmentManager, "_detect_environment") as mock_detect:
            mock_detect.return_value = MLCapabilities(
                environment=MLEnvironment.PRODUCTION
            )
            manager = MLEnvironmentManager()
            assert manager.should_download_models()

            mock_detect.return_value = MLCapabilities(
                environment=MLEnvironment.DEVELOPMENT
            )
            manager = MLEnvironmentManager()
            assert not manager.should_download_models()

    def test_global_manager_functions(self):
        """Test global manager access functions."""
        # Test singleton behavior
        manager1 = get_ml_manager()
        manager2 = get_ml_manager()
        assert manager1 is manager2

        # Test utility functions
        available = is_ml_available()
        assert isinstance(available, bool)

        environment = get_ml_environment()
        assert isinstance(environment, MLEnvironment)

    def test_import_error_handling(self):
        """Test graceful handling of import errors."""

        def mock_import_error(module_name):
            raise ImportError(f"No module named '{module_name}'")

        with patch("importlib.import_module", side_effect=mock_import_error):
            manager = MLEnvironmentManager()
            caps = manager.capabilities

            # Should handle import errors gracefully
            assert caps.environment in [
                MLEnvironment.CI_MINIMAL,
                MLEnvironment.DISABLED,
            ]
            assert caps.fallback_embeddings

    def test_find_spec_none_handling(self):
        """Test handling when importlib.util.find_spec returns None."""
        with patch("importlib.util.find_spec", return_value=None):
            manager = MLEnvironmentManager()
            caps = manager.capabilities

            # Should detect no packages available
            assert not caps.sentence_transformers
            assert not caps.transformers
            assert not caps.chromadb
            assert not caps.torch


class TestMLCapabilities:
    """Test MLCapabilities dataclass."""

    def test_default_values(self):
        """Test default capability values."""
        caps = MLCapabilities()

        assert not caps.sentence_transformers
        assert not caps.transformers
        assert not caps.chromadb
        assert not caps.torch
        assert not caps.has_gpu
        assert caps.environment == MLEnvironment.DISABLED
        assert caps.fallback_embeddings is True

    def test_custom_values(self):
        """Test custom capability values."""
        caps = MLCapabilities(
            sentence_transformers=True,
            torch=True,
            environment=MLEnvironment.PRODUCTION,
            has_gpu=True,
        )

        assert caps.sentence_transformers
        assert caps.torch
        assert caps.has_gpu
        assert caps.environment == MLEnvironment.PRODUCTION


class TestEnvironmentIntegration:
    """Integration tests for different environment scenarios."""

    @pytest.mark.skipif(
        not os.environ.get("UCKN_DISABLE_TORCH") == "1",
        reason="Test requires TORCH disabled mode (CI environment)",
    )
    def test_ci_integration(self):
        """Test integration in CI environment with TORCH disabled."""
        manager = get_ml_manager()
        caps = manager.capabilities

        # In CI with TORCH disabled, should use fallbacks
        assert caps.environment in [MLEnvironment.DISABLED, MLEnvironment.CI_MINIMAL]
        assert caps.fallback_embeddings
        assert not manager.should_download_models()

        # Should still provide device and environment info
        device = manager.get_device()
        assert device == "cpu"

        env_info = manager.get_environment_info()
        assert env_info["torch_disabled"]

    @pytest.mark.skipif(
        os.environ.get("UCKN_DISABLE_TORCH") == "1",
        reason="Test requires TORCH enabled mode (development/production)",
    )
    def test_development_integration(self):
        """Test integration in development environment."""
        manager = get_ml_manager()
        caps = manager.capabilities

        # Should detect actual environment capabilities
        assert caps.fallback_embeddings

        env_info = manager.get_environment_info()
        assert not env_info["torch_disabled"]

        # Environment should be reasonable
        assert caps.environment in [
            MLEnvironment.CI_MINIMAL,
            MLEnvironment.DEVELOPMENT,
            MLEnvironment.PRODUCTION,
        ]
