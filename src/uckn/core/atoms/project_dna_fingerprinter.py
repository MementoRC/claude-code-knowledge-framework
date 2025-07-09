"""
UCKN Project DNA Fingerprinter Atom

Implements project DNA fingerprinting for technology stack analysis,
similarity scoring, and compatibility matrix generation.
"""

import json
import logging
from typing import Any

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

    def generate_fingerprint(
        self, project_path: str, extra_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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

    def _to_weighted_vector(self, fingerprint: dict[str, Any]) -> list[float]:
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

    def _get_global_feature_list(self, fingerprint: dict[str, Any]) -> list[str]:
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

    def _feature_present(self, feature: str, fingerprint: dict[str, Any]) -> bool:
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

    def compute_similarity(self, fp1: dict[str, Any], fp2: dict[str, Any]) -> float:
        """
        Compute similarity score between two fingerprints using cosine similarity.
        """
        try:
            features = sorted(
                set(
                    self._get_global_feature_list(fp1)
                    + self._get_global_feature_list(fp2)
                )
            )
            v1 = np.array(
                [
                    self._get_feature_weight(f)
                    if self._feature_present(f, fp1)
                    else 0.0
                    for f in features
                ]
            )
            v2 = np.array(
                [
                    self._get_feature_weight(f)
                    if self._feature_present(f, fp2)
                    else 0.0
                    for f in features
                ]
            )
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                return 0.0
            cosine_sim = float(
                np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            )
            # Adjust with compatibility matrix
            compat_bonus = self._compatibility_bonus(fp1, fp2)
            return min(1.0, cosine_sim + compat_bonus)
        except Exception as e:
            self._logger.error(f"Failed to compute similarity: {e}")
            return 0.0

    def _compatibility_bonus(self, fp1: dict[str, Any], fp2: dict[str, Any]) -> float:
        """
        Add bonus to similarity based on known compatible tech pairs.
        """
        bonus = 0.0
        for (a, b), score in self.COMPATIBILITY_MATRIX.items():
            if (self._feature_present(a, fp1) and self._feature_present(b, fp2)) or (
                self._feature_present(b, fp1) and self._feature_present(a, fp2)
            ):
                bonus += score * 0.05  # small bonus per compatible pair
        return bonus

    def generate_compatibility_matrix(
        self, fingerprints: list[dict[str, Any]]
    ) -> list[list[float]]:
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
                    matrix[i][j] = self.compute_similarity(
                        fingerprints[i], fingerprints[j]
                    )
        return matrix

    def serialize_fingerprint(self, fingerprint: dict[str, Any]) -> str:
        """
        Serialize a fingerprint to a JSON string.
        """
        try:
            return json.dumps(fingerprint, sort_keys=True)
        except Exception as e:
            self._logger.error(f"Failed to serialize fingerprint: {e}")
            return ""

    def deserialize_fingerprint(self, data: str) -> dict[str, Any]:
        """
        Deserialize a fingerprint from a JSON string.
        """
        try:
            return json.loads(data)
        except Exception as e:
            self._logger.error(f"Failed to deserialize fingerprint: {e}")
            return {}
