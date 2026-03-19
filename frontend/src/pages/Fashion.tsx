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
  Chip,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import CheckroomIcon from '@mui/icons-material/Checkroom'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import CloseIcon from '@mui/icons-material/Close'
import ImageIcon from '@mui/icons-material/Image'
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

export default function Fashion() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<unknown>(null)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    query_type: 'style' as 'style' | 'trend' | 'outfit' | 'accessory' | 'general',
    question: '',
    occasion: '',
    season: '',
    body_type: '',
    personal_style: [] as string[],
  })

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file')
      return
    }

    try {
      const base64 = await fileToBase64(file)
      setUploadedImage(base64.split(',')[1]) // Remove data URL prefix
      setError('')
    } catch (err) {
      console.error('Error converting file:', err)
      setError('Failed to process image')
    }
  }

  const removeImage = () => {
    setUploadedImage(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await api.analyzeFashion({
        query_type: formData.query_type,
        question: formData.question,
        occasion: formData.occasion || undefined,
        season: formData.season || undefined,
        body_type: formData.body_type || undefined,
        personal_style: formData.personal_style.length > 0 ? formData.personal_style : undefined,
      }, uploadedImage || undefined)
      setResult(response.data)
    } catch (err: any) {
      console.error('Analysis failed:', err)
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
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
        background: 'radial-gradient(ellipse at 20% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(236, 72, 153, 0.06) 0%, transparent 50%)',
        pointerEvents: 'none',
      }
    }}>
      <Container maxWidth="lg" sx={{ position: 'relative' }}>
        {/* Header */}
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mb: 3, color: 'text.secondary', '&:hover': { color: 'secondary.main' } }}
        >
          Back to Dashboard
        </Button>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 3,
              background: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 32px rgba(139, 92, 246, 0.3)',
            }}
          >
            <CheckroomIcon sx={{ color: 'white', fontSize: 28 }} />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, background: 'linear-gradient(135deg, #F1F5F9 0%, #94A3B8 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Fashion AI
            </Typography>
            <Typography variant="body2" color="text.secondary">
              AI-powered style recommendations and trend analysis
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={4}>
          {/* Input Form */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Style Query
                </Typography>
                <form onSubmit={handleSubmit}>
                  <Grid container spacing={2.5}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        select
                        label="Query Type"
                        value={formData.query_type}
                        onChange={(e) => setFormData({ ...formData, query_type: e.target.value as typeof formData.query_type })}
                      >
                        <MenuItem value="style">Style Advice</MenuItem>
                        <MenuItem value="trend">Trends</MenuItem>
                        <MenuItem value="outfit">Outfit</MenuItem>
                        <MenuItem value="accessory">Accessories</MenuItem>
                        <MenuItem value="general">General</MenuItem>
                      </TextField>
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Occasion"
                        value={formData.occasion}
                        onChange={(e) => setFormData({ ...formData, occasion: e.target.value })}
                        placeholder="e.g., formal, casual"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Season"
                        value={formData.season}
                        onChange={(e) => setFormData({ ...formData, season: e.target.value })}
                        placeholder="e.g., summer, winter"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Body Type (optional)"
                        value={formData.body_type}
                        onChange={(e) => setFormData({ ...formData, body_type: e.target.value })}
                        placeholder="e.g., hourglass, athletic, slim"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Your Question"
                        value={formData.question}
                        onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                        required
                        multiline
                        rows={4}
                        placeholder="e.g., What should I wear to a summer wedding? How do I incorporate this season's trends?"
                      />
                    </Grid>

                    {/* Image Upload */}
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" sx={{ mb: 1.5, color: 'text.secondary' }}>
                        Upload Clothing Image (optional)
                      </Typography>
                      <input
                        type="file"
                        accept="image/*"
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
                            borderColor: '#8B5CF6',
                            background: 'rgba(139, 92, 246, 0.05)',
                          },
                        }}
                      >
                        {uploadedImage ? (
                          <Box>
                            <Box
                              sx={{
                                width: 120,
                                height: 120,
                                borderRadius: 2,
                                overflow: 'hidden',
                                margin: '0 auto 1rem',
                                border: '2px solid rgba(139, 92, 246, 0.3)',
                              }}
                            >
                              <img
                                src={`data:image/jpeg;base64,${uploadedImage}`}
                                alt="Uploaded clothing"
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              Image uploaded ✓
                            </Typography>
                            <Button
                              size="small"
                              onClick={(e) => { e.stopPropagation(); removeImage(); }}
                              sx={{ mt: 1 }}
                              startIcon={<CloseIcon />}
                            >
                              Remove
                            </Button>
                          </Box>
                        ) : (
                          <>
                            <CloudUploadIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
                            <Typography variant="body2" color="text.secondary">
                              Click to upload clothing image
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Get style analysis based on your item
                            </Typography>
                          </>
                        )}
                      </Paper>
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
                          'Get Style Advice'
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
                  Style Recommendations
                </Typography>
                {result ? (
                  <Box>
                    <Alert severity="success" sx={{ mb: 2, bgcolor: 'rgba(139, 92, 246, 0.1)', color: '#8B5CF6' }}>
                      Analysis completed
                    </Alert>
                    <Paper sx={{ p: 2, bgcolor: 'rgba(0,0,0,0.2)', maxHeight: 500, overflow: 'auto' }}>
                      <Typography 
                        variant="body2" 
                        component="pre" 
                        sx={{ 
                          color: 'text.secondary', 
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word'
                        }}
                      >
                        {JSON.stringify(result, null, 2)}
                      </Typography>
                    </Paper>
                  </Box>
                ) : (
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      height: 300,
                      color: 'text.secondary',
                    }}
                  >
                    <ImageIcon sx={{ fontSize: 64, opacity: 0.2, mb: 2 }} />
                    <Typography>Enter your fashion question</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
