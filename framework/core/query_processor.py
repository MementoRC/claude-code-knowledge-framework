#!/usr/bin/env python3
"""
Query Processing for Enhanced Semantic Search

Provides query preprocessing, normalization, and expansion capabilities
for better semantic search results.
"""

import re
import logging
from typing import Dict, List, Any, Optional


class QueryProcessor:
    """
    Processes and enhances search queries for better semantic search results.
    Includes preprocessing, expansion, standardization, and domain-specific handling.
    """

    def __init__(self,
                 synonyms: Optional[Dict[str, List[str]]] = None,
                 error_patterns: Optional[Dict[str, str]] = None,
                 domain_vocabulary: Optional[Dict[str, str]] = None):
        self._logger = logging.getLogger(__name__)

        # Default synonyms for common development terms
        self.synonyms = synonyms or {
            "install": ["setup", "configure", "deploy"],
            "error": ["failure", "bug", "issue", "problem"],
            "fix": ["resolve", "debug", "patch", "solution"],
            "dependency": ["package", "library", "module"],
            "ci": ["continuous integration", "github actions", "jenkins"],
            "test": ["pytest", "unittest", "jest"],
            "python": ["py", "python3"],
            "javascript": ["js", "node", "nodejs"],
            "build": ["compile", "make", "package"],
            "deploy": ["release", "publish"],
            "config": ["configuration", "settings"],
            "import": ["require", "include"],
            "missing": ["not found", "undefined"],
            "permission": ["access denied", "forbidden"],
            "timeout": ["hang", "slow"],
            "memory": ["ram", "heap"],
            "network": ["connection", "connectivity"],
            "database": ["db", "sql", "postgres", "mysql"],
            "api": ["interface", "endpoint"],
            "auth": ["authentication", "login"],
            "docker": ["container"],
            "kubernetes": ["k8s"],
            "cloud": ["aws", "azure", "gcp"]
        }

        # Common error patterns for normalization
        self.error_patterns = error_patterns or {
            r"ModuleNotFoundError: No module named '([^']*)'": r"ModuleNotFoundError: \1",
            r"ImportError: cannot import name '([^']*)' from '([^']*)'": r"ImportError: \1 from \2",
            r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']*)'": r"FileNotFoundError: \1",
            r"PermissionError: \[Errno 13\] Permission denied: '([^']*)'": r"PermissionError: \1",
            r"ConnectionRefusedError: \[Errno 111\] Connection refused": r"ConnectionRefusedError",
            r"TimeoutError: .* timed out": r"TimeoutError",
            r"KeyError: '([^']*)'": r"KeyError: \1",
            r"AttributeError: .* has no attribute '([^']*)'": r"AttributeError: missing \1",
            r"TypeError: .* takes .* but .* given": r"TypeError: argument mismatch"
        }

        # Domain-specific vocabulary
        self.domain_vocabulary = domain_vocabulary or {
            "npm": "Node Package Manager",
            "pip": "Python Package Installer",
            "git": "Version Control System",
            "docker": "Containerization Platform",
            "k8s": "Kubernetes",
            "ci/cd": "Continuous Integration/Continuous Deployment",
            "orm": "Object-Relational Mapping",
            "rest": "Representational State Transfer",
            "graphql": "Graph Query Language",
            "jwt": "JSON Web Token",
            "ssl/tls": "Secure Socket Layer/Transport Layer Security"
        }

    def normalize_query(self, query: str) -> str:
        """
        Normalizes a query by cleaning and standardizing text.
        """
        # Convert to lowercase for consistent processing
        query = query.lower().strip()
        
        # Remove extra whitespace
        query = re.sub(r"\s+", " ", query)
        
        # Normalize error message patterns
        query = self._normalize_error_patterns(query)
        
        # Apply domain vocabulary standardization
        query = self._apply_domain_vocabulary(query)
        
        return query

    def expand_query(self, query: str) -> List[str]:
        """
        Expands a query with synonyms and related terms.
        """
        normalized = self.normalize_query(query)
        expansions = [normalized]
        
        # Add synonym expansions
        words = normalized.split()
        for word in words:
            if word in self.synonyms:
                for synonym in self.synonyms[word]:
                    # Create variations by replacing the original word
                    expanded = normalized.replace(word, synonym)
                    if expanded not in expansions:
                        expansions.append(expanded)
        
        return expansions[:10]  # Limit to prevent excessive expansions

    def extract_technical_terms(self, query: str) -> List[str]:
        """
        Extracts technical terms and identifiers from the query.
        """
        terms = []
        
        # Extract error class names
        error_classes = re.findall(r'\b\w*Error\b', query, re.IGNORECASE)
        terms.extend(error_classes)
        
        # Extract file extensions
        file_extensions = re.findall(r'\.\w+\b', query)
        terms.extend(file_extensions)
        
        # Extract package/module names
        package_names = re.findall(r'\b[a-z][a-z0-9_-]*[a-z0-9]\b', query.lower())
        terms.extend(package_names)
        
        return list(set(terms))  # Remove duplicates

    def create_search_filters(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates metadata filters based on query analysis and context.
        """
        filters = {}
        
        # Extract technology stack from query
        tech_stack = self._extract_technology_stack(query)
        if tech_stack:
            filters["technology_stack"] = {"$in": tech_stack}
        
        # Extract error categories
        error_category = self._extract_error_category(query)
        if error_category:
            filters["error_category"] = error_category
        
        # Add context-based filters
        if context:
            if context.get("repository"):
                filters["repository"] = context["repository"]
            if context.get("branch"):
                filters["branch"] = context["branch"]
            if context.get("time_range"):
                filters["created_at"] = {"$gte": context["time_range"]}
        
        return filters

    def _normalize_error_patterns(self, query: str) -> str:
        """Apply error pattern normalization."""
        for pattern, replacement in self.error_patterns.items():
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        return query

    def _apply_domain_vocabulary(self, query: str) -> str:
        """Apply domain-specific vocabulary expansion."""
        for term, expansion in self.domain_vocabulary.items():
            # Replace exact matches with expanded form
            pattern = r'\b' + re.escape(term) + r'\b'
            query = re.sub(pattern, expansion, query, flags=re.IGNORECASE)
        return query

    def _extract_technology_stack(self, query: str) -> List[str]:
        """Extract technology stack indicators from query."""
        tech_indicators = {
            "python": ["python", "py", "pip", "conda", "pytest", "django", "flask"],
            "javascript": ["javascript", "js", "node", "npm", "react", "vue", "angular"],
            "java": ["java", "maven", "gradle", "spring", "junit"],
            "go": ["golang", "go", "mod"],
            "rust": ["rust", "cargo"],
            "docker": ["docker", "dockerfile", "container"],
            "kubernetes": ["kubernetes", "k8s", "kubectl", "helm"],
            "git": ["git", "github", "gitlab", "bitbucket"],
            "ci": ["github actions", "jenkins", "gitlab ci", "circleci"]
        }
        
        detected = []
        query_lower = query.lower()
        
        for tech, indicators in tech_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                detected.append(tech)
        
        return detected

    def _extract_error_category(self, query: str) -> Optional[str]:
        """Extract error category from query."""
        error_categories = {
            "import_error": ["modulenotfounderror", "importerror", "no module named"],
            "file_error": ["filenotfounderror", "no such file", "file not found"],
            "permission_error": ["permissionerror", "permission denied", "access denied"],
            "network_error": ["connectionerror", "timeout", "connection refused"],
            "dependency_error": ["dependency", "package", "version conflict"],
            "syntax_error": ["syntaxerror", "invalid syntax"],
            "type_error": ["typeerror", "wrong type", "type mismatch"],
            "value_error": ["valueerror", "invalid value"],
            "key_error": ["keyerror", "missing key"],
            "attribute_error": ["attributeerror", "no attribute"]
        }
        
        query_lower = query.lower()
        for category, keywords in error_categories.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        
        return None