/**
 * TypeScript interfaces for pattern data and API responses
 */

export interface TechStackFilter {
  technologies?: string[];
  project_type?: string;
  complexity?: string;
}

export interface PatternSearchRequest {
  query: string;
  filters?: TechStackFilter;
  limit?: number;
  min_similarity?: number;
}

export interface Pattern {
  id: string;
  document: string;
  metadata: {
    title?: string;
    description?: string;
    pattern_type?: string;
    technologies?: string[];
    code?: string;
    contributed_at?: string;
    validated?: boolean;
    validation_feedback?: string;
    validation_score?: number;
    [key: string]: any;
  };
  similarity_score?: number;
}

export interface PatternSearchResponse {
  patterns: Pattern[];
  total_count: number;
  query_time_ms: number;
}

export interface PatternSubmission {
  document: string;
  metadata: {
    title: string;
    description: string;
    pattern_type: string;
    technologies: string[];
    code?: string;
    [key: string]: any;
  };
  project_id?: string;
}

export interface PatternContributionResponse {
  pattern_id: string;
  status: string;
  message: string;
}

export interface ValidationResult {
  success: boolean;
  feedback?: string;
  score?: number;
}

export interface ValidationResponse {
  pattern_id: string;
  validation_status: string;
  message: string;
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  members: TeamMember[];
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  user_id: string;
  username: string;
  email: string;
  role: 'admin' | 'member' | 'viewer';
  joined_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  teams: string[];
  created_at: string;
  last_login?: string;
}

export interface AnalyticsData {
  total_patterns: number;
  total_searches: number;
  top_technologies: { name: string; count: number }[];
  recent_activity: ActivityItem[];
  pattern_trends: { date: string; count: number }[];
}

export interface ActivityItem {
  id: string;
  type: 'pattern_added' | 'pattern_validated' | 'search_performed';
  description: string;
  timestamp: string;
  user_id: string;
  username: string;
}
