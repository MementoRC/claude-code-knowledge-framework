#!/usr/bin/env python3
"""
Claude Code Knowledge Management System (CCKMS)
Core implementation for capturing and retrieving CI troubleshooting knowledge
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
import re

from .semantic_search import SemanticSearchEngine

class ClaudeCodeKnowledgeManager:
    """
    Core knowledge management system for Claude Code CI troubleshooting
    """
    
    def __init__(self, knowledge_dir: str = ".claude/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.sessions_dir = self.knowledge_dir / "sessions"
        self.patterns_dir = self.knowledge_dir / "patterns"
        self.embeddings_dir = self.knowledge_dir / "embeddings"
        self.index_dir = self.knowledge_dir / "index"
        self.templates_dir = self.knowledge_dir / "templates"
        
        # Ensure directories exist
        for dir_path in [self.sessions_dir, self.patterns_dir, 
                        self.embeddings_dir, self.index_dir, self.templates_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize indexes
        self._initialize_indexes()
        
        # Initialize semantic search engine
        self.semantic_search = SemanticSearchEngine(knowledge_dir)
    
    def _initialize_indexes(self):
        """Initialize search indexes if they don't exist"""
        keyword_index_path = self.index_dir / "keyword_index.json"
        metadata_index_path = self.index_dir / "metadata_index.json"
        
        if not keyword_index_path.exists():
            self._save_json(keyword_index_path, {})
        
        if not metadata_index_path.exists():
            self._save_json(metadata_index_path, {
                "sessions": {},
                "patterns": {},
                "last_updated": datetime.now().isoformat()
            })
    
    def capture_session_knowledge(self, 
                                session_data: Dict[str, Any], 
                                lessons_learned: List[str],
                                solution_patterns: List[Dict[str, Any]],
                                manual_insights: Optional[List[str]] = None) -> str:
        """
        Capture knowledge from a completed CI troubleshooting session
        
        Args:
            session_data: TaskMaster session data
            lessons_learned: List of lessons learned during the session
            solution_patterns: Identified solution patterns
            manual_insights: Additional manual insights
            
        Returns:
            Session ID for future reference
        """
        session_id = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create comprehensive session record
        session_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "context": self._extract_context(session_data),
            "attempts": self._extract_attempts(session_data),
            "final_status": session_data.get("final_status", "unknown"),
            "total_duration_minutes": session_data.get("duration_minutes", 0),
            "lessons_learned": lessons_learned,
            "solution_patterns": solution_patterns,
            "manual_insights": manual_insights or [],
            "quality_gates": session_data.get("quality_gates", {}),
            "tools_used": session_data.get("tools_used", []),
            "environment": {
                "repository": session_data.get("repository", ""),
                "branch": session_data.get("branch", ""),
                "python_version": session_data.get("python_version", ""),
                "ci_platform": session_data.get("ci_platform", "github_actions")
            },
            "metadata": {
                "knowledge_version": "1.0",
                "captured_by": "claude_code_ai",
                "session_complexity": self._assess_complexity(session_data),
                "success_confidence": self._assess_success_confidence(session_data)
            }
        }
        
        # Save session record
        session_file = self.sessions_dir / f"{session_id}_session.json"
        self._save_json(session_file, session_record)
        
        # Update patterns database
        self._update_patterns_database(solution_patterns, session_id)
        
        # Update search indexes
        self._update_keyword_index(session_record)
        self._update_metadata_index(session_record)
        
        # Generate embeddings for semantic search
        self._generate_session_embeddings(session_record)
        
        return session_id
    
    def search_knowledge(self, 
                        query: str,
                        context: Optional[Dict[str, Any]] = None,
                        max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant past solutions
        
        Args:
            query: Search query (failure description, error message, etc.)
            context: Current context (branch, repository, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant session records with similarity scores
        """
        # 1. Keyword search
        keyword_results = self._keyword_search(query)
        
        # 2. Pattern matching
        pattern_results = self._pattern_search(query, context)
        
        # 3. Semantic search (simplified - would use embeddings in full implementation)
        semantic_results = self._semantic_search(query)
        
        # 4. Combine and rank results
        all_results = keyword_results + pattern_results + semantic_results
        
        # 5. Remove duplicates and rank by relevance
        unique_results = self._deduplicate_results(all_results)
        ranked_results = self._rank_results(unique_results, query, context)
        
        return ranked_results[:max_results]
    
    def get_session_context_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get a summary of recent sessions for context restoration
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Summary of recent sessions and patterns
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        recent_sessions = []
        for session_file in self.sessions_dir.glob("*_session.json"):
            session_data = self._load_json(session_file)
            session_date = datetime.fromisoformat(session_data["timestamp"])
            
            if session_date >= cutoff_date:
                recent_sessions.append({
                    "session_id": session_data["session_id"],
                    "timestamp": session_data["timestamp"],
                    "final_status": session_data["final_status"],
                    "repository": session_data["context"].get("repository", ""),
                    "key_lessons": session_data["lessons_learned"][:3],  # Top 3 lessons
                    "success_confidence": session_data["metadata"]["success_confidence"]
                })
        
        # Sort by timestamp (most recent first)
        recent_sessions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Get most common patterns
        common_patterns = self._get_common_patterns(days_back)
        
        return {
            "recent_sessions": recent_sessions,
            "common_patterns": common_patterns,
            "total_sessions": len(recent_sessions),
            "success_rate": self._calculate_success_rate(recent_sessions),
            "generated_at": datetime.now().isoformat()
        }
    
    def suggest_solutions(self, 
                         current_failures: List[str],
                         context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest solutions based on historical knowledge
        
        Args:
            current_failures: List of current test failures
            context: Current context (repository, branch, etc.)
            
        Returns:
            List of suggested solutions with confidence scores
        """
        suggestions = []
        
        for failure in current_failures:
            # Search for similar past failures
            search_results = self.search_knowledge(failure, context, max_results=3)
            
            for result in search_results:
                # Extract solution from successful session
                if result["session_data"]["final_status"] == "success":
                    solution = self._extract_solution_from_session(result["session_data"])
                    suggestions.append({
                        "failure": failure,
                        "solution": solution,
                        "confidence": result["similarity_score"],
                        "source_session": result["session_data"]["session_id"],
                        "historical_success": True
                    })
        
        # Sort by confidence score
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return suggestions
    
    def _extract_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from session data"""
        return {
            "repository": session_data.get("repository", ""),
            "branch": session_data.get("branch", ""),
            "pr_number": session_data.get("pr_number"),
            "ci_status": session_data.get("initial_ci_status", ""),
            "initial_failures": session_data.get("initial_failures", []),
            "environment_type": "ci"
        }
    
    def _extract_attempts(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attempt information from session data"""
        attempts = []
        
        # Extract from TaskMaster tasks if available
        tasks = session_data.get("tasks", [])
        for i, task in enumerate(tasks):
            attempt = {
                "attempt_number": i + 1,
                "approach": task.get("approach", "unknown"),
                "actions_taken": task.get("actions", []),
                "files_modified": task.get("files_modified", []),
                "outcome": task.get("status", "unknown"),
                "duration_minutes": task.get("duration_minutes", 0)
            }
            attempts.append(attempt)
        
        return attempts
    
    def _assess_complexity(self, session_data: Dict[str, Any]) -> str:
        """Assess the complexity of the troubleshooting session"""
        factors = {
            "num_attempts": len(session_data.get("tasks", [])),
            "num_files_modified": len(set().union(*[
                task.get("files_modified", []) 
                for task in session_data.get("tasks", [])
            ])),
            "duration_minutes": session_data.get("duration_minutes", 0),
            "num_failures": len(session_data.get("initial_failures", []))
        }
        
        complexity_score = (
            min(factors["num_attempts"] * 2, 10) +
            min(factors["num_files_modified"], 10) +
            min(factors["duration_minutes"] / 10, 10) +
            min(factors["num_failures"], 10)
        )
        
        if complexity_score < 10:
            return "low"
        elif complexity_score < 25:
            return "medium"
        else:
            return "high"
    
    def _assess_success_confidence(self, session_data: Dict[str, Any]) -> float:
        """Assess confidence in the success of the resolution"""
        final_status = session_data.get("final_status", "unknown")
        quality_gates = session_data.get("quality_gates", {})
        
        if final_status == "success":
            base_confidence = 0.8
        elif final_status == "partial_success":
            base_confidence = 0.6
        else:
            base_confidence = 0.3
        
        # Adjust based on quality gates
        quality_bonus = sum([
            0.05 for gate in quality_gates.values() 
            if gate is True
        ])
        
        return min(base_confidence + quality_bonus, 1.0)
    
    def _keyword_search(self, query: str) -> List[Dict[str, Any]]:
        """Simple keyword-based search"""
        keyword_index = self._load_json(self.index_dir / "keyword_index.json")
        
        query_words = set(re.findall(r'\w+', query.lower()))
        results = []
        
        for session_id, keywords in keyword_index.items():
            matching_keywords = query_words.intersection(set(keywords))
            if matching_keywords:
                score = len(matching_keywords) / len(query_words)
                session_data = self._load_session(session_id)
                if session_data:
                    results.append({
                        "session_data": session_data,
                        "similarity_score": score,
                        "search_type": "keyword"
                    })
        
        return results
    
    def _pattern_search(self, query: str, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search based on known patterns"""
        patterns_file = self.patterns_dir / "solution_patterns.json"
        if not patterns_file.exists():
            return []
        
        patterns = self._load_json(patterns_file)
        results = []
        
        for pattern_id, pattern_data in patterns.items():
            # Check if query matches pattern description
            if query.lower() in pattern_data.get("description", "").lower():
                # Find sessions that used this pattern
                for session_id in pattern_data.get("sessions", []):
                    session_data = self._load_session(session_id)
                    if session_data:
                        results.append({
                            "session_data": session_data,
                            "similarity_score": 0.7,  # Fixed score for pattern matches
                            "search_type": "pattern",
                            "pattern_id": pattern_id
                        })
        
        return results
    
    def _semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        try:
            # Use semantic search engine
            results = self.semantic_search.search_similar_sessions(
                query=query,
                max_results=5,
                similarity_threshold=0.6
            )
            
            # Convert to expected format
            formatted_results = []
            for result in results:
                session_id = result["session_id"]
                session_data = self._load_session(session_id)
                
                if session_data:
                    formatted_results.append({
                        "session_data": session_data,
                        "similarity_score": result["similarity_score"],
                        "search_type": "semantic",
                        "metadata": result.get("metadata", {})
                    })
                    
            return formatted_results
            
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sessions from results"""
        seen_sessions = set()
        unique_results = []
        
        for result in results:
            session_id = result["session_data"]["session_id"]
            if session_id not in seen_sessions:
                seen_sessions.add(session_id)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, results: List[Dict[str, Any]], 
                     query: str, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank results by relevance"""
        for result in results:
            base_score = result["similarity_score"]
            
            # Boost recent sessions
            session_date = datetime.fromisoformat(result["session_data"]["timestamp"])
            days_old = (datetime.now() - session_date).days
            recency_boost = max(0, 1 - days_old / 30)  # Decay over 30 days
            
            # Boost successful sessions
            success_boost = 0.2 if result["session_data"]["final_status"] == "success" else 0
            
            # Boost sessions with similar context
            context_boost = 0
            if context:
                session_context = result["session_data"]["context"]
                if context.get("repository") == session_context.get("repository"):
                    context_boost += 0.1
                if context.get("branch") == session_context.get("branch"):
                    context_boost += 0.05
            
            final_score = base_score + recency_boost * 0.2 + success_boost + context_boost
            result["final_score"] = final_score
        
        # Sort by final score
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results
    
    def _update_patterns_database(self, solution_patterns: List[Dict[str, Any]], session_id: str):
        """Update the patterns database with new patterns"""
        patterns_file = self.patterns_dir / "solution_patterns.json"
        
        if patterns_file.exists():
            patterns = self._load_json(patterns_file)
        else:
            patterns = {}
        
        for pattern in solution_patterns:
            pattern_id = pattern.get("pattern_id", hashlib.md5(
                pattern.get("description", "").encode()
            ).hexdigest()[:8])
            
            if pattern_id not in patterns:
                patterns[pattern_id] = {
                    "description": pattern.get("description", ""),
                    "solution_template": pattern.get("solution_template", ""),
                    "sessions": [],
                    "success_count": 0,
                    "total_count": 0
                }
            
            patterns[pattern_id]["sessions"].append(session_id)
            patterns[pattern_id]["total_count"] += 1
        
        self._save_json(patterns_file, patterns)
    
    def _update_keyword_index(self, session_record: Dict[str, Any]):
        """Update keyword index for fast searching"""
        keyword_index_path = self.index_dir / "keyword_index.json"
        keyword_index = self._load_json(keyword_index_path)
        
        # Extract keywords from session
        keywords = set()
        
        # From lessons learned
        for lesson in session_record.get("lessons_learned", []):
            keywords.update(re.findall(r'\w+', lesson.lower()))
        
        # From failure descriptions
        for attempt in session_record.get("attempts", []):
            for action in attempt.get("actions_taken", []):
                keywords.update(re.findall(r'\w+', action.lower()))
        
        # From context
        context = session_record.get("context", {})
        for value in context.values():
            if isinstance(value, str):
                keywords.update(re.findall(r'\w+', value.lower()))
        
        keyword_index[session_record["session_id"]] = list(keywords)
        self._save_json(keyword_index_path, keyword_index)
    
    def _update_metadata_index(self, session_record: Dict[str, Any]):
        """Update metadata index for filtering and analysis"""
        metadata_index_path = self.index_dir / "metadata_index.json"
        metadata_index = self._load_json(metadata_index_path)
        
        session_id = session_record["session_id"]
        metadata_index["sessions"][session_id] = {
            "timestamp": session_record["timestamp"],
            "final_status": session_record["final_status"],
            "repository": session_record["context"].get("repository", ""),
            "branch": session_record["context"].get("branch", ""),
            "complexity": session_record["metadata"]["session_complexity"],
            "success_confidence": session_record["metadata"]["success_confidence"]
        }
        
        metadata_index["last_updated"] = datetime.now().isoformat()
        self._save_json(metadata_index_path, metadata_index)
    
    def _generate_session_embeddings(self, session_record: Dict[str, Any]):
        """Generate embeddings for semantic search"""
        try:
            session_id = session_record["session_id"]
            success = self.semantic_search.store_session_embedding(session_id, session_record)
            
            if success:
                print(f"Generated embeddings for session {session_id}")
            else:
                print(f"Failed to generate embeddings for session {session_id}")
                
        except Exception as e:
            print(f"Error generating session embeddings: {e}")
    
    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session record by ID"""
        session_file = self.sessions_dir / f"{session_id}_session.json"
        if session_file.exists():
            return self._load_json(session_file)
        return None
    
    def _get_common_patterns(self, days_back: int) -> List[Dict[str, Any]]:
        """Get most common patterns from recent sessions"""
        patterns_file = self.patterns_dir / "solution_patterns.json"
        if not patterns_file.exists():
            return []
        
        patterns = self._load_json(patterns_file)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        pattern_counts = {}
        for pattern_id, pattern_data in patterns.items():
            recent_count = 0
            for session_id in pattern_data.get("sessions", []):
                session_data = self._load_session(session_id)
                if session_data:
                    session_date = datetime.fromisoformat(session_data["timestamp"])
                    if session_date >= cutoff_date:
                        recent_count += 1
            
            if recent_count > 0:
                pattern_counts[pattern_id] = {
                    "pattern_id": pattern_id,
                    "description": pattern_data.get("description", ""),
                    "recent_count": recent_count,
                    "total_count": pattern_data.get("total_count", 0)
                }
        
        # Sort by recent count
        return sorted(pattern_counts.values(), 
                     key=lambda x: x["recent_count"], reverse=True)[:5]
    
    def _calculate_success_rate(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate success rate for recent sessions"""
        if not sessions:
            return 0.0
        
        successful = sum(1 for s in sessions if s["final_status"] == "success")
        return successful / len(sessions)
    
    def _extract_solution_from_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract solution approach from a successful session"""
        attempts = session_data.get("attempts", [])
        if not attempts:
            return {}
        
        # Find the successful attempt (usually the last one)
        successful_attempt = attempts[-1] if attempts else {}
        
        return {
            "approach": successful_attempt.get("approach", ""),
            "actions_taken": successful_attempt.get("actions_taken", []),
            "files_modified": successful_attempt.get("files_modified", []),
            "key_lessons": session_data.get("lessons_learned", [])[:3]
        }
    
    def _save_json(self, file_path: Path, data: Any):
        """Save data as JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_json(self, file_path: Path) -> Any:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


# Command-line interface for Claude Code integration
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: knowledge_manager.py <command> [args...]")
        return
    
    km = ClaudeCodeKnowledgeManager()
    command = sys.argv[1]
    
    if command == "search":
        if len(sys.argv) < 3:
            print("Usage: knowledge_manager.py search <query>")
            return
        
        query = " ".join(sys.argv[2:])
        results = km.search_knowledge(query)
        
        print(f"Found {len(results)} results for: {query}")
        for i, result in enumerate(results, 1):
            session = result["session_data"]
            print(f"\n{i}. Session: {session['session_id']}")
            print(f"   Date: {session['timestamp']}")
            print(f"   Status: {session['final_status']}")
            print(f"   Similarity: {result['similarity_score']:.2f}")
            print(f"   Repository: {session['context'].get('repository', 'N/A')}")
    
    elif command == "summary":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        summary = km.get_session_context_summary(days)
        
        print(f"Knowledge Base Summary (last {days} days)")
        print(f"Total sessions: {summary['total_sessions']}")
        print(f"Success rate: {summary['success_rate']:.1%}")
        print("\nRecent sessions:")
        for session in summary['recent_sessions'][:5]:
            print(f"  - {session['session_id']}: {session['final_status']}")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()