#!/usr/bin/env python3
"""
Tests for Flag Configuration Template
"""

from src.uckn.feature_flags.flag_configuration_template import (
    AtomicComponent,
    FlagConfigurationTemplate,
    TemplateLevel,
    create_example_template,
)


def test_flag_configuration_template():
    """Test basic flag configuration template functionality."""
    template = FlagConfigurationTemplate()

    # Add a component
    component = AtomicComponent(
        name="test_atom",
        level=TemplateLevel.ATOM,
        config={"test": True}
    )
    template.add_component(component)

    # Retrieve component
    retrieved = template.get_component("test_atom")
    assert retrieved is not None
    assert retrieved.name == "test_atom"
    assert retrieved.level == TemplateLevel.ATOM


def test_template_composition():
    """Test template composition from atomic components."""
    template = create_example_template()

    # Validate dependencies
    assert template.validate_dependencies() is True

    # Compose template
    composed = template.compose_template()

    # Verify structure
    assert "atoms" in composed
    assert "molecules" in composed
    assert "organisms" in composed
    assert "templates" in composed

    # Verify content
    assert len(composed["atoms"]) == 1
    assert len(composed["molecules"]) == 1
    assert len(composed["organisms"]) == 1
    assert len(composed["templates"]) == 1


def test_dependency_validation():
    """Test dependency validation."""
    template = FlagConfigurationTemplate()

    # Add component with missing dependency
    component = AtomicComponent(
        name="dependent",
        level=TemplateLevel.MOLECULE,
        config={},
        dependencies=["missing_component"]
    )
    template.add_component(component)

    # Should fail validation
    assert template.validate_dependencies() is False
