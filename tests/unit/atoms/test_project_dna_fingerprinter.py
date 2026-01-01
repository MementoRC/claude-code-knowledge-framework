import tempfile

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
        "architecture": ["MVC"],
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
        "architecture": ["SPA"],
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
        "architecture": ["MVC"],
    }
    fp2 = {
        "languages": ["Python"],
        "language_versions": ["3.11"],
        "package_managers": ["pip"],
        "frameworks": ["Flask"],
        "testing": ["pytest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["pandas"],
        "architecture": ["MVC"],
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
        "architecture": ["MVC"],
    }
    fp2 = {
        "languages": ["JavaScript"],
        "language_versions": ["ES6"],
        "package_managers": ["npm"],
        "frameworks": ["React"],
        "testing": ["Jest"],
        "ci_cd": ["CircleCI"],
        "libraries": ["lodash"],
        "architecture": ["SPA"],
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
        "vector": [1.0, 2.0, 3.0],
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
        "architecture": ["MVC"],
    }
    fp2 = {
        "languages": ["JavaScript"],
        "language_versions": ["ES6"],
        "package_managers": ["npm"],
        "frameworks": ["React"],
        "testing": ["Jest"],
        "ci_cd": ["GitHub Actions"],
        "libraries": ["lodash"],
        "architecture": ["SPA"],
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
        "architecture": ["MVC", "Microservices"],
    }
    fingerprinter.tech_detector = DummyTechStackDetector(stack)
    with tempfile.TemporaryDirectory() as tmpdir:
        fp = fingerprinter.generate_fingerprint(tmpdir)
        assert "vector" in fp
        assert len(fp["vector"]) > 1000
