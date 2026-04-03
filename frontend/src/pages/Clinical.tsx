import { Box, Typography, TextField, Button, Paper, CircularProgress, IconButton, alpha, Chip, Avatar, Fade, Zoom, useTheme } from '@mui/material'
import ReactMarkdown from 'react-markdown'
import { useState, useRef, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import SendIcon from '@mui/icons-material/Send'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import WarningIcon from '@mui/icons-material/Warning'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import DeleteIcon from '@mui/icons-material/Delete'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ScienceIcon from '@mui/icons-material/Science'
import MedicalServicesIcon from '@mui/icons-material/MedicalServices'
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety'
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart'
import VaccinesIcon from '@mui/icons-material/Vaccines'
import { api } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  image?: string
  metadata?: {
    urgency?: string
    specialty?: string
    completed_steps?: string[]
  }
}

export default function Clinical() {
  const navigate = useNavigate()
  const theme = useTheme()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'qa' | 'research' | 'clinical'>('qa')
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleImageSelect = useCallback((file: File) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setSelectedImage(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleImageSelect(file)
  }, [handleImageSelect])

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleImageSelect(file)
  }

  const clearImage = () => {
    setSelectedImage(null)
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSend = async () => {
    if ((!input.trim() && !selectedImage) || loading) return

    const userMessage: Message = { 
      role: 'user', 
      content: input || 'Please analyze this medical image', 
      timestamp: new Date(),
      image: selectedImage || undefined
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      let response
      if (mode === 'qa') {
        response = await api.medicineQA(input)
      } else if (mode === 'research') {
        response = await api.medicineResearch(input)
      } else {
        if (selectedFile) {
          const formData = new FormData()
          formData.append('image', selectedFile)
          formData.append('patient_info', JSON.stringify({
            history: input || 'Medical image analysis requested',
            examination: '',
            investigations: {}
          }))
          response = await api.medicineClinicalImage(formData)
        } else {
          response = await api.medicineClinical({
            history: input,
            examination: '',
            investigations: {}
          })
        }
      }

      const formatMedicineResponse = (data: any) => {
        if (!data) return 'Unable to process your request'
        
        let content = `## Medical Assessment\n\n`
        
        if (data.urgency) {
          content += `**Urgency Level:** ${data.urgency.toUpperCase()}\n\n`
        }
        
        if (data.specialty) {
          content += `**Specialty:** ${data.specialty}\n\n`
        }
        
        if (data.specialist_response) {
          content += `### Specialist Assessment\n${data.specialist_response.assessment || 'Assessment completed'}\n\n`
          
          if (data.specialist_response.recommendations && data.specialist_response.recommendations.length > 0) {
            content += `### Recommendations\n`
            data.specialist_response.recommendations.forEach((rec: string) => {
              content += `- ${rec}\n`
            })
            content += '\n'
          }
        }
        
        if (data.management_plan) {
          content += `### Management Plan\n${data.management_plan.personalized_plan || 'Plan created'}\n\n`
          
          if (data.management_plan.follow_up) {
            content += `**Follow-up:** ${data.management_plan.follow_up}\n`
          }
        }
        
        return content
      }

      const assistantMessage: Message = { 
        role: 'assistant', 
        content: response.success && response.data 
          ? response.data.final_output || formatMedicineResponse(response.data)
          : response.error || 'Unable to process your request',
        timestamp: new Date(),
        metadata: response.success && response.data ? {
          urgency: (response.data as any).urgency,
          specialty: (response.data as any).specialty,
          completed_steps: (response.data as any).completed_steps
        } : undefined
      }
      setMessages(prev => [...prev, assistantMessage])
      clearImage()
    } catch (error) {
      const errorMessage: Message = { 
        role: 'assistant', 
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date() 
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const getUrgencyColor = (urgency?: string) => {
    switch (urgency) {
      case 'emergency': return '#EF4444'
      case 'high': return '#F59E0B'
      case 'medium': return '#3B82F6'
      case 'low': return '#10B981'
      default: return '#6B7280'
    }
  }

  const getModeIcon = (m: string) => {
    switch (m) {
      case 'qa': return <LocalHospitalIcon />
      case 'research': return <ScienceIcon />
      case 'clinical': return <MedicalServicesIcon />
      default: return <LocalHospitalIcon />
    }
  }

  const getModeColor = (m: string) => {
    switch (m) {
      case 'qa': return '#10B981'
      case 'research': return '#8B5CF6'
      case 'clinical': return '#F97316'
      default: return '#10B981'
    }
  }

  const modes = [
    { id: 'qa', label: 'Medical Q&A', icon: <LocalHospitalIcon />, desc: 'Ask medical questions' },
    { id: 'research', label: 'Research', icon: <ScienceIcon />, desc: 'Deep medical research' },
    { id: 'clinical', label: 'Clinical Decision', icon: <MedicalServicesIcon />, desc: 'Clinical support & imaging' },
  ]

  return (
    <Box sx={{ 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      background: 'linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 50%, #2d2d2d 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated background */}
      <Box sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none',
        zIndex: 0,
      }}>
        <Box sx={{
          position: 'absolute',
          top: -100,
          right: -100,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16,185,129,0.15) 0%, transparent 70%)',
          animation: 'float 10s ease-in-out infinite',
        }} />
        <Box sx={{
          position: 'absolute',
          bottom: -150,
          left: -150,
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%)',
          animation: 'float 12s ease-in-out infinite',
          animationDelay: '2s',
        }} />
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(249,115,22,0.08) 0%, transparent 70%)',
          animation: 'float 14s ease-in-out infinite',
          animationDelay: '4s',
        }} />
      </Box>

      {/* Header */}
      <Fade in={mounted} timeout={800}>
        <Box sx={{ 
          p: 2.5, 
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          background: 'rgba(15,23,42,0.8)',
          backdropFilter: 'blur(20px)',
          position: 'relative',
          zIndex: 10,
        }}>
          <IconButton 
            onClick={() => navigate('/')} 
            size="small" 
            sx={{ 
              color: 'rgba(255,255,255,0.7)',
              bgcolor: 'rgba(255,255,255,0.05)',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)', color: '#fff' },
            }}
          >
            <ArrowBackIcon />
          </IconButton>
          
          <Avatar sx={{ 
            width: 48,
            height: 48,
            background: `linear-gradient(135deg, ${getModeColor(mode)} 0%, ${alpha(getModeColor(mode), 0.7)} 100%)`,
            boxShadow: `0 4px 20px ${alpha(getModeColor(mode), 0.4)}`,
          }}>
            {getModeIcon(mode)}
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" sx={{ 
              fontWeight: 700, 
              background: `linear-gradient(135deg, ${getModeColor(mode)} 0%, #fff 100%)`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              Clinical Assistant
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              {modes.map((m) => (
                <Chip 
                  key={m.id}
                  label={m.label}
                  size="small" 
                  icon={m.icon}
                  onClick={() => setMode(m.id as any)}
                  sx={{ 
                    cursor: 'pointer',
                    bgcolor: mode === m.id ? alpha(getModeColor(m.id), 0.2) : 'rgba(255,255,255,0.05)',
                    color: mode === m.id ? getModeColor(m.id) : 'rgba(255,255,255,0.6)',
                    border: `1px solid ${mode === m.id ? alpha(getModeColor(m.id), 0.4) : 'rgba(255,255,255,0.1)'}`,
                    fontWeight: mode === m.id ? 600 : 400,
                    '& .MuiChip-icon': { color: mode === m.id ? getModeColor(m.id) : 'rgba(255,255,255,0.5)' },
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      bgcolor: alpha(getModeColor(m.id), 0.15),
                      border: `1px solid ${alpha(getModeColor(m.id), 0.3)}`,
                    },
                  }}
                />
              ))}
            </Box>
          </Box>

          {/* Mode indicators */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(16,185,129,0.2)' }}>
              <HealthAndSafetyIcon sx={{ fontSize: 18, color: '#10B981' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(139,92,246,0.2)' }}>
              <MonitorHeartIcon sx={{ fontSize: 18, color: '#8B5CF6' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(249,115,22,0.2)' }}>
              <VaccinesIcon sx={{ fontSize: 18, color: '#F97316' }} />
            </Avatar>
          </Box>
        </Box>
      </Fade>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 3, position: 'relative', zIndex: 1 }}>
        {messages.length === 0 ? (
          <Fade in={mounted} timeout={1000}>
            <Box sx={{ 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Zoom in={mounted} timeout={1200}>
                <Avatar sx={{ 
                  width: 100, 
                  height: 100, 
                  mb: 3,
                  background: `linear-gradient(135deg, ${getModeColor(mode)} 0%, ${alpha(getModeColor(mode), 0.7)} 100%)`,
                  boxShadow: `0 12px 48px ${alpha(getModeColor(mode), 0.4)}`,
                  animation: 'pulse 3s ease-in-out infinite',
                }}>
                  <AutoAwesomeIcon sx={{ fontSize: 50 }} />
                </Avatar>
              </Zoom>
              
              <Typography variant="h3" sx={{ 
                mb: 1.5, 
                fontWeight: 700, 
                color: '#fff',
                textAlign: 'center',
              }}>
                How can I assist with your medical query today?
              </Typography>
              
              <Typography variant="body1" sx={{ 
                color: 'rgba(255,255,255,0.6)', 
                textAlign: 'center', 
                maxWidth: 600, 
                lineHeight: 1.8,
                mb: 4,
              }}>
                {mode === 'qa' && 'Ask about patient conditions, treatment options, drug interactions, or clinical guidelines. Our AI agents provide evidence-based medical information.'}
                {mode === 'research' && 'Request comprehensive medical research on any topic with evidence-based analysis and peer-reviewed sources.'}
                {mode === 'clinical' && 'Describe a clinical scenario or upload medical images for AI-powered decision support and analysis.'}
              </Typography>

              {/* Quick suggestions */}
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 700 }}>
                {(mode === 'clinical' 
                  ? ['Skin rash analysis', 'X-ray interpretation', 'Wound assessment', 'Symptom analysis']
                  : mode === 'research'
                  ? ['Latest diabetes research', 'COVID-19 updates', 'Cancer treatment advances', 'Mental health studies']
                  : ['Common cold symptoms', 'Drug interactions', 'Vaccination schedule', 'Emergency signs']
                ).map((suggestion, i) => (
                  <Zoom in={mounted} timeout={1400 + i * 100} key={suggestion}>
                    <Chip
                      label={suggestion}
                      onClick={() => setInput(suggestion)}
                      sx={{ 
                        cursor: 'pointer',
                        bgcolor: alpha(getModeColor(mode), 0.1),
                        color: getModeColor(mode),
                        border: `1px solid ${alpha(getModeColor(mode), 0.3)}`,
                        fontWeight: 500,
                        transition: 'all 0.3s ease',
                        '&:hover': { 
                          bgcolor: alpha(getModeColor(mode), 0.2),
                          transform: 'translateY(-2px)',
                          boxShadow: `0 4px 12px ${alpha(getModeColor(mode), 0.3)}`,
                        },
                      }}
                    />
                  </Zoom>
                ))}
              </Box>
            </Box>
          </Fade>
        ) : (
          <Box sx={{ maxWidth: 900, mx: 'auto' }}>
            {messages.map((message, index) => (
              <Fade in timeout={500} key={index}>
                <Paper 
                  sx={{ 
                    mb: 2.5, 
                    p: 3,
                    bgcolor: message.role === 'user' 
                      ? alpha(getModeColor(mode), 0.1) 
                      : 'rgba(255,255,255,0.03)',
                    border: '1px solid',
                    borderColor: message.role === 'user' 
                      ? alpha(getModeColor(mode), 0.3) 
                      : 'rgba(255,255,255,0.08)',
                    borderRadius: 3,
                    backdropFilter: 'blur(10px)',
                    boxShadow: message.role === 'assistant' 
                      ? `0 4px 24px rgba(0,0,0,0.3)` 
                      : 'none',
                  }}
                >
                  {message.image && (
                    <Box sx={{ mb: 2, borderRadius: 2, overflow: 'hidden', maxHeight: 300 }}>
                      <img 
                        src={message.image} 
                        alt="Uploaded medical image" 
                        style={{ width: '100%', height: 'auto', objectFit: 'contain' }} 
                      />
                    </Box>
                  )}
                  <Box sx={{ 
                    '& h1': { fontSize: '1.5rem', fontWeight: 700, mb: 1, color: 'rgba(255,255,255,0.95)' },
                    '& h2': { fontSize: '1.25rem', fontWeight: 600, mt: 2, mb: 1, color: 'rgba(255,255,255,0.9)' },
                    '& h3': { fontSize: '1.1rem', fontWeight: 600, mt: 1.5, mb: 0.5, color: 'rgba(255,255,255,0.85)' },
                    '& p': { mb: 1, lineHeight: 1.7 },
                    '& ul, & ol': { pl: 3, mb: 1 },
                    '& li': { mb: 0.5 },
                    '& strong': { fontWeight: 600, color: '#10B981' },
                  }}>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </Box>
                  {message.metadata && (
                    <Box sx={{ mt: 2.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {message.metadata.urgency && (
                        <Chip 
                          icon={<WarningIcon />}
                          label={`Urgency: ${message.metadata.urgency}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha(getUrgencyColor(message.metadata.urgency), 0.2),
                            color: getUrgencyColor(message.metadata.urgency),
                            border: `1px solid ${alpha(getUrgencyColor(message.metadata.urgency), 0.4)}`,
                            fontWeight: 600,
                          }}
                        />
                      )}
                      {message.metadata.specialty && (
                        <Chip 
                          label={`Specialty: ${message.metadata.specialty}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha(getModeColor(mode), 0.15),
                            color: getModeColor(mode),
                            border: `1px solid ${alpha(getModeColor(mode), 0.3)}`,
                          }}
                        />
                      )}
                      {message.metadata.completed_steps && message.metadata.completed_steps.length > 0 && (
                        <Chip 
                          icon={<CheckCircleIcon />}
                          label={`${message.metadata.completed_steps.length} steps completed`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#10B981', 0.2),
                            color: '#10B981',
                            border: `1px solid ${alpha('#10B981', 0.4)}`,
                            fontWeight: 500,
                          }}
                        />
                      )}
                    </Box>
                  )}
                </Paper>
              </Fade>
            ))}
            {loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                <CircularProgress size={24} sx={{ color: getModeColor(mode) }} />
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                  Analyzing your medical query...
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </Box>

      {/* Input */}
      <Fade in={mounted} timeout={1200}>
        <Box sx={{ 
          p: 2.5, 
          borderTop: '1px solid rgba(255,255,255,0.08)',
          background: 'rgba(15,23,42,0.9)',
          backdropFilter: 'blur(20px)',
          position: 'relative',
          zIndex: 10,
        }}>
          <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
            {/* Image upload area for clinical mode */}
            {mode === 'clinical' && (
              <Box
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                sx={{
                  mb: 2,
                  p: 3,
                  border: '2px dashed',
                  borderColor: isDragging ? getModeColor(mode) : alpha('#F97316', 0.3),
                  borderRadius: 3,
                  bgcolor: isDragging ? alpha('#F97316', 0.1) : 'rgba(255,255,255,0.02)',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    borderColor: getModeColor(mode),
                    bgcolor: alpha('#F97316', 0.08),
                  },
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileInputChange}
                  style={{ display: 'none' }}
                />
                {selectedImage ? (
                  <Box sx={{ position: 'relative' }}>
                    <img 
                      src={selectedImage} 
                      alt="Selected medical image" 
                      style={{ 
                        maxHeight: 200, 
                        width: '100%', 
                        objectFit: 'contain', 
                        borderRadius: 8 
                      }} 
                    />
                    <IconButton
                      onClick={(e) => { e.stopPropagation(); clearImage(); }}
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        bgcolor: 'rgba(0,0,0,0.6)',
                        color: 'white',
                        '&:hover': { bgcolor: 'rgba(0,0,0,0.8)' },
                      }}
                      size="small"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center' }}>
                    <CloudUploadIcon sx={{ fontSize: 48, color: alpha('#F97316', 0.6), mb: 1 }} />
                    <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>
                      Drag & drop a medical image here, or click to select
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.4)', mt: 0.5 }}>
                      Supports X-rays, skin conditions, wounds, lab results (JPEG, PNG, WebP)
                    </Typography>
                  </Box>
                )}
              </Box>
            )}

            <Box sx={{ 
              display: 'flex', 
              gap: 1.5,
            }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder={
                  mode === 'qa' ? 'Describe the clinical scenario or question...' :
                  mode === 'research' ? 'Enter your research question...' :
                  (selectedImage ? 'Add a description or ask a question about the image...' : 'Describe patient history, examination findings, or upload an image...')
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={loading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'rgba(255,255,255,0.05)',
                    color: '#fff',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 2,
                    '&:hover': {
                      border: `1px solid ${alpha(getModeColor(mode), 0.3)}`,
                    },
                    '&.Mui-focused': {
                      border: `1px solid ${getModeColor(mode)}`,
                      boxShadow: `0 0 0 3px ${alpha(getModeColor(mode), 0.2)}`,
                    },
                    '& fieldset': { border: 'none' },
                  },
                  '& .MuiInputBase-input::placeholder': {
                    color: 'rgba(255,255,255,0.4)',
                  },
                }}
              />
              <Button 
                variant="contained"
                onClick={handleSend}
                disabled={loading || (!input.trim() && !selectedImage)}
                sx={{ 
                  minWidth: 56,
                  height: 56,
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${getModeColor(mode)} 0%, ${alpha(getModeColor(mode), 0.7)} 100%)`,
                  boxShadow: `0 4px 20px ${alpha(getModeColor(mode), 0.4)}`,
                  '&:hover': {
                    boxShadow: `0 6px 24px ${alpha(getModeColor(mode), 0.5)}`,
                  },
                  '&:disabled': {
                    bgcolor: 'rgba(255,255,255,0.1)',
                    color: 'rgba(255,255,255,0.3)',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
              </Button>
            </Box>
          </Box>
        </Box>
      </Fade>

      {/* CSS Animations */}
      <style>
        {`
          @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-30px) rotate(5deg); }
          }
          @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
          }
        `}
      </style>
    </Box>
  )
}
