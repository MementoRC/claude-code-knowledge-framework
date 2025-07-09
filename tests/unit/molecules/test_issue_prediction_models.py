import random
from unittest.mock import Mock, patch

import pytest

from src.uckn.core.molecules.issue_prediction_models import IssuePredictionModels


@pytest.fixture
def issue_prediction_models():
    return IssuePredictionModels()


def test_is_available_returns_true(issue_prediction_models):
    assert issue_prediction_models.is_available() is True


def test_train_model_with_empty_data(issue_prediction_models):
    success = issue_prediction_models.train_model([])
    assert success is False
    assert issue_prediction_models._is_model_trained is False


def test_train_model_with_data_mock_success(issue_prediction_models):
    training_data = [{"features": [1, 2], "label": "issue_type_A"}]
    success = issue_prediction_models.train_model(training_data)
    assert success is True
    assert issue_prediction_models._is_model_trained is True


def test_feature_extract_returns_list_of_floats(issue_prediction_models):
    project_data = {
        "project_path": "/tmp/proj",
        "tech_stack": {"languages": ["Python"]},
    }
    features = issue_prediction_models.feature_extract(project_data)
    assert isinstance(features, list)
    assert all(isinstance(f, float) for f in features)
    assert len(features) == 128  # Based on mock implementation


def test_predict_returns_mock_prediction_if_not_trained(issue_prediction_models):
    issue_prediction_models._is_model_trained = False  # Ensure it's not trained
    project_data = {"project_path": "/tmp/proj"}
    predictions = issue_prediction_models.predict(project_data)
    assert len(predictions) == 1
    assert predictions[0]["type"] == "ml_general_risk"
    assert predictions[0]["confidence"] == 0.4


@patch(
    "random.random", side_effect=[0.3, 0.7, 0.5]
)  # First call triggers issue, second call for confidence, third as buffer
@patch("random.choice", return_value="ml_performance_issue")
def test_predict_returns_ml_issue_if_trained_and_random_allows(
    mock_choice, mock_random, issue_prediction_models
):
    issue_prediction_models._is_model_trained = True
    project_data = {"project_path": "/tmp/proj"}
    predictions = issue_prediction_models.predict(project_data)
    assert len(predictions) == 1
    assert predictions[0]["type"] == "ml_performance_issue"
    assert 0.6 <= predictions[0]["confidence"] <= 0.95


@patch("random.random", side_effect=[0.8, 0.5])  # High random value, no issue predicted, buffer
def test_predict_returns_no_issue_if_trained_and_random_disallows(
    mock_random, issue_prediction_models
):
    issue_prediction_models._is_model_trained = True
    project_data = {"project_path": "/tmp/proj"}
    predictions = issue_prediction_models.predict(project_data)
    assert len(predictions) == 0


def test_predict_handles_no_features(issue_prediction_models):
    issue_prediction_models._is_model_trained = True
    with patch.object(issue_prediction_models, "feature_extract", return_value=[]):
        project_data = {"project_path": "/tmp/proj"}
        predictions = issue_prediction_models.predict(project_data)
        assert len(predictions) == 0
