import { Box, Typography, TextField, Button, Paper, CircularProgress, IconButton, alpha, Chip, Avatar, Fade, Zoom, useTheme } from '@mui/material'
import ReactMarkdown from 'react-markdown'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import SendIcon from '@mui/icons-material/Send'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import WarningIcon from '@mui/icons-material/Warning'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ShowChartIcon from '@mui/icons-material/ShowChart'
import NewspaperIcon from '@mui/icons-material/Newspaper'
import SavingsIcon from '@mui/icons-material/Savings'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import PieChartIcon from '@mui/icons-material/PieChart'
import { api } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: {
    risk_level?: string
    risk_iteration?: number
    risk_resolved?: boolean
    completed_steps?: string[]
  }
}

export default function Finance() {
  const navigate = useNavigate()
  const theme = useTheme()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'qa' | 'investment' | 'news'>('qa')
  const [mounted, setMounted] = useState(false)
  
  // Investment form state
  const [age, setAge] = useState(30)
  const [salary, setSalary] = useState(75000)
  const [occupation, setOccupation] = useState('Software Engineer')
  const [targetFund, setTargetFund] = useState(500000)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSend = async () => {
    if ((!input.trim() && mode !== 'investment') || loading) return

    const userMessage: Message = { 
      role: 'user', 
      content: mode === 'investment' 
        ? `Investment plan for ${occupation}, age ${age}, salary $${salary.toLocaleString()}, target $${targetFund.toLocaleString()}`
        : input, 
      timestamp: new Date() 
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      let response
      if (mode === 'qa') {
        response = await api.financeQA(input)
      } else if (mode === 'investment') {
        response = await api.financeInvestment({
          age,
          salary,
          occupation,
          target_fund: targetFund
        })
      } else {
        response = await api.financeNews()
      }

      const formatFinanceResponse = (data: any, mode: string) => {
        if (!data) return 'Unable to process your request'
        
        if (mode === 'investment' && data.investment_guide) {
          const guide = data.investment_guide
          let content = `## Investment Guide\n\n`
          
          if (guide.strategy) {
            content += `**Strategy:** ${guide.strategy}\n\n`
          }
          
          if (guide.allocations && Object.keys(guide.allocations).length > 0) {
            content += `### Asset Allocations\n`
            Object.entries(guide.allocations).forEach(([asset, percentage]) => {
              content += `- **${asset}:** ${percentage}%\n`
            })
            content += '\n'
          }
          
          if (guide.warnings && guide.warnings.length > 0) {
            content += `### Warnings\n`
            guide.warnings.forEach((warning: string) => {
              content += `- ${warning}\n`
            })
          }
          
          return content
        }
        
        if (mode === 'news' && data.news_report) {
          const report = data.news_report
          let content = `## Financial News\n\n`
          
          if (report.headlines && report.headlines.length > 0) {
            content += `### Headlines\n`
            report.headlines.forEach((headline: string) => {
              content += `- ${headline}\n`
            })
            content += '\n'
          }
          
          if (report.trends && report.trends.length > 0) {
            content += `### Market Trends\n`
            report.trends.forEach((trend: string) => {
              content += `- ${trend}\n`
            })
          }
          
          return content
        }
        
        return 'Financial analysis completed'
      }

      const assistantMessage: Message = { 
        role: 'assistant', 
        content: response.success && response.data 
          ? response.data.final_output || formatFinanceResponse(response.data, mode)
          : response.error || 'Unable to process your request',
        timestamp: new Date(),
        metadata: response.success && response.data ? {
          risk_level: (response.data as any).risk_resolved ? 'resolved' : 'pending',
          risk_iteration: (response.data as any).risk_iteration,
          risk_resolved: (response.data as any).risk_resolved,
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

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case 'resolved': return '#10B981'
      case 'high': return '#EF4444'
      case 'medium': return '#F59E0B'
      case 'low': return '#3B82F6'
      default: return '#6B7280'
    }
  }

  const getModeColor = (m: string) => {
    switch (m) {
      case 'qa': return '#3B82F6'
      case 'investment': return '#10B981'
      case 'news': return '#F59E0B'
      default: return '#3B82F6'
    }
  }

  const modes = [
    { id: 'qa', label: 'Financial Q&A', icon: <AccountBalanceIcon />, desc: 'Ask financial questions' },
    { id: 'investment', label: 'Investment Planning', icon: <SavingsIcon />, desc: 'Personalized investment plans' },
    { id: 'news', label: 'Market News', icon: <NewspaperIcon />, desc: 'Latest market updates' },
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
          background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
          animation: 'float 10s ease-in-out infinite',
        }} />
        <Box sx={{
          position: 'absolute',
          bottom: -150,
          left: -150,
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(16,185,129,0.1) 0%, transparent 70%)',
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
            {mode === 'qa' ? <AccountBalanceIcon /> : mode === 'investment' ? <SavingsIcon /> : <NewspaperIcon />}
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" sx={{ 
              fontWeight: 700, 
              background: `linear-gradient(135deg, ${getModeColor(mode)} 0%, #fff 100%)`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              Finance Assistant
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

          {/* Finance icons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(59,130,246,0.2)' }}>
              <ShowChartIcon sx={{ fontSize: 18, color: '#3B82F6' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(16,185,129,0.2)' }}>
              <AnalyticsIcon sx={{ fontSize: 18, color: '#10B981' }} />
            </Avatar>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(245,158,11,0.2)' }}>
              <PieChartIcon sx={{ fontSize: 18, color: '#F59E0B' }} />
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
                How can I assist with your financial questions today?
              </Typography>
              
              <Typography variant="body1" sx={{ 
                color: 'rgba(255,255,255,0.6)', 
                textAlign: 'center', 
                maxWidth: 600, 
                lineHeight: 1.8,
                mb: 4,
              }}>
                {mode === 'qa' && 'Ask about investment strategies, portfolio analysis, market trends, or financial planning. Our AI agents provide expert financial guidance.'}
                {mode === 'investment' && 'Fill in your details below to get a personalized investment plan tailored to your goals and risk tolerance.'}
                {mode === 'news' && 'Get the latest financial news and market updates curated by our AI agents.'}
              </Typography>

              {/* Quick suggestions */}
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 700 }}>
                {(mode === 'qa' 
                  ? ['Best retirement strategy', 'Stock market analysis', 'Cryptocurrency trends', 'Tax optimization']
                  : mode === 'investment'
                  ? ['Conservative portfolio', 'Growth strategy', 'Balanced approach', 'Aggressive growth']
                  : ['Market updates', 'Economic trends', 'Company earnings', 'Global markets']
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
                    '& strong': { fontWeight: 600, color: '#F59E0B' },
                  }}>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </Box>
                  {message.metadata && (
                    <Box sx={{ mt: 2.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {message.metadata.risk_level && (
                        <Chip 
                          icon={<WarningIcon />}
                          label={`Risk: ${message.metadata.risk_level}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha(getRiskColor(message.metadata.risk_level), 0.2),
                            color: getRiskColor(message.metadata.risk_level),
                            border: `1px solid ${alpha(getRiskColor(message.metadata.risk_level), 0.4)}`,
                            fontWeight: 600,
                          }}
                        />
                      )}
                      {message.metadata.risk_iteration !== undefined && (
                        <Chip 
                          label={`Iteration: ${message.metadata.risk_iteration}`}
                          size="small"
                          sx={{ 
                            bgcolor: alpha('#3B82F6', 0.15),
                            color: '#3B82F6',
                            border: `1px solid ${alpha('#3B82F6', 0.3)}`,
                          }}
                        />
                      )}
                      {message.metadata.risk_resolved !== undefined && (
                        <Chip 
                          icon={<CheckCircleIcon />}
                          label={message.metadata.risk_resolved ? 'Risk Resolved' : 'Risk Pending'}
                          size="small"
                          sx={{ 
                            bgcolor: message.metadata.risk_resolved ? alpha('#10B981', 0.2) : alpha('#F59E0B', 0.2),
                            color: message.metadata.risk_resolved ? '#10B981' : '#F59E0B',
                            border: `1px solid ${message.metadata.risk_resolved ? alpha('#10B981', 0.4) : alpha('#F59E0B', 0.4)}`,
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
                  Analyzing your financial query...
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
          {mode === 'investment' ? (
            <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 2.5 }}>
                <TextField
                  label="Age"
                  type="number"
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#10B981', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #10B981`, boxShadow: `0 0 0 3px ${alpha('#10B981', 0.2)}` },
                      '& fieldset': { border: 'none' },
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.6)' },
                    '& .MuiInputLabel-root.Mui-focused': { color: '#10B981' },
                  }}
                />
                <TextField
                  label="Annual Salary"
                  type="number"
                  value={salary}
                  onChange={(e) => setSalary(Number(e.target.value))}
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#10B981', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #10B981`, boxShadow: `0 0 0 3px ${alpha('#10B981', 0.2)}` },
                      '& fieldset': { border: 'none' },
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.6)' },
                    '& .MuiInputLabel-root.Mui-focused': { color: '#10B981' },
                  }}
                />
                <TextField
                  label="Occupation"
                  value={occupation}
                  onChange={(e) => setOccupation(e.target.value)}
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#10B981', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #10B981`, boxShadow: `0 0 0 3px ${alpha('#10B981', 0.2)}` },
                      '& fieldset': { border: 'none' },
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.6)' },
                    '& .MuiInputLabel-root.Mui-focused': { color: '#10B981' },
                  }}
                />
                <TextField
                  label="Target Fund"
                  type="number"
                  value={targetFund}
                  onChange={(e) => setTargetFund(Number(e.target.value))}
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.05)',
                      color: '#fff',
                      border: '1px solid rgba(255,255,255,0.1)',
                      '&:hover': { border: `1px solid ${alpha('#10B981', 0.3)}` },
                      '&.Mui-focused': { border: `1px solid #10B981`, boxShadow: `0 0 0 3px ${alpha('#10B981', 0.2)}` },
                      '& fieldset': { border: 'none' },
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.6)' },
                    '& .MuiInputLabel-root.Mui-focused': { color: '#10B981' },
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
                  background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                  boxShadow: '0 4px 20px rgba(16,185,129,0.4)',
                  borderRadius: 2,
                  fontWeight: 600,
                  '&:hover': {
                    boxShadow: '0 6px 24px rgba(16,185,129,0.5)',
                  },
                  '&:disabled': {
                    bgcolor: 'rgba(255,255,255,0.1)',
                    color: 'rgba(255,255,255,0.3)',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Generate Investment Plan'}
              </Button>
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
                placeholder={mode === 'qa' ? 'Ask about investments, market analysis, or financial planning...' : 'Click to get latest market news...'}
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
