import { Box, Typography, TextField, Button, Paper, CircularProgress, IconButton, alpha, Chip, FormControl, InputLabel, Select, MenuItem, Avatar, Fade, Zoom, useTheme } from '@mui/material'
import ReactMarkdown from 'react-markdown'
import { useState, useRef, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import SendIcon from '@mui/icons-material/Send'
import CheckroomIcon from '@mui/icons-material/Checkroom'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import StyleIcon from '@mui/icons-material/Style'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import DeleteIcon from '@mui/icons-material/Delete'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import DiamondIcon from '@mui/icons-material/Diamond'
import PaletteIcon from '@mui/icons-material/Palette'
import StarIcon from '@mui/icons-material/Star'
import FavoriteIcon from '@mui/icons-material/Favorite'
import { api } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  image?: string
  metadata?: {
    items_detected?: string[]
    style?: string
    colors?: string[]
    occasion_fit?: string
    suggestions?: string[]
    completed_steps?: string[]
  }
}

export default function Fashion() {
  const navigate = useNavigate()
  const theme = useTheme()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'analyze' | 'trends' | 'recommend'>('analyze')
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [mounted, setMounted] = useState(false)
  
  // Recommendation form state
  const [budget, setBudget] = useState(200)
  const [occasion, setOccasion] = useState('casual')
  const [time, setTime] = useState('day')
  const [location, setLocation] = useState('Lagos')

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
    if ((!input.trim() && mode !== 'trends' && !selectedImage) || loading) return

    const userMessage: Message = { 
      role: 'user', 
      content: mode === 'recommend' 
        ? `Outfit recommendation for ${occasion} occasion, ${time} time, ${location}, budget $${budget}`
        : mode === 'trends' ? 'Show me current fashion trends' : input, 
      timestamp: new Date(),
      image: selectedImage || undefined
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      let response
      if (mode === 'analyze') {
        if (selectedFile) {
          const formData = new FormData()
          formData.append('image', selectedFile)
          formData.append('query', input || 'Analyze this outfit')
          response = await api.fashionAnalyzeImage(formData)
        } else {
          response = await api.fashionAnalyze(input)
        }
      } else if (mode === 'trends') {
        response = await api.fashionTrends()
      } else {
        response = await api.fashionRecommend(budget, occasion, time, location)
      }

      const formatFashionResponse = (data: any, mode: string) => {
        if (!data) return 'Unable to process your request'
        
        if (mode === 'analyze' && data.outfit_analysis) {
          const analysis = data.outfit_analysis
          let content = `## Outfit Analysis\n\n`
          
          if (analysis.style) {
            content += `**Style:** ${analysis.style}\n\n`
          }
          
          if (analysis.occasion_fit) {
            content += `**Occasion Fit:** ${analysis.occasion_fit}\n\n`
          }
          
          if (analysis.items_detected && analysis.items_detected.length > 0) {
            content += `### Items Detected\n`
            analysis.items_detected.forEach((item: string) => {
              content += `- ${item}\n`
            })
            content += '\n'
          }
          
          if (analysis.colors && analysis.colors.length > 0) {
            content += `### Color Palette\n`
            analysis.colors.forEach((color: string) => {
              content += `- ${color}\n`
            })
            content += '\n'
          }
          
          if (analysis.suggestions && analysis.suggestions.length > 0) {
            content += `### Suggestions\n`
            analysis.suggestions.forEach((suggestion: string) => {
              content += `- ${suggestion}\n`
            })
          }
          
          return content
        }
        
        if (mode === 'trends' && data.style_trend) {
          const trend = data.style_trend
          let content = `## Fashion Trends\n\n`
          
          if (trend.current_trends && trend.current_trends.length > 0) {
            content += `### Current Trends\n`
            trend.current_trends.forEach((t: string) => {
              content += `- ${t}\n`
            })
            content += '\n'
          }
          
          if (trend.trending_colors && trend.trending_colors.length > 0) {
            content += `### Trending Colors\n`
            trend.trending_colors.forEach((color: string) => {
              content += `- ${color}\n`
            })
            content += '\n'
          }
          
          if (trend.trending_styles && trend.trending_styles.length > 0) {
            content += `### Trending Styles\n`
            trend.trending_styles.forEach((style: string) => {
              content += `- ${style}\n`
            })
          }
          
          return content
        }
        
        if (mode === 'recommend' && data.outfit_recommendation) {
          const rec = data.outfit_recommendation
          let content = `## Outfit Recommendation\n\n`
          
          if (rec.recommended_items && rec.recommended_items.length > 0) {
            content += `### Recommended Items\n`
            rec.recommended_items.forEach((item: string) => {
              content += `- ${item}\n`
            })
            content += '\n'
          }
          
          if (rec.style_notes) {
            content += `### Style Notes\n${rec.style_notes}\n\n`
          }
          
          if (rec.estimated_cost) {
            content += `**Estimated Cost:** $${rec.estimated_cost.toFixed(2)}\n\n`
          }
          
          if (rec.trend_alignment) {
            content += `**Trend Alignment:** ${rec.trend_alignment}\n`
          }
          
          return content
        }
        
        return 'Analysis completed'
      }

      const assistantMessage: Message = { 
        role: 'assistant', 
        content: response.success && response.data 
          ? response.data.final_output || formatFashionResponse(response.data, mode)
          : response.error || 'Unable to process your request',
        timestamp: new Date(),
        metadata: response.success && response.data ? {
          items_detected: (response.data as any).outfit_analysis?.items_detected,
          style: (response.data as any).outfit_analysis?.style,
          colors: (response.data as any).outfit_analysis?.colors,
          occasion_fit: (response.data as any).outfit_analysis?.occasion_fit,
          suggestions: (response.data as any).outfit_analysis?.suggestions,
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

  const getModeColor = (m: string) => {
    switch (m) {
      case 'analyze': return '#EC4899'
      case 'trends': return '#A855F7'
      case 'recommend': return '#F59E0B'
      default: return '#EC4899'
    }
  }

  const modes = [
    { id: 'analyze', label: 'Analyze Outfit', icon: <StyleIcon />, desc: 'Style analysis & suggestions' },
    { id: 'trends', label: 'Trends', icon: <TrendingUpIcon />, desc: 'Latest fashion trends' },
    { id: 'recommend', label: 'Get Recommendation', icon: <StarIcon />, desc: 'Personalized recommendations' },
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
          background: 'radial-gradient(circle, rgba(236,72,153,0.15) 0%, transparent 70%)',
          animation: 'float 10s ease-in-out infinite',
        }} />
        <Box sx={{
          position: 'absolute',
          bottom: -150,
          left: -150,
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(168,85,247,0.1) 0%, transparent 70%)',
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
          background: 'radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%)',
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
          background: 'rgba(26,10,31,0.8)',
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
            {mode === 'analyze' ? <StyleIcon /> : mode === 'trends' ? <TrendingUpIcon /> : <StarIcon />}
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" sx={{ 
              fontWeight: 700, 
              background: `linear-gradient(135deg, ${getModeColor(mode)} 0%, #fff 100%)`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              Fashion Assistant
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

          {/* Fashion icons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(236,72,153,0.2)' }}>
              <DiamondIcon sx={{ fontSize: 18, color: '#EC4899' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(168,85,247,0.2)' }}>
              <PaletteIcon sx={{ fontSize: 18, color: '#A855F7' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(245,158,11,0.2)' }}>
              <FavoriteIcon sx={{ fontSize: 18, color: '#F59E0B' }} />
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
                How can I assist with your fashion questions today?
              </Typography>
              
              <Typography variant="body1" sx={{ 
                color: 'rgba(255,255,255,0.6)', 
                textAlign: 'center', 
                maxWidth: 600, 
                lineHeight: 1.8,
                mb: 4,
              }}>
                {mode === 'analyze' && 'Upload an outfit image or describe it for AI-powered style analysis and personalized suggestions.'}
                {mode === 'trends' && 'Get the latest fashion trends and style insights curated by our AI fashion experts.'}
                {mode === 'recommend' && 'Fill in your details below to get personalized outfit recommendations tailored to your style.'}
              </Typography>

              {/* Quick suggestions */}
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 700 }}>
                {(mode === 'analyze' 
                  ? ['Casual streetwear', 'Formal business attire', 'Evening cocktail dress', 'Summer beach outfit']
                  : mode === 'trends'
                  ? ['Spring 2024 trends', 'Sustainable fashion', 'Color of the year', 'Accessory trends']
                  : ['Wedding guest outfit', 'Office wear', 'Date night look', 'Weekend casual']
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
                        alt="Uploaded outfit" 
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
                    '& strong': { fontWeight: 600, color: '#EC4899' },
                  }}>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </Box>
                  {message.metadata && (
                    <Box sx={{ mt: 2.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {message.metadata.style && (
                        <Chip 
                          icon={<StyleIcon />}
                          label={`Style: ${message.metadata.style}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#EC4899', 0.2),
                            color: '#EC4899',
                            border: `1px solid ${alpha('#EC4899', 0.4)}`,
                            fontWeight: 600,
                          }}
                        />
                      )}
                      {message.metadata.occasion_fit && (
                        <Chip 
                          label={`Occasion: ${message.metadata.occasion_fit}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#A855F7', 0.15),
                            color: '#A855F7',
                            border: `1px solid ${alpha('#A855F7', 0.3)}`,
                          }}
                        />
                      )}
                      {message.metadata.colors && message.metadata.colors.length > 0 && (
                        <Chip 
                          label={`Colors: ${message.metadata.colors.join(', ')}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#F59E0B', 0.15),
                            color: '#F59E0B',
                            border: `1px solid ${alpha('#F59E0B', 0.3)}`,
                          }}
                        />
                      )}
                      {message.metadata.items_detected && message.metadata.items_detected.length > 0 && (
                        <Chip 
                          icon={<CheckCircleIcon />}
                          label={`${message.metadata.items_detected.length} items detected`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#10B981', 0.2),
                            color: '#10B981',
                            border: `1px solid ${alpha('#10B981', 0.4)}`,
                            fontWeight: 500,
                          }}
                        />
                      )}
                      {message.metadata.completed_steps && message.metadata.completed_steps.length > 0 && (
                        <Chip 
                          icon={<TrendingUpIcon />}
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
                  Analyzing your fashion query...
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
          background: 'rgba(26,10,31,0.9)',
          backdropFilter: 'blur(20px)',
          position: 'relative',
          zIndex: 10,
        }}>
          {mode === 'recommend' ? (
            <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 2.5 }}>
                <TextField
                  label="Budget ($)"
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#EC4899', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #EC4899`, boxShadow: `0 0 0 3px ${alpha('#EC4899', 0.2)}` },
                      '& fieldset': { border: 'none' },
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.6)' },
                    '& .MuiInputLabel-root.Mui-focused': { color: '#EC4899' },
                  }}
                />
                <FormControl size="medium">
                  <InputLabel sx={{ color: 'rgba(255,255,255,0.6)', '&.Mui-focused': { color: '#EC4899' } }}>Occasion</InputLabel>
                  <Select
                    value={occasion}
                    label="Occasion"
                    onChange={(e) => setOccasion(e.target.value)}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#EC4899', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #EC4899` },
                      '& fieldset': { border: 'none' },
                      '& .MuiSelect-icon': { color: 'rgba(255,255,255,0.6)' },
                    }}
                  >
                    <MenuItem value="casual">Casual</MenuItem>
                    <MenuItem value="formal">Formal</MenuItem>
                    <MenuItem value="business">Business</MenuItem>
                    <MenuItem value="party">Party</MenuItem>
                    <MenuItem value="wedding">Wedding</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="medium">
                  <InputLabel sx={{ color: 'rgba(255,255,255,0.6)', '&.Mui-focused': { color: '#EC4899' } }}>Time of Day</InputLabel>
                  <Select
                    value={time}
                    label="Time of Day"
                    onChange={(e) => setTime(e.target.value)}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#EC4899', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #EC4899` },
                      '& fieldset': { border: 'none' },
                      '& .MuiSelect-icon': { color: 'rgba(255,255,255,0.6)' },
                    }}
                  >
                    <MenuItem value="day">Day</MenuItem>
                    <MenuItem value="evening">Evening</MenuItem>
                    <MenuItem value="night">Night</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  label="Location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#EC4899', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #EC4899`, boxShadow: `0 0 0 3px ${alpha('#EC4899', 0.2)}` },
                      '& fieldset': { border: 'none' },
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.6)' },
                    '& .MuiInputLabel-root.Mui-focused': { color: '#EC4899' },
                  }}
                />
              </Box>
              <Button 
                variant="contained"
                onClick={handleSend}
                disabled={loading}
                fullWidth
                size="large"
                sx={{
                  py: 1.5,
                  background: 'linear-gradient(135deg, #EC4899 0%, #A855F7 100%)',
                  boxShadow: '0 4px 20px rgba(236,72,153,0.4)',
                  borderRadius: 2,
                  fontWeight: 600,
                  '&:hover': {
                    boxShadow: '0 6px 24px rgba(236,72,153,0.5)',
                  },
                  '&:disabled': {
                    bgcolor: 'rgba(255,255,255,0.1)',
                    color: 'rgba(255,255,255,0.3)',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Get Recommendation'}
              </Button>
            </Box>
          ) : (
            <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
              {/* Image upload area for analyze mode */}
              {mode === 'analyze' && (
                <Box
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  sx={{
                    mb: 2,
                    p: 3,
                    border: '2px dashed',
                    borderColor: isDragging ? getModeColor(mode) : alpha('#EC4899', 0.3),
                    borderRadius: 3,
                    bgcolor: isDragging ? alpha('#EC4899', 0.1) : 'rgba(255,255,255,0.02)',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: getModeColor(mode),
                      bgcolor: alpha('#EC4899', 0.08),
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
                        alt="Selected outfit" 
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
                      <CloudUploadIcon sx={{ fontSize: 48, color: alpha('#EC4899', 0.6), mb: 1 }} />
                      <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>
                        Drag & drop an outfit image here, or click to select
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.4)', mt: 0.5 }}>
                        Supports JPEG, PNG, WebP
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
                  placeholder={mode === 'analyze' ? 'Describe the outfit or ask a question...' : 'Click to get latest fashion trends...'}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={loading || mode === 'trends'}
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
                  disabled={loading || (mode !== 'trends' && !input.trim() && !selectedImage)}
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
          )}
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
