import axios, { type AxiosInstance } from 'axios';

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Message type for ChatInterface
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  domain?: string;
}

// Error handler helper
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.error || error.message || 'An error occurred';
  }
  return error instanceof Error ? error.message : 'An unknown error occurred';
}

// CDS API
export const cdsApi = {
  query: (query: string, context?: string) =>
    apiClient.post('/cds/query', { query, patient_context: context }),
  health: () => apiClient.get('/cds/health'),
  agents: () => apiClient.get('/cds/agents'),
};

// Chat helper functions for ChatInterface
export const sendCDSMessage = async (params: { message: string; context?: Record<string, unknown> }) => {
  const response = await cdsApi.query(params.message, params.context?.patient_context as string);
  // Transform to chat format
  const data = response.data;
  return {
    response: data.response || data.recommendations?.join('\n') || '',
    recommendations: data.recommendations || [],
    evidence: data.evidence || [],
    agent_id: data.agent_id,
    confidence: data.confidence,
  };
};

export const sendFinanceQuery = async (params: { query: string }) => {
  const response = await financeApi.query(params.query);
  const data = response.data;
  return {
    response: data.proposed_action || data.reasoning || '',
    reasoning: data.reasoning,
    hitlRequired: data.status === 'pending_approval',
    thread_id: data.thread_id,
  };
};

// Finance API
export const financeApi = {
  query: (query: string) =>
    apiClient.post('/finance/query', { query }),
  approve: (threadId: string, decision: string) =>
    apiClient.post('/finance/approve', { thread_id: threadId, decision }),
  threads: () => apiClient.get('/finance/threads'),
  reflectionAnalyze: (query: string) =>
    apiClient.post('/finance/reflection/analyze', { query }),
  getReflectionStatus: (threadId: string) =>
    apiClient.get(`/finance/reflection/status/${threadId}`),
};

// HITL helper functions
export const getPendingApprovals = async () => {
  const response = await apiClient.get('/finance/threads');
  const threads = response.data.threads || [];
  return threads
    .filter((t: { status: string }) => t.status === 'pending_approval')
    .map((t: { thread_id: string; query: string; current_stage: string }) => ({
      id: t.thread_id,
      type: 'Financial Analysis',
      description: t.query?.substring(0, 100) || 'Financial query',
      timestamp: new Date().toISOString(),
    }));
};

export const approveFinanceAction = async (actionId: string) => {
  return financeApi.approve(actionId, 'approve');
};

export const rejectFinanceAction = async (actionId: string, reason: string) => {
  return financeApi.approve(actionId, 'reject');
};

// AI Dev API
export const aiDevApi = {
  query: (query: string, language?: string) =>
    apiClient.post('/ai/query', { query, language: language || 'python' }),
  analyze: (query: string, codeSnippet?: string, repo?: string, filePath?: string) =>
    apiClient.post('/ai/analyze', { query, code_snippet: codeSnippet, repo, file_path: filePath }),
  health: () => apiClient.get('/ai/health'),
};

// analyzeCode helper for AIDev page
export interface AIDevResponse {
  status: string;
  analysis: string;
  issues: Array<{
    severity: string;
    message: string;
    suggestion?: string;
    line?: number;
  }>;
  suggestions: string[];
  metadata?: Record<string, unknown>;
}

export const analyzeCode = async (params: {
  code: string;
  language: string;
  analysisType: string;
}): Promise<AIDevResponse> => {
  // Map analysis type to query
  const queryMap: Record<string, string> = {
    full: `Perform full analysis on this ${params.language} code`,
    security: `Analyze this ${params.language} code for security vulnerabilities`,
    performance: `Analyze this ${params.language} code for performance issues`,
    best_practices: `Review this ${params.language} code for best practices`,
  };
  
  const response = await aiDevApi.analyze(
    queryMap[params.analysisType] || queryMap.full,
    params.code
  );
  return response.data;
};

// Fashion API
export const fashionApi = {
  query: (query: string, budget?: string, occasion?: string, domain?: string) =>
    apiClient.post('/fashion/query', { 
      query, 
      budget: budget || '50k-150k NGN',
      occasion: occasion || '',
      domain: domain || 'both'
    }),
  style: (occasion: string, styleDomain?: string, budgetRange?: string, preferences?: string) =>
    apiClient.post('/fashion/style', {
      occasion,
      style_domain: styleDomain || 'both',
      budget_range: budgetRange || '50k-150k NGN',
      preferences: preferences || ''
    }),
  corporate: (occasion: string, budgetRange?: string, preferences?: string) =>
    apiClient.post('/fashion/corporate', { occasion, budget_range: budgetRange, preferences }),
  cultural: (occasion: string, budgetRange?: string, preferences?: string) =>
    apiClient.post('/fashion/cultural', { occasion, budget_range: budgetRange, preferences }),
  health: () => apiClient.get('/fashion/health'),
};

// Fashion helper functions and types
export interface FashionResponse {
  status: string;
  outfit?: string;
  recommendations?: string[];
  stylingTips?: string[];
  colorPalette?: string[];
  sources?: string[];
  budget_breakdown?: string;
  tips?: string[];
  metadata?: Record<string, unknown>;
}

export const getFashionRecommendations = async (params: {
  style: string;
  preferences?: string;
  occasion?: string;
  bodyType?: string;
}): Promise<FashionResponse> => {
  const response = await fashionApi.query(
    params.style,
    '50k-150k NGN',
    params.occasion,
    'both'
  );
  const data = response.data;
  
  // Transform response to match expected format
  return {
    status: data.status,
    recommendations: data.outfit ? [data.outfit] : [],
    stylingTips: data.tips || [],
    colorPalette: [],
    sources: data.sources || [],
    budget_breakdown: data.budget_breakdown,
    metadata: data.metadata,
  };
};

// Evaluation API
export const evaluationApi = {
  submitRating: (interactionId: string, rating: number, feedback?: string) =>
    apiClient.post('/evaluation/feedback', { 
      interaction_id: interactionId, 
      rating, 
      feedback 
    }),
  getMetrics: () => apiClient.get('/evaluation/metrics'),
};

export default apiClient;
