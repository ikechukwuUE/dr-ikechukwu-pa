/**
 * API Service for Vogue Space Multi-Agent System
 * ===============================================
 * Handles all API calls to the Flask backend.
 * Updated for BeeAI Framework integration with MCP tools.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// ============================================================================
// TYPES
// ============================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  timestamp: string;
  services: {
    flask: string;
    beeai: string;
    mcp: string;
  };
}

export interface MedicineQAResponse {
  session_id: string;
  query: string;
  final_output: string;
  urgency: string | null;
  specialty: string;
  completed_steps: string[];
}

export interface MedicineResearchResponse {
  session_id: string;
  question: string;
  final_output: string;
  completed_steps: string[];
}

export interface MedicineClinicalResponse {
  session_id: string;
  final_output: string;
  urgency: string | null;
  specialty: string;
  human_approved: boolean;
  completed_steps: string[];
}

export interface MedicineNewsResponse {
  final_output: string;
  completed_steps: string[];
}

export interface FinanceQAResponse {
  session_id: string;
  query: string;
  final_output: string;
  completed_steps: string[];
}

export interface FinanceInvestmentResponse {
  session_id: string;
  final_output: string;
  investment_plan: {
    summary: string;
    guide: {
      strategy: string;
      allocations: Record<string, number>;
      warnings: string[];
    };
    risk_history: Array<{
      risk_level: string;
      findings: string[];
      iteration: number;
      resolved: boolean;
    }>;
  } | null;
  risk_resolved: boolean;
  risk_iteration: number;
  completed_steps: string[];
}

export interface FinanceNewsResponse {
  final_output: string;
  completed_steps: string[];
}

export interface CodingGenerateResponse {
  session_id: string;
  description: string;
  language: string;
  final_output: string;
  generated_code: string | null;
  review_approved: boolean;
  review_iteration: number;
  issues: string[];
  completed_steps: string[];
}

export interface CodingNewsResponse {
  final_output: string;
  completed_steps: string[];
}

export interface FashionAnalyzeResponse {
  session_id: string;
  final_output: string;
  outfit_analysis: {
    items_detected: string[];
    style: string;
    colors: string[];
    occasion_fit: string;
    suggestions: string[];
  } | null;
  completed_steps: string[];
}

export interface FashionTrendsResponse {
  final_output: string;
  style_trend: {
    current_trends: string[];
    trending_colors: string[];
    trending_styles: string[];
  } | null;
  completed_steps: string[];
}

export interface FashionRecommendResponse {
  session_id: string;
  final_output: string;
  outfit_recommendation: {
    recommended_items: string[];
    style_notes: string;
    estimated_cost: number;
    trend_alignment: string;
  } | null;
  completed_steps: string[];
}

export interface FashionNewsResponse {
  final_output: string;
  completed_steps: string[];
}

// ============================================================================
// API CLIENT
// ============================================================================

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      
      const defaultHeaders: HeadersInit = {
        'Content-Type': 'application/json',
      };

      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP error! status: ${response.status}`,
        };
      }

      return {
        success: true,
        data: data.data || data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  // ==========================================================================
  // HEALTH CHECK
  // ==========================================================================

  async healthCheck(): Promise<ApiResponse<HealthCheckResponse>> {
    return this.request<HealthCheckResponse>('/api/health');
  }

  // ==========================================================================
  // MEDICINE DOMAIN
  // ==========================================================================

  async medicineQA(
    query: string,
    sessionId?: string
  ): Promise<ApiResponse<MedicineQAResponse>> {
    return this.request<MedicineQAResponse>('/api/medicine/qa', {
      method: 'POST',
      body: JSON.stringify({ query, session_id: sessionId }),
    });
  }

  async medicineResearch(
    question: string,
    scope: string = 'broad',
    sessionId?: string
  ): Promise<ApiResponse<MedicineResearchResponse>> {
    return this.request<MedicineResearchResponse>('/api/medicine/research', {
      method: 'POST',
      body: JSON.stringify({ question, scope, session_id: sessionId }),
    });
  }

  async medicineClinical(
    patientInfo: {
      history: string;
      examination: string;
      investigations: Record<string, any>;
    },
    sessionId?: string
  ): Promise<ApiResponse<MedicineClinicalResponse>> {
    return this.request<MedicineClinicalResponse>('/api/medicine/clinical', {
      method: 'POST',
      body: JSON.stringify({ patient_info: patientInfo, session_id: sessionId }),
    });
  }

  async medicineClinicalImage(
    formData: FormData
  ): Promise<ApiResponse<MedicineClinicalResponse>> {
    try {
      const url = `${this.baseUrl}/api/medicine/clinical`;
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP error! status: ${response.status}`,
        };
      }

      return {
        success: true,
        data: data.data || data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  async medicineClinicalApprove(
    sessionId: string,
    approved: boolean,
    feedback?: string,
    modifications?: string[]
  ): Promise<ApiResponse<any>> {
    return this.request<any>('/api/medicine/clinical/approve', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        approved,
        feedback,
        modifications,
      }),
    });
  }

  async medicineNews(): Promise<ApiResponse<MedicineNewsResponse>> {
    return this.request<MedicineNewsResponse>('/api/medicine/news');
  }

  // ==========================================================================
  // FINANCE DOMAIN
  // ==========================================================================

  async financeQA(
    query: string,
    sessionId?: string
  ): Promise<ApiResponse<FinanceQAResponse>> {
    return this.request<FinanceQAResponse>('/api/finance/qa', {
      method: 'POST',
      body: JSON.stringify({ query, session_id: sessionId }),
    });
  }

  async financeInvestment(
    investorInfo: {
      age: number;
      salary: number;
      occupation: string;
      target_fund: number;
    },
    sessionId?: string
  ): Promise<ApiResponse<FinanceInvestmentResponse>> {
    return this.request<FinanceInvestmentResponse>('/api/finance/investment', {
      method: 'POST',
      body: JSON.stringify({ investor_info: investorInfo, session_id: sessionId }),
    });
  }

  async financeNews(): Promise<ApiResponse<FinanceNewsResponse>> {
    return this.request<FinanceNewsResponse>('/api/finance/news');
  }

  // ==========================================================================
  // CODING DOMAIN
  // ==========================================================================

  async codingGenerate(
    description: string,
    language: string = 'python',
    constraints: string[] = [],
    sessionId?: string
  ): Promise<ApiResponse<CodingGenerateResponse>> {
    return this.request<CodingGenerateResponse>('/api/coding/generate', {
      method: 'POST',
      body: JSON.stringify({
        description,
        language,
        constraints,
        session_id: sessionId,
      }),
    });
  }

  async codingNews(): Promise<ApiResponse<CodingNewsResponse>> {
    return this.request<CodingNewsResponse>('/api/coding/news');
  }

  async codingReview(
    code: string,
    language: string = 'python',
    sessionId?: string
  ): Promise<ApiResponse<CodingGenerateResponse>> {
    return this.request<CodingGenerateResponse>('/api/coding/review', {
      method: 'POST',
      body: JSON.stringify({
        code,
        language,
        session_id: sessionId,
      }),
    });
  }

  async codingDebug(
    code: string,
    language: string = 'python',
    error: string = '',
    sessionId?: string
  ): Promise<ApiResponse<CodingGenerateResponse>> {
    return this.request<CodingGenerateResponse>('/api/coding/debug', {
      method: 'POST',
      body: JSON.stringify({
        code,
        language,
        error,
        session_id: sessionId,
      }),
    });
  }

  // ==========================================================================
  // FASHION DOMAIN
  // ==========================================================================

  async fashionAnalyze(
    imageDescription: string,
    sessionId?: string
  ): Promise<ApiResponse<FashionAnalyzeResponse>> {
    return this.request<FashionAnalyzeResponse>('/api/fashion/analyze', {
      method: 'POST',
      body: JSON.stringify({
        image_description: imageDescription,
        session_id: sessionId,
      }),
    });
  }

  async fashionAnalyzeImage(
    formData: FormData
  ): Promise<ApiResponse<FashionAnalyzeResponse>> {
    try {
      const url = `${this.baseUrl}/api/fashion/analyze`;
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP error! status: ${response.status}`,
        };
      }

      return {
        success: true,
        data: data.data || data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  async fashionTrends(): Promise<ApiResponse<FashionTrendsResponse>> {
    return this.request<FashionTrendsResponse>('/api/fashion/trends');
  }

  async fashionRecommend(
    budget: number,
    occasion: string,
    time: string,
    location: string,
    sessionId?: string
  ): Promise<ApiResponse<FashionRecommendResponse>> {
    return this.request<FashionRecommendResponse>('/api/fashion/recommend', {
      method: 'POST',
      body: JSON.stringify({
        budget,
        occasion,
        time,
        location,
        session_id: sessionId,
      }),
    });
  }

  async fashionNews(): Promise<ApiResponse<FashionNewsResponse>> {
    return this.request<FashionNewsResponse>('/api/fashion/news');
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export const api = new ApiClient(API_BASE_URL);

export default api;
