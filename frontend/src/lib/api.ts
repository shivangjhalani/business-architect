// API client for the Business Capability Management System
export const API_BASE_URL = 'http://localhost:8000/api';

// Types
export interface Capability {
  id: string;
  name: string;
  description: string;
  parent: string | null;
  parent_name?: string | null;
  level: number;
  status: 'CURRENT' | 'PROPOSED' | 'DEPRECATED' | 'ARCHIVED';
  strategic_importance: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  owner?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  children_count?: number;
  full_path: string;
  children?: Capability[];
}

export interface CreateCapabilityRequest {
  name: string;
  description: string;
  parent?: string | null;
  status: 'CURRENT' | 'PROPOSED' | 'DEPRECATED' | 'ARCHIVED';
  strategic_importance: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  owner?: string;
  notes?: string;
}

export interface BusinessGoal {
  id: string;
  title: string;
  description: string;
  pdf_file: string | null;
  status: 'PENDING_ANALYSIS' | 'ANALYZED' | 'RECOMMENDATIONS_APPLIED' | 'CLOSED';
  submitted_at: string;
  recommendations_count: number;
  pending_recommendations_count: number;
  is_analyzed: boolean;
  pdf_filename: string | null;
}

export interface CapabilityRecommendation {
  id: string;
  business_goal: string;
  business_goal_title: string;
  recommendation_type: 'ADD_CAPABILITY' | 'MODIFY_CAPABILITY' | 'DELETE_CAPABILITY' | 'STRENGTHEN_CAPABILITY' | 'MERGE_CAPABILITIES' | 'SPLIT_CAPABILITY';
  target_capability: string | null;
  target_capability_details: any;
  proposed_name: string | null;
  proposed_description: string | null;
  proposed_parent: string | null;
  proposed_parent_details: any;
  additional_details: string | null;
  status: 'PENDING' | 'APPLIED' | 'REJECTED';
  recommended_by_ai_at: string;
  applied_at: string | null;
  is_actionable: boolean;
  confidence_score?: number;
}

export interface LLMQuery {
  query: string;
  context?: string;
}

export interface LLMResponse {
  answer: string;
  query: string;
  context_used: string;
  vector_context: {
    similar_capabilities: any[];
    similar_goals: any[];
    similar_recommendations: any[];
    context_enhancement: string;
  };
}

export interface VectorSearchRequest {
  query: string;
  limit?: number;
  threshold?: number;
}

export interface VectorSearchResult {
  id: string;
  name?: string;
  title?: string;
  description: string;
  similarity_score: number;
  full_path?: string;
  strategic_importance?: string;
}

export interface ApiResponse<T> {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results: T[];
}

