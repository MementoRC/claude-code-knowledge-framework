#!/usr/bin/env python3
"""
Flag Configuration Template

Template for atomic design in the codebase, demonstrating the pattern for
feature flag configurations using atomic design principles.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TemplateLevel(Enum):
    """Atomic design template levels."""

    ATOM = "atom"
    MOLECULE = "molecule"
    ORGANISM = "organism"
    TEMPLATE = "template"


@dataclass
class AtomicComponent:
    """Basic atomic component for templates."""

    name: str
    level: TemplateLevel
    config: dict[str, Any]
    dependencies: list[str] | None = None


class FlagConfigurationTemplate:
    """
    Template demonstrating atomic design pattern for feature flag configuration.

    This serves as a template for applying atomic design patterns to other
    knowledge management components in the framework.
    """

    def __init__(self) -> None:
        self._components: dict[str, AtomicComponent] = {}

    def add_component(self, component: AtomicComponent) -> None:
        """Add an atomic component to the template."""
        self._components[component.name] = component

    def get_component(self, name: str) -> AtomicComponent | None:
        """Get a component by name."""
        return self._components.get(name)

    def compose_template(self) -> dict[str, Any]:
        """Compose complete template from atomic components."""
        template: dict[str, list[dict[str, Any]]] = {
            "atoms": [],
            "molecules": [],
            "organisms": [],
            "templates": [],
        }

        for component in self._components.values():
            level_key = f"{component.level.value}s"
            template[level_key].append(
                {
                    "name": component.name,
                    "config": component.config,
                    "dependencies": component.dependencies or [],
                }
            )

        return template

    def validate_dependencies(self) -> bool:
        """Validate that all component dependencies exist."""
        all_names = set(self._components.keys())

        for component in self._components.values():
            if component.dependencies:
                for dep in component.dependencies:
                    if dep not in all_names:
                        return False
        return True


# Example atomic design template usage
def create_example_template() -> FlagConfigurationTemplate:
    """Create example template showing atomic design pattern."""
    template = FlagConfigurationTemplate()

    # Atom level
    template.add_component(
        AtomicComponent(
            name="flag_value",
            level=TemplateLevel.ATOM,
            config={"type": "boolean", "default": False},
        )
    )

    # Molecule level
    template.add_component(
        AtomicComponent(
            name="feature_flag",
            level=TemplateLevel.MOLECULE,
            config={"validation": True, "environment_aware": True},
            dependencies=["flag_value"],
        )
    )

    # Organism level
    template.add_component(
        AtomicComponent(
            name="flag_registry",
            level=TemplateLevel.ORGANISM,
            config={"storage": "memory", "persistence": True},
            dependencies=["feature_flag"],
        )
    )

    # Template level
    template.add_component(
        AtomicComponent(
            name="progressive_rollout",
            level=TemplateLevel.TEMPLATE,
            config={"stages": ["canary", "gradual", "full"]},
            dependencies=["flag_registry"],
        )
    )

    return template
