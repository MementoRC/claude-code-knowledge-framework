/**
 * API service for communicating with the UCKN FastAPI backend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  PatternSearchRequest,
  PatternSearchResponse,
  PatternSubmission,
  PatternContributionResponse,
  ValidationResult,
  ValidationResponse,
  Pattern,
  Team,
  User,
  AnalyticsData,
} from '../types/patterns';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth tokens (when implemented)
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Pattern Management
  async searchPatterns(request: PatternSearchRequest): Promise<PatternSearchResponse> {
    const response: AxiosResponse<PatternSearchResponse> = await this.api.post(
      '/patterns/search',
      request
    );
    return response.data;
  }

  async contributePattern(pattern: PatternSubmission): Promise<PatternContributionResponse> {
    const response: AxiosResponse<PatternContributionResponse> = await this.api.post(
      '/patterns/contribute',
      pattern
    );
    return response.data;
  }

  async validatePattern(
    patternId: string,
    validation: ValidationResult
  ): Promise<ValidationResponse> {
    const response: AxiosResponse<ValidationResponse> = await this.api.put(
      `/patterns/${patternId}/validate`,
      validation
    );
    return response.data;
  }

  async getPattern(patternId: string): Promise<Pattern> {
    const response: AxiosResponse<Pattern> = await this.api.get(`/patterns/${patternId}`);
    return response.data;
  }

  // Team Management
  async getTeams(): Promise<Team[]> {
    const response: AxiosResponse<{ teams: Team[] }> = await this.api.get('/teams');
    return response.data.teams;
  }

  async createTeam(team: Partial<Team>): Promise<Team> {
    const response: AxiosResponse<Team> = await this.api.post('/teams', team);
    return response.data;
  }

  async updateTeam(teamId: string, updates: Partial<Team>): Promise<Team> {
    const response: AxiosResponse<Team> = await this.api.put(`/teams/${teamId}`, updates);
    return response.data;
  }

  async deleteTeam(teamId: string): Promise<void> {
    await this.api.delete(`/teams/${teamId}`);
  }

  async addTeamMember(teamId: string, userId: string, role: string): Promise<void> {
    await this.api.post(`/teams/${teamId}/members`, { user_id: userId, role });
  }

  async removeTeamMember(teamId: string, userId: string): Promise<void> {
    await this.api.delete(`/teams/${teamId}/members/${userId}`);
  }

  // User Management
  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<User> = await this.api.get('/auth/me');
    return response.data;
  }

  async updateUserProfile(updates: Partial<User>): Promise<User> {
    const response: AxiosResponse<User> = await this.api.put('/auth/profile', updates);
    return response.data;
  }

  async searchUsers(query: string): Promise<User[]> {
    const response: AxiosResponse<{ users: User[] }> = await this.api.get(
      `/auth/users/search?q=${encodeURIComponent(query)}`
    );
    return response.data.users;
  }

  // Analytics
  async getAnalytics(): Promise<AnalyticsData> {
    const response: AxiosResponse<AnalyticsData> = await this.api.get('/analytics/dashboard');
    return response.data;
  }

  async getPatternAnalytics(patternId: string): Promise<any> {
    const response: AxiosResponse<any> = await this.api.get(`/analytics/patterns/${patternId}`);
    return response.data;
  }

  // Project Management
  async analyzeProject(projectPath: string): Promise<any> {
    const response: AxiosResponse<any> = await this.api.post('/projects/analyze', {
      project_path: projectPath,
    });
    return response.data;
  }

  async getProjectRecommendations(projectPath: string): Promise<any> {
    const response: AxiosResponse<any> = await this.api.post('/projects/recommendations', {
      project_path: projectPath,
    });
    return response.data;
  }

  // Predictions
  async getPredictions(projectPath: string): Promise<any> {
    const response: AxiosResponse<any> = await this.api.post('/predictions/issues', {
      project_path: projectPath,
    });
    return response.data;
  }

  // Collaboration
  async sharePattern(patternId: string, teamId: string): Promise<void> {
    await this.api.post('/collaboration/share', {
      pattern_id: patternId,
      team_id: teamId,
    });
  }

  async getSharedPatterns(teamId: string): Promise<Pattern[]> {
    const response: AxiosResponse<{ patterns: Pattern[] }> = await this.api.get(
      `/collaboration/shared/${teamId}`
    );
    return response.data.patterns;
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response: AxiosResponse<{ status: string; timestamp: string }> = await this.api.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;