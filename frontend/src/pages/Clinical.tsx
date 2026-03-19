import { useState, useRef } from 'react'
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Paper,
  Tabs,
  Tab,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Fade,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import CloseIcon from '@mui/icons-material/Close'
import ImageIcon from '@mui/icons-material/Image'
import SearchIcon from '@mui/icons-material/Search'
import ArticleIcon from '@mui/icons-material/Article'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import WarningIcon from '@mui/icons-material/Warning'
import api from '../services/api'

// Convert file to base64
const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = error => reject(error)
  })
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`clinical-tabpanel-${index}`}
      aria-labelledby={`clinical-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

type EvidenceLevel = 'clinical_guidelines' | 'meta_analysis' | 'rct' | 'controlled_trial' | 'cohort' | 'case_control' | 'case_series' | 'case_report' | 'expert_opinion' | 'preclinical' | 'unknown'

const evidenceLevelColors: Record<EvidenceLevel, 'success' | 'info' | 'warning' | 'error'> = {
  clinical_guidelines: 'success',
  meta_analysis: 'info',
  rct: 'info',
  controlled_trial: 'warning',
  cohort: 'warning',
  case_control: 'warning',
  case_series: 'error',
  case_report: 'error',
  expert_opinion: 'error',
  preclinical: 'error',
  unknown: 'error',
}

const evidenceLevelLabels: Record<EvidenceLevel, string> = {
  clinical_guidelines: 'Clinical Guidelines',
  meta_analysis: 'Meta-Analysis',
  rct: 'Randomized Trial',
  controlled_trial: 'Controlled Trial',
  cohort: 'Cohort Study',
  case_control: 'Case-Control',
  case_series: 'Case Series',
  case_report: 'Case Report',
  expert_opinion: 'Expert Opinion',
  preclinical: 'Preclinical',
  unknown: 'Unclassified',
}

interface QueryResultData {
  sources: Array<{
    type: string
    content: string
    evidence_level?: EvidenceLevel
  }>
  summary?: string
  clinical_relevance?: string
  evidence_summary?: Record<EvidenceLevel, number>
}

interface QueryHistoryItem {
  query: string
  result: { data: QueryResultData }
}

export default function Clinical() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [activeTab, setActiveTab] = useState(0)
  const [loading, setLoading] = useState(false)
  const [patientResult, setPatientResult] = useState<unknown>(null)
  const [queryResult, setQueryResult] = useState<QueryResultData | null>(null)
  const [uploadedImages, setUploadedImages] = useState<string[]>([])
  const [error, setError] = useState('')
  const [queryError, setQueryError] = useState('')
  const [queryInput, setQueryInput] = useState('')
  const [includeClinicalTrials, setIncludeClinicalTrials] = useState(false)
  const [maxResults, setMaxResults] = useState(5)
  const [selectedEvidenceLevel, setSelectedEvidenceLevel] = useState<EvidenceLevel | ''>('')
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([])

  // Patient form state
  const [formData, setFormData] = useState({
    age: '',
    sex: 'male' as 'male' | 'female' | 'other',
    chief_complaint: '',
    symptoms: '',
    medical_history: '',
    current_medications: '',
    allergies: '',
    occupation: '',
  })

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const newImages: string[] = []
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      if (file.type.startsWith('image/')) {
        try {
          const base64 = await fileToBase64(file)
          newImages.push(base64.split(',')[1])
        } catch (err) {
          console.error('Error converting file:', err)
        }
      }
    }
    setUploadedImages(prev => [...prev, ...newImages])
  }

  const removeImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index))
  }

  const handlePatientSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await api.analyzePatient(
        {
          age: parseInt(formData.age),
          sex: formData.sex,
          chief_complaint: formData.chief_complaint,
          occupation: formData.occupation || 'Not specified',
          married: false,
          symptoms: formData.symptoms.split(',').map((s) => s.trim()).filter(Boolean),
          medical_history: formData.medical_history.split(',').map((s) => s.trim()).filter(Boolean),
          current_medications: formData.current_medications.split(',').map((s) => s.trim()).filter(Boolean),
          allergies: formData.allergies.split(',').map((s) => s.trim()).filter(Boolean),
        },
        uploadedImages.length > 0 ? uploadedImages : undefined
      )
      setPatientResult(response.data)
    } catch (err: any) {
      console.error('Analysis failed:', err)
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryInput.trim()) return
    setLoading(true)
    setQueryError('')
    try {
      const response = await api.queryMedicalResearch({
        query: queryInput,
        include_clinical_trials: includeClinicalTrials,
        max_results: maxResults,
        sort_by_evidence: true,
        min_evidence_level: selectedEvidenceLevel || undefined,
      })
      const data = response.data.data as QueryResultData
      setQueryResult(data)
      setQueryHistory(prev => [{ query: queryInput, result: { data } }, ...prev.slice(0, 9)])
      setQueryInput('')
    } catch (err: any) {
      console.error('Query failed:', err)
      setQueryError(err.response?.data?.detail || 'Query failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const renderPatientResults = () => {
    if (!patientResult) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: 400,
            color: 'text.secondary',
          }}
        >
          <ImageIcon sx={{ fontSize: 80, opacity: 0.2, mb: 2 }} />
          <Typography variant="body1" gutterBottom>
            Enter patient information to get clinical analysis
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Powered by 15 specialist AI agents
          </Typography>
        </Box>
      )
    }

    const data = typeof patientResult === 'object' && patientResult ? (patientResult as any).data || patientResult : patientResult
    const typedData = data as any

    return (
      <Fade in={true}>
        <Paper sx={{ p: 3, bgcolor: 'rgba(0,0,0,0.2)', maxHeight: 600, overflow: 'auto' }}>
          {typedData.emergency && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="subtitle2">EMERGENCY ALERT</Typography>
              {typedData.immediate_actions?.map((action: string, idx: number) => (
                <Typography key={idx}>• {action}</Typography>
              ))}
            </Alert>
          )}

          {typedData.urgency_level && (
            <Alert severity={typedData.urgency_level === 'critical' ? 'error' : typedData.urgency_level === 'high' ? 'warning' : 'info'} sx={{ mb: 2 }}>
              Urgency Level: {typedData.urgency_level.toUpperCase()}
            </Alert>
          )}

          <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', mt: 2 }}>
            Primary Diagnosis
          </Typography>
          <Typography variant="body1" paragraph>
            {typedData.primary_diagnosis?.diagnosis || typedData.primary_diagnosis_list?.[0] || 'No diagnosis determined'}
          </Typography>
          {typedData.primary_diagnosis?.confidence_score && (
            <Typography variant="body2" color="text.secondary" paragraph>
              Confidence: {Math.round(typedData.primary_diagnosis.confidence_score * 100)}%
            </Typography>
          )}

          {typedData.differential_diagnoses?.length > 0 && (
            <>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', mt: 3 }}>
                Differential Diagnoses
              </Typography>
              <List dense>
                {typedData.differential_diagnoses.map((dx: any, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemText
                      primary={dx.diagnosis}
                      secondary={`Confidence: ${Math.round(dx.confidence_score * 100)}%`}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          {typedData.treatment_plan?.length > 0 && (
            <>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', mt: 3 }}>
                Treatment Plan
              </Typography>
              <List dense>
                {typedData.treatment_plan.map((med: any, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemText
                      primary={`${med.medication} - ${med.dosage}`}
                      secondary={`${med.route} • ${med.duration}`}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          {typedData.investigations?.length > 0 && (
            <>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', mt: 3 }}>
                Recommended Investigations
              </Typography>
              <List dense>
                {typedData.investigations.map((inv: any, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemText
                      primary={inv.test_name}
                      secondary={`${inv.category} • ${inv.urgency}`}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          {typedData.red_flags?.length > 0 && (
            <>
              <Typography variant="h6" gutterBottom sx={{ color: 'error.main', mt: 3 }}>
                Red Flags
              </Typography>
              <List dense>
                {typedData.red_flags.map((flag: string, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemIcon>
                      <WarningIcon color="error" />
                    </ListItemIcon>
                    <ListItemText primary={flag} />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          {typedData.specialist_referrals?.length > 0 && (
            <>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', mt: 3 }}>
                Specialist Referrals
              </Typography>
              <List dense>
                {typedData.specialist_referrals.map((ref: any, idx: number) => (
                  <ListItem key={idx}>
                    <ListItemText
                      primary={ref.specialty}
                      secondary={`${ref.urgency} - ${ref.reason}`}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          <Divider sx={{ my: 3 }} />
          <Typography variant="caption" color="text.secondary" display="block">
            Confidence Score: {Math.round((typedData.confidence_score || 0) * 100)}%
          </Typography>
          {typedData.limitations?.length > 0 && (
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Limitations: {typedData.limitations.join(', ')}
            </Typography>
          )}
        </Paper>
      </Fade>
    )
  }

  const renderQueryResults = () => {
    if (!queryResult && queryHistory.length === 0) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: 400,
            color: 'text.secondary',
          }}
        >
          <SearchIcon sx={{ fontSize: 80, opacity: 0.2, mb: 2 }} />
          <Typography variant="body1" gutterBottom>
            Ask a medical question to get evidence-backed responses
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Search clinical guidelines and medical literature
          </Typography>
        </Box>
      )
    }

    return (
      <Box>
        {/* Query History */}
        {queryHistory.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
              Recent Queries
            </Typography>
            <List>
              {queryHistory.map((item, idx) => (
                <ListItem
                  key={idx}
                  button
                  onClick={() => setQueryResult(item.result.data)}
                  sx={{
                    mb: 1,
                    borderRadius: 1,
                    bgcolor: 'rgba(255,255,255,0.05)',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
                  }}
                >
                  <ListItemIcon>
                    <SearchIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={item.query}
                    secondary={`${item.result.data.sources?.length || 0} sources found`}
                  />
                </ListItem>
              ))}
            </List>
            <Divider sx={{ my: 2 }} />
          </Box>
        )}

        {/* Current Result */}
        {queryResult && (
          <Fade in={true}>
            <Paper sx={{ p: 3, bgcolor: 'rgba(0,0,0,0.2)', maxHeight: 600, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', mb: 2 }}>
                {queryResult.clinical_relevance || 'Research Results'}
              </Typography>

              {queryResult.evidence_summary && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Evidence Summary
                  </Typography>
                  {Object.entries(queryResult.evidence_summary).map(([level, count]) => (
                    <Chip
                      key={level}
                      icon={<CheckCircleIcon />}
                      label={`${evidenceLevelLabels[level as EvidenceLevel] || level}: ${count}`}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                      color={evidenceLevelColors[level as EvidenceLevel] || 'default'}
                    />
                  ))}
                </Box>
              )}

              {queryResult.sources && Array.isArray(queryResult.sources) && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    Sources ({queryResult.sources.length})
                  </Typography>
                  {queryResult.sources.map((source: any, idx: number) => (
                    <Card key={idx} sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.05)' }}>
                      <CardContent sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <ArticleIcon sx={{ mr: 1, color: 'primary.main' }} />
                          <Typography variant="subtitle2">
                            {source.type?.replace('_', ' ') || 'Source'}
                          </Typography>
                          {source.evidence_level && (
                            <Chip
                              label={evidenceLevelLabels[source.evidence_level as EvidenceLevel] || source.evidence_level}
                              size="small"
                              color={evidenceLevelColors[source.evidence_level as EvidenceLevel] || 'default'}
                              sx={{ ml: 'auto' }}
                            />
                          )}
                        </Box>
                        <Typography variant="body2" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                          {source.content}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}

              {queryResult.summary && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Summary
                  </Typography>
                  <Typography variant="body2" color="text.secondary" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                    {queryResult.summary}
                  </Typography>
                </Box>
              )}
            </Paper>
          </Fade>
        )}
      </Box>
    )
  }

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      py: 4,
      background: 'linear-gradient(135deg, #0A0A0F 0%, #0F1419 50%, #0A0F14 100%)',
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'radial-gradient(ellipse at 20% 20%, rgba(20, 184, 166, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.06) 0%, transparent 50%)',
        pointerEvents: 'none',
      }
    }}>
      <Container maxWidth="xl" sx={{ position: 'relative' }}>
        {/* Header */}
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mb: 3, color: 'text.secondary', '&:hover': { color: 'primary.main' } }}
        >
          Back to Dashboard
        </Button>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <Box
            sx={{
              width: 64,
              height: 64,
              borderRadius: 3,
              background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 32px rgba(20, 184, 166, 0.3)',
            }}
          >
            <LocalHospitalIcon sx={{ color: 'white', fontSize: 32 }} />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, background: 'linear-gradient(135deg, #F1F5F9 0%, #94A3B8 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Clinical Decision Support
            </Typography>
            <Typography variant="body2" color="text.secondary">
              AI-powered medical analysis with evidence-backed research
            </Typography>
          </Box>
        </Box>

        {/* Tabs */}
        <Card sx={{ mb: 4, bgcolor: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(10px)' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={activeTab}
              onChange={(e, newValue) => setActiveTab(newValue)}
              variant="fullWidth"
              sx={{
                '& .MuiTab-root': {
                  py: 2,
                  fontWeight: 600,
                  textTransform: 'none',
                },
              }}
            >
              <Tab icon={<LocalHospitalIcon />} label="Patient Analysis" />
              <Tab icon={<SearchIcon />} label="Medical Research Query" />
            </Tabs>
          </Box>

          <TabPanel value={activeTab} index={0}>
            <Grid container spacing={4}>
              {/* Input Form */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ mb: 3, color: 'primary.main' }}>
                      Patient Information
                    </Typography>
                    <form onSubmit={handlePatientSubmit}>
                      <Grid container spacing={2.5}>
                        <Grid item xs={6}>
                          <TextField
                            fullWidth
                            label="Age"
                            type="number"
                            value={formData.age}
                            onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                            required
                            sx={{
                              '& .MuiOutlinedInput-root': {
                                '&:hover fieldset': { borderColor: '#14B8A6' },
                                '&.Mui-focused fieldset': { borderColor: '#14B8A6' },
                              },
                            }}
                          />
                        </Grid>
                        <Grid item xs={6}>
                          <TextField
                            fullWidth
                            select
                            label="Sex"
                            value={formData.sex}
                            onChange={(e) => setFormData({ ...formData, sex: e.target.value as 'male' | 'female' | 'other' })}
                          >
                            <MenuItem value="male">Male</MenuItem>
                            <MenuItem value="female">Female</MenuItem>
                            <MenuItem value="other">Other</MenuItem>
                          </TextField>
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Occupation"
                            value={formData.occupation}
                            onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                            placeholder="Patient's occupation"
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Chief Complaint"
                            value={formData.chief_complaint}
                            onChange={(e) => setFormData({ ...formData, chief_complaint: e.target.value })}
                            required
                            multiline
                            rows={2}
                            placeholder="Primary reason for visit"
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Symptoms (comma-separated)"
                            value={formData.symptoms}
                            onChange={(e) => setFormData({ ...formData, symptoms: e.target.value })}
                            placeholder="e.g., fever, cough, fatigue"
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Medical History (comma-separated)"
                            value={formData.medical_history}
                            onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Current Medications (comma-separated)"
                            value={formData.current_medications}
                            onChange={(e) => setFormData({ ...formData, current_medications: e.target.value })}
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Allergies (comma-separated)"
                            value={formData.allergies}
                            onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
                          />
                        </Grid>

                        {/* Image Upload */}
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" sx={{ mb: 1.5, color: 'text.secondary' }}>
                            Medical Images (X-rays, CT scans, etc.)
                          </Typography>
                          <input
                            type="file"
                            accept="image/*"
                            multiple
                            ref={fileInputRef}
                            onChange={handleImageUpload}
                            style={{ display: 'none' }}
                          />
                          <Paper
                            onClick={() => fileInputRef.current?.click()}
                            sx={{
                              p: 3,
                              border: '2px dashed rgba(148, 163, 184, 0.2)',
                              borderRadius: 2,
                              cursor: 'pointer',
                              textAlign: 'center',
                              transition: 'all 0.2s ease',
                              '&:hover': {
                                borderColor: '#14B8A6',
                                bgcolor: 'rgba(20, 184, 166, 0.05)',
                              },
                            }}
                          >
                            <CloudUploadIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
                            <Typography variant="body2" color="text.secondary">
                              Click to upload medical images
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Supports X-rays, CT scans, MRI images
                            </Typography>
                          </Paper>

                          {/* Preview uploaded images */}
                          {uploadedImages.length > 0 && (
                            <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                              {uploadedImages.map((img, index) => (
                                <Box
                                  key={index}
                                  sx={{
                                    position: 'relative',
                                    width: 80,
                                    height: 80,
                                    borderRadius: 1,
                                    overflow: 'hidden',
                                    border: '1px solid rgba(148, 163, 184, 0.2)',
                                  }}
                                >
                                  <img
                                    src={`data:image/jpeg;base64,${img}`}
                                    alt={`Upload ${index + 1}`}
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                  />
                                  <IconButton
                                    size="small"
                                    onClick={(e) => { e.stopPropagation(); removeImage(index); }}
                                    sx={{
                                      position: 'absolute',
                                      top: 2,
                                      right: 2,
                                      bgcolor: 'rgba(0,0,0,0.7)',
                                      '&:hover': { bgcolor: 'rgba(220,38,38,0.9)' },
                                      width: 24,
                                      height: 24,
                                    }}
                                  >
                                    <CloseIcon sx={{ fontSize: 14, color: 'white' }} />
                                  </IconButton>
                                </Box>
                              ))}
                            </Box>
                          )}
                        </Grid>

                        <Grid item xs={12}>
                          {error && (
                            <Alert severity="error" sx={{ mb: 2 }}>
                              {error}
                            </Alert>
                          )}
                          <Button
                            type="submit"
                            variant="contained"
                            fullWidth
                            size="large"
                            disabled={loading}
                            sx={{
                              background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
                              py: 1.8,
                              fontSize: '1rem',
                              fontWeight: 600,
                              boxShadow: '0 4px 14px rgba(20, 184, 166, 0.4)',
                              '&:hover': {
                                background: 'linear-gradient(135deg, #0D9488 0%, #0F766E 100%)',
                              },
                              '&:disabled': {
                                background: 'rgba(148, 163, 184, 0.2)',
                              },
                            }}
                          >
                            {loading ? (
                              <CircularProgress size={24} color="inherit" />
                            ) : (
                              'Analyze Patient'
                            )}
                          </Button>
                        </Grid>
                      </Grid>
                    </form>
                  </CardContent>
                </Card>
              </Grid>

              {/* Results */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ mb: 3 }}>
                      Analysis Results
                    </Typography>
                    {renderPatientResults()}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            <Grid container spacing={4}>
              {/* Query Form */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ mb: 3, color: 'secondary.main' }}>
                      Medical Research Query
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      Ask any medical question and receive evidence-backed responses from clinical guidelines and medical literature.
                    </Typography>
                    <form onSubmit={handleQuerySubmit}>
                      <Grid container spacing={2.5}>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Your Medical Question"
                            value={queryInput}
                            onChange={(e) => setQueryInput(e.target.value)}
                            required
                            multiline
                            rows={4}
                            placeholder="e.g., What are the current guidelines for hypertension management? What is the first-line treatment for community-acquired pneumonia?"
                            sx={{
                              '& .MuiOutlinedInput-root': {
                                '&:hover fieldset': { borderColor: '#8B5CF6' },
                                '&.Mui-focused fieldset': { borderColor: '#8B5CF6' },
                              },
                            }}
                          />
                        </Grid>

                        <Grid item xs={12} sm={6}>
                          <TextField
                            fullWidth
                            select
                            label="Max Results"
                            value={maxResults}
                            onChange={(e) => setMaxResults(parseInt(e.target.value))}
                          >
                            <MenuItem value={3}>3 sources</MenuItem>
                            <MenuItem value={5}>5 sources</MenuItem>
                            <MenuItem value={10}>10 sources</MenuItem>
                            <MenuItem value={20}>20 sources</MenuItem>
                          </TextField>
                        </Grid>

                        <Grid item xs={12} sm={6}>
                          <TextField
                            fullWidth
                            select
                            label="Minimum Evidence Level"
                            value={selectedEvidenceLevel}
                            onChange={(e) => setSelectedEvidenceLevel(e.target.value as EvidenceLevel | '')}
                          >
                            <MenuItem value="">All levels</MenuItem>
                            <MenuItem value="clinical_guidelines">Clinical Guidelines</MenuItem>
                            <MenuItem value="meta_analysis">Meta-Analysis</MenuItem>
                            <MenuItem value="rct">Randomized Trial</MenuItem>
                            <MenuItem value="cohort">Cohort Study</MenuItem>
                          </TextField>
                        </Grid>

                        <Grid item xs={12}>
                          <Button
                            type="button"
                            variant="outlined"
                            onClick={() => setIncludeClinicalTrials(!includeClinicalTrials)}
                            sx={{ mr: 1, mb: 1 }}
                          >
                            {includeClinicalTrials ? 'Include Clinical Trials ✓' : 'Include Clinical Trials'}
                          </Button>
                        </Grid>

                        <Grid item xs={12}>
                          {queryError && (
                            <Alert severity="error" sx={{ mb: 2 }}>
                              {queryError}
                            </Alert>
                          )}
                          <Button
                            type="submit"
                            variant="contained"
                            fullWidth
                            size="large"
                            disabled={loading || !queryInput.trim()}
                            sx={{
                              background: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)',
                              py: 1.8,
                              fontSize: '1rem',
                              fontWeight: 600,
                              boxShadow: '0 4px 14px rgba(139, 92, 246, 0.4)',
                              '&:hover': {
                                background: 'linear-gradient(135deg, #7C3AED 0%, #DB2777 100%)',
                              },
                              '&:disabled': {
                                background: 'rgba(148, 163, 184, 0.2)',
                              },
                            }}
                          >
                            {loading ? (
                              <CircularProgress size={24} color="inherit" />
                            ) : (
                              'Search Evidence'
                            )}
                          </Button>
                        </Grid>
                      </Grid>
                    </form>
                  </CardContent>
                </Card>
              </Grid>

              {/* Results */}
              <Grid item xs={12} md={6}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ mb: 3 }}>
                      Evidence-Backed Response
                    </Typography>
                    {renderQueryResults()}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </Card>
      </Container>
    </Box>
  )
}
