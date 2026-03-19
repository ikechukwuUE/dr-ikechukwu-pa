// API Service for Dr. Ikechukwu PA Backend
import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class APIService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  // ============ Clinical Decision Support (CDS) ============
  async analyzePatient(patientData: {
    patient_id?: string
    age: number
    sex: 'male' | 'female' | 'other'
    occupation?: string
    married?: boolean
    weight_kg?: number
    height_cm?: number
    chief_complaint: string
    symptoms: string[]
    medical_history: string[]
    current_medications: string[]
    allergies: string[]
    vital_signs?: Record<string, unknown>
  }, images?: string[]) {
    const payload: any = {
      patient_info: patientData,
    }
    if (images && images.length > 0) {
      payload.images = images
    }
    const response = await this.client.post('/api/cds/analyze', payload)
    return response.data
  }

  async getSpecialists() {
    const response = await this.client.get('/api/cds/specialists')
    return response.data
  }

  async queryMedicalResearch(data: {
    query: string
    include_clinical_trials?: boolean
    max_results?: number
    sort_by_evidence?: boolean
    min_evidence_level?: 'clinical_guidelines' | 'meta_analysis' | 'rct' | 'controlled_trial' | 'cohort' | 'case_control' | 'case_series' | 'case_report' | 'expert_opinion' | 'preclinical' | 'unknown'
  }) {
    const response = await this.client.post('/api/cds/query', {
      query: data.query,
      include_clinical_trials: data.include_clinical_trials ?? false,
      max_results: data.max_results ?? 5,
      sort_by_evidence: data.sort_by_evidence ?? true,
      min_evidence_level: data.min_evidence_level
    })
    return response.data
  }

  // ============ Finance ============
  async analyzeFinance(data: {
    query_type: 'investment' | 'budget' | 'tax' | 'retirement' | 'debt' | 'general'
    question: string
    financial_goals?: string[]
    risk_tolerance?: 'conservative' | 'moderate' | 'aggressive'
    time_horizon_years?: number
  }) {
    const response = await this.client.post('/api/finance/analyze', {
      query: data,
    })
    return response.data
  }

  async analyzePortfolio(portfolio: {
    stocks?: Record<string, number>
    bonds?: Record<string, number>
    etfs?: Record<string, number>
    cash?: number
    crypto?: Record<string, number>
  }) {
    const response = await this.client.post('/api/finance/portfolio/analyze', portfolio)
    return response.data
  }

  // ============ Fashion ============
  async analyzeFashion(data: {
    query_type: 'style' | 'trend' | 'outfit' | 'accessory' | 'general'
    question: string
    occasion?: string
    season?: string
    body_type?: string
    personal_style?: string[]
  }, imageData?: string) {
    const payload: any = {
      query: data,
    }
    if (imageData) {
      payload.image_analysis = {
        image_data: imageData,
        analysis_type: ['style', 'color', 'trend', 'occasion'],
      }
    }
    const response = await this.client.post('/api/fashion/analyze', payload)
    return response.data
  }

  async getOutfitRecommendation(occasion: string, weather?: string) {
    const response = await this.client.get('/api/fashion/outfit', {
      params: { occasion, weather },
    })
    return response.data
  }

  // ============ AI Development ============
  async generateCode(data: {
    language: string
    task_description: string
    constraints?: string[]
    test_cases?: string[]
    framework?: string
  }) {
    const response = await this.client.post('/api/aidev/generate', data)
    return response.data
  }

  async debugCode(data: {
    code: string
    error_message?: string
    language: string
    context?: string
  }) {
    const response = await this.client.post('/api/aidev/debug', data)
    return response.data
  }

  async reviewCode(code: string, language: string) {
    const response = await this.client.post('/api/aidev/review', null, {
      params: { code, language },
    })
    return response.data
  }

  // ============ Health Check ============
  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }
}

export const api = new APIService()
export default api
