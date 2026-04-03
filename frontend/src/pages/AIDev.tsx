import { Box, Typography, TextField, Button, Paper, CircularProgress, IconButton, alpha, Chip, FormControl, InputLabel, Select, MenuItem, Avatar, Fade, Zoom, useTheme } from '@mui/material'
import ReactMarkdown from 'react-markdown'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import SendIcon from '@mui/icons-material/Send'
import CodeIcon from '@mui/icons-material/Code'
import BugReportIcon from '@mui/icons-material/BugReport'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import WarningIcon from '@mui/icons-material/Warning'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import TerminalIcon from '@mui/icons-material/Terminal'
import BuildIcon from '@mui/icons-material/Build'
import NewspaperIcon from '@mui/icons-material/Newspaper'
import ArchitectureIcon from '@mui/icons-material/Architecture'
import IntegrationInstructionsIcon from '@mui/icons-material/IntegrationInstructions'
import { api } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: {
    language?: string
    generated_code?: string
    review_approved?: boolean
    review_iteration?: number
    issues?: string[]
    completed_steps?: string[]
  }
}

export default function AIDev() {
  const navigate = useNavigate()
  const theme = useTheme()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'generate' | 'review' | 'debug' | 'news'>('generate')
  const [mounted, setMounted] = useState(false)
  
  // Code generation form state
  const [language, setLanguage] = useState('python')
  const [constraints, setConstraints] = useState('')

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSend = async () => {
    if ((!input.trim() && mode !== 'news') || loading) return

    const userMessage: Message = { 
      role: 'user', 
      content: mode === 'generate' 
        ? `Generate ${language} code: ${input}${constraints ? `\nConstraints: ${constraints}` : ''}`
        : mode === 'review' ? `Review code: ${input}`
        : mode === 'debug' ? `Debug code: ${input}`
        : 'Show latest coding news', 
      timestamp: new Date() 
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      let response
      if (mode === 'generate') {
        response = await api.codingGenerate(input, language, constraints ? constraints.split('\n') : [])
      } else if (mode === 'review') {
        response = await api.codingReview(input, language)
      } else if (mode === 'debug') {
        response = await api.codingDebug(input, language)
      } else {
        response = await api.codingNews()
      }

      const formatCodingResponse = (data: any) => {
        if (!data) return 'Unable to process your request'
        
        let content = `# Generated ${data.language || 'Code'}\n\n`
        content += `## Description\n${data.description || 'Code generation request'}\n\n`
        content += `## Code\n\`\`\`${data.language || 'text'}\n${data.generated_code || ''}\n\`\`\`\n\n`
        content += `## Explanation\n${data.code_explanation || 'Code generated successfully'}\n`
        
        if (data.issues && data.issues.length > 0) {
          content += `\n## Issues Resolved\n`
          data.issues.forEach((issue: string) => {
            content += `- ${issue}\n`
          })
        }
        
        if (data.suggestions && data.suggestions.length > 0) {
          content += `\n## Suggestions\n`
          data.suggestions.forEach((suggestion: string) => {
            content += `- ${suggestion}\n`
          })
        }
        
        return content
      }

      const assistantMessage: Message = { 
        role: 'assistant', 
        content: response.success && response.data 
          ? response.data.final_output || formatCodingResponse(response.data)
          : response.error || 'Unable to process your request',
        timestamp: new Date(),
        metadata: response.success && response.data ? {
          language: (response.data as any).language,
          generated_code: (response.data as any).generated_code,
          review_approved: (response.data as any).review_approved,
          review_iteration: (response.data as any).review_iteration,
          issues: (response.data as any).issues,
          completed_steps: (response.data as any).completed_steps
        } : undefined
      }
      setMessages(prev => [...prev, assistantMessage])
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
      case 'generate': return '#8B5CF6'
      case 'review': return '#3B82F6'
      case 'debug': return '#F59E0B'
      case 'news': return '#10B981'
      default: return '#8B5CF6'
    }
  }

  const modes = [
    { id: 'generate', label: 'Generate Code', icon: <CodeIcon />, desc: 'AI code generation' },
    { id: 'review', label: 'Review Code', icon: <IntegrationInstructionsIcon />, desc: 'Code review & best practices' },
    { id: 'debug', label: 'Debug Code', icon: <BugReportIcon />, desc: 'Debug & fix issues' },
    { id: 'news', label: 'Coding News', icon: <NewspaperIcon />, desc: 'Latest dev trends' },
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
          background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)',
          animation: 'float 10s ease-in-out infinite',
        }} />
        <Box sx={{
          position: 'absolute',
          bottom: -150,
          left: -150,
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%)',
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
          background: 'radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 70%)',
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
          background: 'rgba(15,10,26,0.8)',
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
            {mode === 'generate' ? <CodeIcon /> : mode === 'review' ? <IntegrationInstructionsIcon /> : mode === 'debug' ? <BugReportIcon /> : <NewspaperIcon />}
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" sx={{ 
              fontWeight: 700, 
              background: `linear-gradient(135deg, ${getModeColor(mode)} 0%, #fff 100%)`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              AI Dev Assistant
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
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

          {/* Dev icons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(139,92,246,0.2)' }}>
              <TerminalIcon sx={{ fontSize: 18, color: '#8B5CF6' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(59,130,246,0.2)' }}>
              <BuildIcon sx={{ fontSize: 18, color: '#3B82F6' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(16,185,129,0.2)' }}>
              <ArchitectureIcon sx={{ fontSize: 18, color: '#10B981' }} />
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
                How can I assist with your coding questions today?
              </Typography>
              
              <Typography variant="body1" sx={{ 
                color: 'rgba(255,255,255,0.6)', 
                textAlign: 'center', 
                maxWidth: 600, 
                lineHeight: 1.8,
                mb: 4,
              }}>
                {mode === 'generate' && 'Describe what code you need and our AI agents will generate production-ready code with best practices.'}
                {mode === 'review' && 'Paste your code and our AI agents will review it for best practices, security issues, and improvements.'}
                {mode === 'debug' && 'Paste your code and error message and our AI agents will help debug and fix the issues.'}
                {mode === 'news' && 'Get the latest coding news, development trends, and technology updates curated by our AI.'}
              </Typography>

              {/* Quick suggestions */}
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 700 }}>
                {(mode === 'generate' 
                  ? ['REST API endpoint', 'React component', 'Python class', 'Database schema']
                  : mode === 'review'
                  ? ['Security audit', 'Performance review', 'Code style check', 'Best practices']
                  : mode === 'debug'
                  ? ['TypeError fix', 'Import error', 'Logic bug', 'Performance issue']
                  : ['Tech trends', 'Framework updates', 'Language news', 'Open source']
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
                  <Box sx={{ 
                    '& h1': { fontSize: '1.5rem', fontWeight: 700, mb: 1, color: 'rgba(255,255,255,0.95)' },
                    '& h2': { fontSize: '1.25rem', fontWeight: 600, mt: 2, mb: 1, color: 'rgba(255,255,255,0.9)' },
                    '& h3': { fontSize: '1.1rem', fontWeight: 600, mt: 1.5, mb: 0.5, color: 'rgba(255,255,255,0.85)' },
                    '& p': { mb: 1, lineHeight: 1.7 },
                    '& ul, & ol': { pl: 3, mb: 1 },
                    '& li': { mb: 0.5 },
                    '& code': { 
                      bgcolor: 'rgba(0,0,0,0.4)', 
                      px: 0.75, 
                      py: 0.25, 
                      borderRadius: 1, 
                      fontFamily: 'monospace',
                      fontSize: '0.85em',
                    },
                    '& pre': {
                      bgcolor: 'rgba(0,0,0,0.5)',
                      p: 2,
                      borderRadius: 2,
                      overflow: 'auto',
                      maxHeight: 400,
                      '& code': { bgcolor: 'transparent', p: 0 },
                    },
                    '& strong': { fontWeight: 600, color: '#8B5CF6' },
                  }}>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </Box>
                  {message.metadata && (
                    <Box sx={{ mt: 2.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {message.metadata.language && (
                        <Chip 
                          label={`Language: ${message.metadata.language}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#8B5CF6', 0.2),
                            color: '#8B5CF6',
                            border: `1px solid ${alpha('#8B5CF6', 0.4)}`,
                            fontWeight: 600,
                          }}
                        />
                      )}
                      {message.metadata.review_approved !== undefined && (
                        <Chip 
                          icon={message.metadata.review_approved ? <CheckCircleIcon /> : <WarningIcon />}
                          label={message.metadata.review_approved ? 'Approved' : 'Issues Found'}
                          size="small"
                          sx={{ 
                            bgcolor: message.metadata.review_approved ? alpha('#10B981', 0.2) : alpha('#F59E0B', 0.2),
                            color: message.metadata.review_approved ? '#10B981' : '#F59E0B',
                            border: `1px solid ${message.metadata.review_approved ? alpha('#10B981', 0.4) : alpha('#F59E0B', 0.4)}`,
                            fontWeight: 500,
                          }}
                        />
                      )}
                      {message.metadata.review_iteration !== undefined && (
                        <Chip 
                          label={`Iteration: ${message.metadata.review_iteration}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#3B82F6', 0.15),
                            color: '#3B82F6',
                            border: `1px solid ${alpha('#3B82F6', 0.3)}`,
                          }}
                        />
                      )}
                      {message.metadata.issues && message.metadata.issues.length > 0 && (
                        <Chip 
                          icon={<BugReportIcon />}
                          label={`${message.metadata.issues.length} issues found`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#EF4444', 0.2),
                            color: '#EF4444',
                            border: `1px solid ${alpha('#EF4444', 0.4)}`,
                            fontWeight: 500,
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
                  {message.metadata?.generated_code && (
                    <Paper 
                      sx={{ 
                        mt: 2, 
                        p: 2, 
                        bgcolor: 'rgba(0,0,0,0.4)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 2,
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        overflow: 'auto',
                        maxHeight: 300,
                      }}
                    >
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: 'rgba(255,255,255,0.9)' }}>
                        {message.metadata.generated_code}
                      </pre>
                    </Paper>
                  )}
                </Paper>
              </Fade>
            ))}
            {loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                <CircularProgress size={24} sx={{ color: getModeColor(mode) }} />
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                  Processing your request...
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
          background: 'rgba(15,10,26,0.9)',
          backdropFilter: 'blur(20px)',
          position: 'relative',
          zIndex: 10,
        }}>
          {mode === 'generate' ? (
            <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 2.5 }}>
                <FormControl size="medium">
                  <InputLabel sx={{ color: 'rgba(255,255,255,0.6)', '&.Mui-focused': { color: '#8B5CF6' } }}>Language</InputLabel>
                  <Select
                    value={language}
                    label="Language"
                    onChange={(e) => setLanguage(e.target.value)}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#8B5CF6', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #8B5CF6` },
                      '& fieldset': { border: 'none' },
                      '& .MuiSelect-icon': { color: 'rgba(255,255,255,0.6)' },
                    }}
                  >
                    <MenuItem value="python">Python</MenuItem>
                    <MenuItem value="javascript">JavaScript</MenuItem>
                    <MenuItem value="typescript">TypeScript</MenuItem>
                    <MenuItem value="java">Java</MenuItem>
                    <MenuItem value="cpp">C++</MenuItem>
                    <MenuItem value="go">Go</MenuItem>
                    <MenuItem value="rust">Rust</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  label="Constraints (optional)"
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                  size="medium"
                  placeholder="e.g., Use recursion, Add error handling"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#8B5CF6', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #8B5CF6`, boxShadow: `0 0 0 3px ${alpha('#8B5CF6', 0.2)}` },
                      '& fieldset': { border: 'none' },
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.6)' },
                    '& .MuiInputLabel-root.Mui-focused': { color: '#8B5CF6' },
                    '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.4)' },
                  }}
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 1.5 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder="Describe the code you need..."
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
                  disabled={loading || !input.trim()}
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
          ) : (
            <Box sx={{ 
              display: 'flex', 
              gap: 1.5, 
              maxWidth: 1000, 
              mx: 'auto',
            }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder={
                  mode === 'review' ? 'Paste your code for review...' :
                  mode === 'debug' ? 'Paste your code and error message...' :
                  'Click to get latest coding news...'
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={loading || mode === 'news'}
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
                disabled={loading || (mode !== 'news' && !input.trim())}
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
