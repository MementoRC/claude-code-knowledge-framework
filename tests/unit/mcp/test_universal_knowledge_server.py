"""
Test Universal Knowledge MCP Server functionality
"""

import json
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock the MCP imports before importing the server
sys_modules_backup = {}


def setup_mcp_mocks():
    """Setup mocks for MCP components"""
    global sys_modules_backup

    # Mock MCP modules
    mock_mcp = MagicMock()
    mock_mcp.server = MagicMock()
    mock_mcp.server.Server = MagicMock
    mock_mcp.server.models = MagicMock()
    mock_mcp.server.stdio = MagicMock()
    mock_mcp.types = MagicMock()

    # Store original modules
    import sys

    sys_modules_backup = {
        name: sys.modules.get(name)
        for name in [
            "mcp",
            "mcp.server",
            "mcp.server.models",
            "mcp.server.stdio",
            "mcp.types",
        ]
    }

    # Replace with mocks
    sys.modules["mcp"] = mock_mcp
    sys.modules["mcp.server"] = mock_mcp.server
    sys.modules["mcp.server.models"] = mock_mcp.server.models
    sys.modules["mcp.server.stdio"] = mock_mcp.server.stdio
    sys.modules["mcp.types"] = mock_mcp.types

    return mock_mcp


# Setup mocks before importing
mock_mcp = setup_mcp_mocks()

# Now import the server
with patch.dict(
    "sys.modules",
    {
        "mcp": mock_mcp,
        "mcp.server": mock_mcp.server,
        "mcp.server.models": mock_mcp.server.models,
        "mcp.server.stdio": mock_mcp.server.stdio,
        "mcp.types": mock_mcp.types,
    },
):
    from src.uckn.mcp.universal_knowledge_server import UniversalKnowledgeServer


