"""
UCKN Query Parser Atom

Parses complex search queries, supporting boolean operators (AND, OR, NOT),
basic stemming, and synonym expansion.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from collections import deque

try:
    from nltk.stem import PorterStemmer
    from nltk.tokenize import word_tokenize
    import nltk
    # Download necessary NLTK data if not already present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    PorterStemmer = None
    word_tokenize = None
    NLTK_AVAILABLE = False

class QueryParser:
    """
    Parses a natural language query string into a structured format,
    applying boolean logic, stemming, and synonym expansion.
    """

    def __init__(self, synonym_map: Optional[Dict[str, List[str]]] = None):
        self._logger = logging.getLogger(__name__)
        self.stemmer = PorterStemmer() if NLTK_AVAILABLE else None
        self.synonym_map = synonym_map or self._default_synonym_map()

    def _default_synonym_map(self) -> Dict[str, List[str]]:
        """Provides a default, simple synonym map."""
        return {
            "python": ["py", "pythonic"],
            "javascript": ["js", "node", "nodejs"],
            "java": ["jvm"],
            "database": ["db", "sql", "nosql"],
            "error": ["bug", "issue", "problem", "exception"],
            "solution": ["fix", "workaround", "resolve"],
            "performance": ["speed", "optimize", "efficiency"],
            "security": ["vulnerability", "exploit", "secure"],
            "deployment": ["deploy", "ci/cd", "devops"],
            "testing": ["test", "qa", "unit test", "integration test"]
        }

    def _stem_word(self, word: str) -> str:
        """Applies stemming to a single word."""
        if self.stemmer:
            return self.stemmer.stem(word.lower())
        return word.lower()

    def _expand_synonyms(self, word: str) -> List[str]:
        """Expands a word to include its synonyms and its stemmed form."""
        word_lower = word.lower()
        expanded_words = {word_lower}
        if self.stemmer:
            expanded_words.add(self.stemmer.stem(word_lower))
        
        # Check for exact match or stemmed match in synonym map
        for key, synonyms in self.synonym_map.items():
            if word_lower == key or (self.stemmer and self.stemmer.stem(word_lower) == self.stemmer.stem(key)):
                expanded_words.update(synonyms)
                if self.stemmer:
                    expanded_words.update(self.stemmer.stem(s) for s in synonyms)
            elif word_lower in synonyms: # If the word itself is a synonym
                expanded_words.add(key)
                if self.stemmer:
                    expanded_words.add(self.stemmer.stem(key))
        
        return list(expanded_words)

    def parse_query(self, query_string: str) -> Dict[str, Any]:
        """
        Parses a query string with boolean operators (AND, OR, NOT).
        Example: "python AND (flask OR django) NOT deprecated"
        Returns a structured query dictionary.
        """
        if not query_string:
            return {"operator": "AND", "clauses": []}

        # Normalize operators to uppercase for consistent parsing
        query_string = query_string.replace(" AND ", " AND ").replace(" OR ", " OR ").replace(" NOT ", " NOT ")
        
        # Regex to split by operators, keeping them
        tokens = re.split(r'( AND | OR | NOT )', query_string)
        tokens = [t.strip() for t in tokens if t.strip()]

        # Handle implicit ANDs and parentheses
        processed_tokens = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '(':
                # Find matching parenthesis
                paren_level = 1
                sub_tokens = []
                j = i + 1
                while j < len(tokens) and paren_level > 0:
                    if tokens[j] == '(':
                        paren_level += 1
                    elif tokens[j] == ')':
                        paren_level -= 1
                    if paren_level > 0:
                        sub_tokens.append(tokens[j])
                    j += 1
                if paren_level != 0:
                    self._logger.warning(f"Mismatched parentheses in query: {query_string}")
                    # Treat as a single term if parentheses are mismatched
                    processed_tokens.append(token + " ".join(sub_tokens))
                    i = j
                else:
                    processed_tokens.append(self.parse_query(" ".join(sub_tokens))) # Recursively parse sub-query
                    i = j
            elif token in ["AND", "OR", "NOT"]:
                processed_tokens.append(token)
                i += 1
            else:
                # Regular term, expand synonyms and stem
                expanded_terms = self._expand_synonyms(token)
                if len(expanded_terms) > 1:
                    # If multiple synonyms, treat as an OR clause
                    processed_tokens.append({"operator": "OR", "clauses": [{"type": "term", "value": t} for t in expanded_terms]})
                else:
                    processed_tokens.append({"type": "term", "value": expanded_terms[0]})
                i += 1
            
            # Insert implicit ANDs
            if i < len(tokens) and \
               isinstance(processed_tokens[-1], (dict, str)) and \
               tokens[i] not in ["AND", "OR", "NOT", ")"] and \
               not (isinstance(tokens[i], dict) and tokens[i].get("operator")): # If next token is not an operator or a parsed sub-query
                if isinstance(tokens[i], str) and tokens[i] == '(': # Handle ( after a term
                    pass # Handled by the ( logic above
                else:
                    processed_tokens.append("AND")

        # Build the AST (Abstract Syntax Tree)
        # First, handle NOT (highest precedence)
        # Then AND
        # Then OR

        # Convert to a deque for easier manipulation
        q = deque(processed_tokens)
        
        # Pass 1: Handle NOT
        temp_q = deque()
        while q:
            item = q.popleft()
            if item == "NOT":
                if not q:
                    self._logger.warning("NOT operator without a term in query.")
                    continue
                operand = q.popleft()
                temp_q.append({"operator": "NOT", "clause": operand})
            else:
                temp_q.append(item)
        q = temp_q

        # Pass 2: Handle AND
        temp_q = deque()
        while q:
            item = q.popleft()
            if item == "AND":
                if not temp_q:
                    self._logger.warning("AND operator without left operand in query.")
                    continue
                left = temp_q.pop()
                if not q:
                    self._logger.warning("AND operator without right operand in query.")
                    temp_q.append(left) # Put left back
                    continue
                right = q.popleft()
                temp_q.append({"operator": "AND", "clauses": [left, right]})
            else:
                temp_q.append(item)
        q = temp_q

        # Pass 3: Handle OR
        temp_q = deque()
        while q:
            item = q.popleft()
            if item == "OR":
                if not temp_q:
                    self._logger.warning("OR operator without left operand in query.")
                    continue
                left = temp_q.pop()
                if not q:
                    self._logger.warning("OR operator without right operand in query.")
                    temp_q.append(left) # Put left back
                    continue
                right = q.popleft()
                temp_q.append({"operator": "OR", "clauses": [left, right]})
            else:
                temp_q.append(item)
        
        if not temp_q:
            return {"operator": "AND", "clauses": []} # Empty query or only operators

        # If there's only one item left, it's the root of the AST
        if len(temp_q) == 1:
            return temp_q[0]
        else:
            # If multiple items remain, it implies implicit ANDs at the top level
            # This can happen if the initial parsing didn't insert enough ANDs or if the query is malformed
            # For safety, wrap remaining top-level items in an implicit AND
            self._logger.warning(f"Multiple top-level clauses after parsing, implicitly combining with AND: {temp_q}")
            return {"operator": "AND", "clauses": list(temp_q)}

    def extract_terms(self, query_dict: Dict[str, Any]) -> List[str]:
        """Extract all terms from a parsed query for use in vector search."""
        terms = []
        
        def _extract_recursive(clause):
            if isinstance(clause, dict):
                if clause.get("type") == "term":
                    terms.append(clause.get("value", ""))
                elif clause.get("operator") in ["AND", "OR"]:
                    for sub_clause in clause.get("clauses", []):
                        _extract_recursive(sub_clause)
                elif clause.get("operator") == "NOT":
                    _extract_recursive(clause.get("clause", {}))
        
        _extract_recursive(query_dict)
        return list(set(terms))  # Remove duplicates