// API Client Class
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`API Error: ${response.status} - ${error}`);
      }

      // Handle empty responses (like 204 No Content)
      const contentType = response.headers.get('content-type');
      if (response.status === 204 || !contentType?.includes('application/json')) {
        return undefined as T;
      }

      const text = await response.text();
      if (!text.trim()) {
        return undefined as T;
      }

      return JSON.parse(text);
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Capabilities API
  async getCapabilities(params?: {
    status?: string;
    level?: number;
    parent_id?: string;
    root_only?: boolean;
    search?: string;
  }): Promise<ApiResponse<Capability>> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.level) searchParams.append('level', params.level.toString());
    if (params?.parent_id) searchParams.append('parent_id', params.parent_id);
    if (params?.root_only) searchParams.append('root_only', 'true');
    if (params?.search) searchParams.append('search', params.search);

    return this.request(`/capabilities/?${searchParams}`);
  }

  async getCapability(id: string): Promise<Capability> {
    return this.request(`/capabilities/${id}/`);
  }

  async createCapability(capability: CreateCapabilityRequest): Promise<Capability> {
    return this.request(`/capabilities/`, {
      method: 'POST',
      body: JSON.stringify(capability),
    });
  }

  async updateCapability(id: string, capability: Partial<CreateCapabilityRequest>): Promise<Capability> {
    return this.request(`/capabilities/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(capability),
    });
  }

  async deleteCapability(id: string): Promise<void> {
    return this.request(`/capabilities/${id}/`, {
      method: 'DELETE',
    });
  }

  async permanentDeleteCapability(id: string): Promise<{ message: string }> {
    return this.request(`/capabilities/${id}/permanent_delete/`, {
      method: 'DELETE',
    });
  }

  async getSimilarCapabilities(id: string, limit = 5, threshold = 0.6): Promise<{
    similar_capabilities: VectorSearchResult[];
    query_capability: { id: string; name: string };
  }> {
    return this.request(`/capabilities/${id}/similar/?limit=${limit}&threshold=${threshold}`);
  }

  async searchCapabilities(request: VectorSearchRequest): Promise<{
    results: VectorSearchResult[];
    query: string;
    total_results: number;
  }> {
    return this.request(`/capabilities/search/`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Business Goals API
  async getBusinessGoals(params?: {
    status?: string;
    search?: string;
  }): Promise<ApiResponse<BusinessGoal>> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.search) searchParams.append('search', params.search);

    return this.request(`/business-goals/?${searchParams}`);
  }

  async getBusinessGoal(id: string): Promise<BusinessGoal> {
    return this.request(`/business-goals/${id}/`);
  }

  async createBusinessGoal(formData: FormData): Promise<BusinessGoal> {
    return this.request(`/business-goals/`, {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData,
    });
  }

  async deleteBusinessGoal(id: string): Promise<void> {
    return this.request(`/business-goals/${id}/`, {
      method: 'DELETE',
    });
  }

  async permanentDeleteBusinessGoal(id: string): Promise<{ message: string }> {
    return this.request(`/business-goals/${id}/permanent_delete/`, {
      method: 'DELETE',
    });
  }

  async analyzeBusinessGoal(id: string): Promise<{
    status: string;
    recommendations_created: number;
    summary: string;
  }> {
    return this.request(`/business-goals/${id}/analyze/`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async getSimilarBusinessGoals(id: string, limit = 5): Promise<{
    similar_goals: VectorSearchResult[];
    query_goal: { id: string; title: string };
  }> {
    return this.request(`/business-goals/${id}/similar/?limit=${limit}`);
  }

  async searchBusinessGoals(request: VectorSearchRequest): Promise<{
    results: VectorSearchResult[];
    query: string;
    total_results: number;
  }> {
    return this.request(`/business-goals/search/`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Recommendations API
  async getRecommendations(params?: {
    recommendation_type?: string;
    status?: string;
    business_goal?: string;
  }): Promise<ApiResponse<CapabilityRecommendation>> {
    const searchParams = new URLSearchParams();
    if (params?.recommendation_type) searchParams.append('recommendation_type', params.recommendation_type);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.business_goal) searchParams.append('business_goal', params.business_goal);

    return this.request(`/recommendations/?${searchParams}`);
  }

  async getBusinessGoalRecommendations(goalId: string): Promise<ApiResponse<CapabilityRecommendation>> {
    return this.request(`/business-goals/${goalId}/recommendations/`);
  }

  async applyRecommendation(id: string): Promise<{
    status: string;
    action_taken: string;
    capability_id?: string;
    message: string;
  }> {
    return this.request(`/recommendations/${id}/apply/`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async rejectRecommendation(id: string): Promise<{
    status: string;
  }> {
    return this.request(`/recommendations/${id}/reject/`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async permanentDeleteRecommendation(id: string): Promise<{ message: string }> {
    return this.request(`/recommendations/${id}/permanent_delete/`, {
      method: 'DELETE',
    });
  }

  // LLM API
  async queryLLM(request: LLMQuery): Promise<LLMResponse> {
    return this.request(`/llm/query/`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Vector Database API
  async getVectorStatus(): Promise<{
    indexes: Record<string, any>;
    overall_health: string;
  }> {
    return this.request(`/vectors/status/`);
  }

  async getCapabilityRecommendations(id: string): Promise<ApiResponse<CapabilityRecommendation>> {
    return this.request(`/capabilities/${id}/recommendations/`);
  }
}

export const apiClient = new ApiClient(); 