class TestUniversalKnowledgeServer:
    """Test Universal Knowledge MCP Server functionality"""

    def setup_method(self):
        """Setup test fixtures for each test method."""
        self.temp_dir = tempfile.mkdtemp()

        # Mock all UCKN components
        with (
            patch(
                "src.uckn.mcp.universal_knowledge_server.ChromaDBConnector"
            ) as mock_chroma,
            patch(
                "src.uckn.mcp.universal_knowledge_server.ProjectDNAFingerprinter"
            ) as mock_dna,
            patch(
                "src.uckn.mcp.universal_knowledge_server.MultiModalEmbeddings"
            ) as mock_embeddings,
            patch(
                "src.uckn.mcp.universal_knowledge_server.SemanticSearchEngine"
            ) as mock_search,
            patch(
                "src.uckn.mcp.universal_knowledge_server.PatternManager"
            ) as mock_pattern_mgr,
            patch(
                "src.uckn.mcp.universal_knowledge_server.TechStackCompatibilityMatrix"
            ) as mock_compat,
            patch(
                "src.uckn.mcp.universal_knowledge_server.PatternAnalytics"
            ) as mock_analytics,
            patch(
                "src.uckn.mcp.universal_knowledge_server.PatternRecommendationEngine"
            ) as mock_rec_engine,
            patch(
                "src.uckn.mcp.universal_knowledge_server.KnowledgeManager"
            ) as mock_km,
        ):
            # Configure mocks
            self.mock_chroma = mock_chroma.return_value
            self.mock_chroma.is_available.return_value = True

            self.mock_dna = mock_dna.return_value
            self.mock_embeddings = mock_embeddings.return_value
            self.mock_search = mock_search.return_value
            self.mock_search.is_available.return_value = True

            self.mock_pattern_mgr = mock_pattern_mgr.return_value
            self.mock_compat = mock_compat.return_value
            self.mock_compat.is_available.return_value = True

            self.mock_analytics = mock_analytics.return_value
            self.mock_rec_engine = mock_rec_engine.return_value
            self.mock_km = mock_km.return_value

            # Initialize server
            self.server = UniversalKnowledgeServer(project_root=self.temp_dir)

    def test_initialization(self):
        """Test UniversalKnowledgeServer initializes correctly."""
        assert self.server.project_root == self.temp_dir
        assert self.server.server is not None
        assert hasattr(self.server, "chroma_connector")
        assert hasattr(self.server, "dna_fingerprinter")
        assert hasattr(self.server, "recommendation_engine")

    def test_initialization_with_mocked_components(self):
        """Test that all components are properly mocked."""
        assert self.server.chroma_connector == self.mock_chroma
        assert self.server.dna_fingerprinter == self.mock_dna
        assert self.server.semantic_search == self.mock_search
        assert self.server.pattern_manager == self.mock_pattern_mgr
        assert self.server.recommendation_engine == self.mock_rec_engine

    @pytest.mark.asyncio
    async def test_search_patterns_success(self):
        """Test search_patterns tool with successful results."""
        # Mock search results
        mock_results = [
            {
                "id": "pattern_1",
                "document": "Test pattern content",
                "metadata": {"type": "setup"},
                "similarity_score": 0.9,
            }
        ]
        self.mock_search.search_by_text.return_value = mock_results

        result = await self.server._search_patterns(
            query="test query", project_path=self.temp_dir, limit=5
        )

        # Verify the result structure
        assert hasattr(result, "content")
        assert len(result.content) > 0

        # Parse the JSON response
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert response["query"] == "test query"
        assert response["total_found"] == 1
        assert len(response["results"]) == 1
        assert response["results"][0]["pattern_id"] == "pattern_1"

    @pytest.mark.asyncio
    async def test_search_patterns_fallback_to_pattern_manager(self):
        """Test search_patterns falls back to pattern manager when semantic search unavailable."""
        # Remove search_by_text method to trigger fallback
        delattr(self.mock_search, "search_by_text")

        mock_results = [
            {
                "id": "pattern_2",
                "document": "Fallback pattern",
                "metadata": {"type": "bugfix"},
                "similarity_score": 0.8,
            }
        ]
        self.mock_pattern_mgr.search_patterns.return_value = mock_results

        result = await self.server._search_patterns(query="fallback test")

        # Verify fallback was used
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)
        assert response["results"][0]["pattern_id"] == "pattern_2"

    @pytest.mark.asyncio
    async def test_recommend_setup_success(self):
        """Test recommend_setup tool with successful recommendations."""
        # Mock recommendation objects
        mock_rec = Mock()
        mock_rec.pattern_id = "setup_pattern_1"
        mock_rec.description = "Setup recommendation"
        mock_rec.confidence_score = 0.9
        mock_rec.compatibility_score = 0.8
        mock_rec.success_rate = 0.85

        self.mock_rec_engine.get_setup_recommendations.return_value = [mock_rec]

        result = await self.server._recommend_setup(project_path=self.temp_dir, limit=3)

        # Verify the result
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert response["project_path"] == self.temp_dir
        assert response["total_recommendations"] == 1
        assert response["recommendations"][0]["pattern_id"] == "setup_pattern_1"
        assert response["recommendations"][0]["confidence_score"] == 0.9

    @pytest.mark.asyncio
    async def test_recommend_setup_unavailable(self):
        """Test recommend_setup when recommendation engine is unavailable."""
        # Remove the method to simulate unavailability
        delattr(self.mock_rec_engine, "get_setup_recommendations")

        result = await self.server._recommend_setup(project_path=self.temp_dir)

        # Verify error response
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert "error" in response
        assert "not available" in response["error"]

    @pytest.mark.asyncio
    async def test_predict_issues_success(self):
        """Test predict_issues tool with successful predictions."""
        # Mock prediction objects
        mock_pred = Mock()
        mock_pred.description = "Potential security issue"
        mock_pred.pattern_id = "security_pattern_1"
        mock_pred.pattern_content = "Use HTTPS for all connections"
        mock_pred.confidence_score = 0.7

        self.mock_rec_engine.get_proactive_recommendations.return_value = [mock_pred]

        result = await self.server._predict_issues(project_path=self.temp_dir, limit=3)

        # Verify the result
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert response["project_path"] == self.temp_dir
        assert response["total_predictions"] == 1
        assert (
            response["potential_issues"][0]["issue_type"] == "Potential security issue"
        )
        assert response["potential_issues"][0]["confidence_score"] == 0.7

    @pytest.mark.asyncio
    async def test_validate_solution_success(self):
        """Test validate_solution tool with successful validation."""
        # Mock similar solutions
        mock_solutions = [
            {
                "id": "solution_1",
                "similarity_score": 0.85,
                "document": "Similar solution pattern with good practices",
            },
            {
                "id": "solution_2",
                "similarity_score": 0.75,
                "document": "Another similar approach",
            },
        ]
        self.mock_search.search_by_text.return_value = mock_solutions

        result = await self.server._validate_solution(
            solution_description="Use JWT for authentication",
            problem_context="Need secure user authentication",
            project_path=self.temp_dir,
        )

        # Verify the result
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert response["solution_description"] == "Use JWT for authentication"
        assert response["problem_context"] == "Need secure user authentication"
        assert response["validation_score"] == 0.85  # Max of similarity scores
        assert len(response["similar_patterns"]) == 2
        assert len(response["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_contribute_pattern_success(self):
        """Test contribute_pattern tool with successful contribution."""
        self.mock_pattern_mgr.add_pattern.return_value = "new_pattern_123"

        result = await self.server._contribute_pattern(
            pattern_title="New Setup Pattern",
            pattern_description="A new way to configure projects",
            pattern_type="setup",
            pattern_code="npm init -y",
            technologies=["Node.js", "npm"],
            project_path=self.temp_dir,
        )

        # Verify the result
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert response["status"] == "success"
        assert response["pattern_id"] == "new_pattern_123"
        assert "successfully" in response["message"]

    @pytest.mark.asyncio
    async def test_contribute_pattern_failure(self):
        """Test contribute_pattern tool with failure."""
        self.mock_pattern_mgr.add_pattern.return_value = None

        result = await self.server._contribute_pattern(
            pattern_title="Failed Pattern",
            pattern_description="This should fail",
            pattern_type="setup",
        )

        # Verify error response
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert response["status"] == "error"
        assert "Failed to add pattern" in response["message"]

    @pytest.mark.asyncio
    async def test_get_project_dna_success(self):
        """Test get_project_dna tool with successful analysis."""
        mock_fingerprint = {
            "languages": ["Python"],
            "frameworks": ["FastAPI"],
            "testing": ["pytest"],
            "vector": [0.1, 0.2, 0.3],
        }
        self.mock_dna.generate_fingerprint.return_value = mock_fingerprint

        result = await self.server._get_project_dna(project_path=self.temp_dir)

        # Verify the result
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert response["project_path"] == self.temp_dir
        assert response["dna_fingerprint"] == mock_fingerprint
        assert "analysis_timestamp" in response

    @pytest.mark.asyncio
    async def test_get_project_dna_unavailable(self):
        """Test get_project_dna when DNA fingerprinting is unavailable."""
        # Remove the method to simulate unavailability
        delattr(self.mock_dna, "generate_fingerprint")

        result = await self.server._get_project_dna(project_path=self.temp_dir)

        # Verify error response
        assert hasattr(result, "content")
        response_text = result.content[0].text
        response = json.loads(response_text)

        assert "error" in response
        assert "not available" in response["error"]

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test error handling in tool calls."""
        # Force an exception in the search
        self.mock_search.search_by_text.side_effect = Exception("Mock search error")

        result = await self.server._search_patterns(query="error test")

        # Verify error is handled gracefully
        assert hasattr(result, "content")
        response_text = result.content[0].text
        assert "Search failed" in response_text
        assert "Mock search error" in response_text

    def test_create_mock_components(self):
        """Test creation of mock components for graceful degradation."""
        # Create a new server instance that will fail component initialization
        with patch(
            "src.uckn.mcp.universal_knowledge_server.ChromaDBConnector",
            side_effect=Exception("Mock init error"),
        ):
            server = UniversalKnowledgeServer(project_root=self.temp_dir)

            # Verify mock components were created
            assert hasattr(server, "chroma_connector")
            assert hasattr(server, "dna_fingerprinter")
            assert server.chroma_connector.is_available() is False


def teardown_mcp_mocks():
    """Restore original modules"""
    import sys

    for name, module in sys_modules_backup.items():
        if module is not None:
            sys.modules[name] = module
        elif name in sys.modules:
            del sys.modules[name]


def teardown_module():
    """Clean up after all tests"""
    teardown_mcp_mocks()


if __name__ == "__main__":
    pytest.main([__file__])
