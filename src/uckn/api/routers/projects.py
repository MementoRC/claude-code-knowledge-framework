"""
Project intelligence endpoints for UCKN API.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...core.organisms.knowledge_manager import KnowledgeManager
from ..dependencies import get_knowledge_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class TechnologyStackDNA(BaseModel):
    """Technology stack DNA model."""

    languages: list[str]
    frameworks: list[str]
    build_systems: list[str]
    ci_platforms: list[str]
    deployment_targets: list[str]
    complexity_score: float
    fingerprint: str


class ProjectAnalysisRequest(BaseModel):
    """Request model for project analysis."""

    project_path: str = Field(..., description="Path to the project directory")


class ProjectAnalysisResponse(BaseModel):
    """Response model for project analysis."""

    dna: TechnologyStackDNA
    analysis_time_ms: int
    recommendations: list[str]


class SetupRecommendationRequest(BaseModel):
    """Request model for setup recommendations."""

    dna: TechnologyStackDNA


class SetupRecommendation(BaseModel):
    """Setup recommendation model."""

    category: str
    title: str
    description: str
    priority: str
    implementation_steps: list[str]
    estimated_time: str


class SetupRecommendationResponse(BaseModel):
    """Response model for setup recommendations."""

    recommendations: list[SetupRecommendation]
    total_count: int


class IssueWarning(BaseModel):
    """Issue warning model."""

    severity: str
    category: str
    title: str
    description: str
    likelihood: float
    mitigation_steps: list[str]


class IssuesPredictionRequest(BaseModel):
    """Request model for issues prediction."""

    dna: TechnologyStackDNA


class IssuesPredictionResponse(BaseModel):
    """Response model for issues prediction."""

    warnings: list[IssueWarning]
    total_count: int
    risk_score: float


@router.post("/projects/analyze", response_model=ProjectAnalysisResponse)
async def analyze_project(
    request: ProjectAnalysisRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
):
    """Analyze project technology stack and generate DNA fingerprint."""
    try:
        import time

        start_time = time.time()

        # Analyze project stack
        stack_analysis = knowledge_manager.analyze_project_stack(request.project_path)

        # Create DNA model
        dna = TechnologyStackDNA(
            languages=stack_analysis.get("languages", []),
            frameworks=stack_analysis.get("frameworks", []),
            build_systems=stack_analysis.get("build_systems", []),
            ci_platforms=stack_analysis.get("ci_platforms", []),
            deployment_targets=stack_analysis.get("deployment_targets", []),
            complexity_score=stack_analysis.get("complexity_score", 0.0),
            fingerprint=stack_analysis.get("fingerprint", ""),
        )

        analysis_time = int((time.time() - start_time) * 1000)

        # Generate basic recommendations
        recommendations = [
            f"Project uses {len(dna.languages)} programming languages",
            f"Detected {len(dna.frameworks)} frameworks",
            f"Complexity score: {dna.complexity_score:.2f}",
        ]

        return ProjectAnalysisResponse(
            dna=dna, analysis_time_ms=analysis_time, recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Error analyzing project: {e}")
        raise HTTPException(
            status_code=500, detail=f"Project analysis failed: {str(e)}"
        )


@router.post("/projects/recommend-setup", response_model=SetupRecommendationResponse)
async def recommend_setup(
    request: SetupRecommendationRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
):
    """Get setup recommendations based on technology stack DNA."""
    try:
        # Generate recommendations based on tech stack
        recommendations = []

        # CI/CD recommendations
        if not request.dna.ci_platforms:
            recommendations.append(
                SetupRecommendation(
                    category="CI/CD",
                    title="Set up Continuous Integration",
                    description="No CI platform detected. Consider setting up automated testing and deployment.",
                    priority="high",
                    implementation_steps=[
                        "Choose a CI platform (GitHub Actions, GitLab CI, etc.)",
                        "Create workflow configuration files",
                        "Set up automated testing",
                        "Configure deployment pipelines",
                    ],
                    estimated_time="2-4 hours",
                )
            )

        # Testing recommendations
        if "python" in [lang.lower() for lang in request.dna.languages]:
            recommendations.append(
                SetupRecommendation(
                    category="Testing",
                    title="Python Testing Setup",
                    description="Ensure comprehensive test coverage for Python projects.",
                    priority="medium",
                    implementation_steps=[
                        "Install pytest and testing dependencies",
                        "Create test directory structure",
                        "Set up test configuration",
                        "Add coverage reporting",
                    ],
                    estimated_time="1-2 hours",
                )
            )

        return SetupRecommendationResponse(
            recommendations=recommendations, total_count=len(recommendations)
        )

    except Exception as e:
        logger.error(f"Error generating setup recommendations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Setup recommendation failed: {str(e)}"
        )


@router.post("/projects/predict-issues", response_model=IssuesPredictionResponse)
async def predict_issues(
    request: IssuesPredictionRequest,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
):
    """Predict potential issues based on technology stack DNA."""
    try:
        warnings = []
        risk_score = 0.0

        # Check for high complexity
        if request.dna.complexity_score > 0.8:
            warnings.append(
                IssueWarning(
                    severity="high",
                    category="complexity",
                    title="High Project Complexity",
                    description="Project complexity score indicates potential maintenance challenges.",
                    likelihood=0.8,
                    mitigation_steps=[
                        "Review and refactor complex components",
                        "Improve documentation",
                        "Add comprehensive tests",
                        "Consider breaking into smaller modules",
                    ],
                )
            )
            risk_score += 0.3

        # Check for technology stack conflicts
        if len(request.dna.languages) > 3:
            warnings.append(
                IssueWarning(
                    severity="medium",
                    category="technology",
                    title="Multiple Programming Languages",
                    description="Using many programming languages can increase maintenance complexity.",
                    likelihood=0.6,
                    mitigation_steps=[
                        "Evaluate if all languages are necessary",
                        "Standardize on fewer technologies where possible",
                        "Ensure team expertise covers all languages",
                        "Document technology choices and rationale",
                    ],
                )
            )
            risk_score += 0.2

        # Check for missing CI/CD
        if not request.dna.ci_platforms:
            warnings.append(
                IssueWarning(
                    severity="medium",
                    category="deployment",
                    title="No CI/CD Platform Detected",
                    description="Missing automated testing and deployment increases risk of bugs in production.",
                    likelihood=0.7,
                    mitigation_steps=[
                        "Set up continuous integration",
                        "Add automated testing",
                        "Configure deployment pipelines",
                        "Add code quality checks",
                    ],
                )
            )
            risk_score += 0.2

        # Normalize risk score
        risk_score = min(risk_score, 1.0)

        return IssuesPredictionResponse(
            warnings=warnings, total_count=len(warnings), risk_score=risk_score
        )

    except Exception as e:
        logger.error(f"Error predicting issues: {e}")
        raise HTTPException(
            status_code=500, detail=f"Issue prediction failed: {str(e)}"
        )
