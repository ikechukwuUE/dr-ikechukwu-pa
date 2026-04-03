import { Box, Typography, Card, CardContent, Grid, Avatar, Chip, IconButton, Tooltip, Fade, Zoom, useTheme, alpha } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import CheckroomIcon from '@mui/icons-material/Checkroom'
import CodeIcon from '@mui/icons-material/Code'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import PsychologyIcon from '@mui/icons-material/Psychology'
import BoltIcon from '@mui/icons-material/Bolt'
import SparklesIcon from '@mui/icons-material/AutoAwesome'
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch'
import ShieldIcon from '@mui/icons-material/Shield'
import SpeedIcon from '@mui/icons-material/Speed'
import GroupsIcon from '@mui/icons-material/Groups'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'

export default function Dashboard() {
  const navigate = useNavigate()
  const theme = useTheme()
  const [hoveredCard, setHoveredCard] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const domains = [
    {
      id: 'clinical',
      title: 'Clinical Assistant',
      subtitle: 'Medical Intelligence',
      description: 'Advanced medical decision support, patient assessment, and clinical guidance powered by AI',
      icon: <LocalHospitalIcon sx={{ fontSize: 36 }} />,
      path: '/clinical',
      gradient: 'linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%)',
      glowColor: 'rgba(16, 185, 129, 0.4)',
      bgPattern: 'radial-gradient(circle at 20% 80%, rgba(16, 185, 129, 0.15) 0%, transparent 50%)',
      features: ['Q&A', 'Research', 'Clinical Decision', 'Image Analysis'],
      stats: { agents: 4, tools: 12 }
    },
    {
      id: 'finance',
      title: 'Finance Assistant',
      subtitle: 'Wealth Intelligence',
      description: 'Smart investment analysis, portfolio management, and personalized financial planning',
      icon: <AccountBalanceIcon sx={{ fontSize: 36 }} />,
      path: '/finance',
      gradient: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%)',
      glowColor: 'rgba(59, 130, 246, 0.4)',
      bgPattern: 'radial-gradient(circle at 80% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 50%)',
      features: ['Q&A', 'Investment Planning', 'Market News', 'Risk Analysis'],
      stats: { agents: 3, tools: 8 }
    },
    {
      id: 'fashion',
      title: 'Fashion Assistant',
      subtitle: 'Style Intelligence',
      description: 'Personalized style recommendations, outfit analysis, and trend insights with vision AI',
      icon: <CheckroomIcon sx={{ fontSize: 36 }} />,
      path: '/fashion',
      gradient: 'linear-gradient(135deg, #EC4899 0%, #DB2777 50%, #BE185D 100%)',
      glowColor: 'rgba(236, 72, 153, 0.4)',
      bgPattern: 'radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.15) 0%, transparent 50%)',
      features: ['Outfit Analysis', 'Trends', 'Recommendations', 'Vision AI'],
      stats: { agents: 3, tools: 10 }
    },
    {
      id: 'aidev',
      title: 'AI Dev Assistant',
      subtitle: 'Code Intelligence',
      description: 'Intelligent code generation, debugging, and development best practices with AI review',
      icon: <CodeIcon sx={{ fontSize: 36 }} />,
      path: '/aidev',
      gradient: 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 50%, #6D28D9 100%)',
      glowColor: 'rgba(139, 92, 246, 0.4)',
      bgPattern: 'radial-gradient(circle at 30% 70%, rgba(139, 92, 246, 0.15) 0%, transparent 50%)',
      features: ['Code Generation', 'Review', 'Debug', 'Best Practices'],
      stats: { agents: 4, tools: 15 }
    },
  ]

  const capabilities = [
    { icon: <PsychologyIcon />, label: 'Multi-Agent AI', color: '#8B5CF6' },
    { icon: <BoltIcon />, label: 'Real-time Processing', color: '#F59E0B' },
    { icon: <ShieldIcon />, label: 'Secure & Private', color: '#10B981' },
    { icon: <SpeedIcon />, label: 'High Performance', color: '#3B82F6' },
    { icon: <GroupsIcon />, label: 'Collaborative', color: '#EC4899' },
    { icon: <TrendingUpIcon />, label: 'Scalable', color: '#06B6D4' },
  ]

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 25%, #2d2d2d 50%, #0d0d0d 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated background elements */}
      <Box sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none',
        zIndex: 0,
      }}>
        {/* Floating orbs */}
        {[...Array(5)].map((_, i) => (
          <Box
            key={i}
            sx={{
              position: 'absolute',
              width: { xs: 80, md: 150 + i * 40 },
              height: { xs: 80, md: 150 + i * 40 },
              borderRadius: '50%',
              background: `radial-gradient(circle, ${['rgba(139,92,246,0.1)', 'rgba(59,130,246,0.08)', 'rgba(236,72,153,0.06)', 'rgba(16,185,129,0.05)', 'rgba(245,158,11,0.04)'][i]} 0%, transparent 70%)`,
              top: `${[10, 60, 20, 70, 40][i]}%`,
              left: `${[20, 70, 80, 10, 50][i]}%`,
              animation: `float ${8 + i * 2}s ease-in-out infinite`,
              animationDelay: `${i * 0.5}s`,
            }}
          />
        ))}
        
        {/* Grid pattern */}
        <Box sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `
            linear-gradient(rgba(139,92,246,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(139,92,246,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          opacity: 0.5,
        }} />
      </Box>

      {/* Main content */}
      <Box sx={{ position: 'relative', zIndex: 1, p: { xs: 2, md: 3 } }}>
        <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
          {/* Hero Header */}
          <Fade in={mounted} timeout={1000}>
            <Box sx={{ textAlign: 'center', mb: 5, pt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                <Avatar sx={{
                  width: 64,
                  height: 64,
                  background: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 50%, #F59E0B 100%)',
                  boxShadow: '0 8px 32px rgba(139,92,246,0.4)',
                  animation: 'pulse 3s ease-in-out infinite',
                }}>
                  <AutoAwesomeIcon sx={{ fontSize: 32 }} />
                </Avatar>
              </Box>
              
              <Typography 
                variant="h1" 
                sx={{ 
                  fontSize: { xs: '2rem', md: '3rem', lg: '3.5rem' },
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #fff 0%, #a78bfa 50%, #ec4899 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 1,
                  letterSpacing: '-0.02em',
                }}
              >
                Vogue Space
              </Typography>
              
              <Typography 
                variant="h5" 
                sx={{ 
                  color: 'rgba(255,255,255,0.7)',
                  fontWeight: 400,
                  mb: 3,
                  fontSize: { xs: '0.9rem', md: '1.1rem' },
                }}
              >
                Next-Generation Multi-Agent AI System
              </Typography>

              {/* Capability chips */}
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center', mb: 3 }}>
                {capabilities.map((cap, i) => (
                  <Zoom in={mounted} timeout={800 + i * 100} key={cap.label}>
                    <Chip
                      icon={cap.icon}
                      label={cap.label}
                      sx={{
                        bgcolor: alpha(cap.color, 0.15),
                        color: cap.color,
                        border: `1px solid ${alpha(cap.color, 0.3)}`,
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        '& .MuiChip-icon': { color: cap.color, fontSize: '1rem' },
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          bgcolor: alpha(cap.color, 0.25),
                          transform: 'translateY(-2px)',
                          boxShadow: `0 4px 12px ${alpha(cap.color, 0.3)}`,
                        },
                      }}
                    />
                  </Zoom>
                ))}
              </Box>
            </Box>
          </Fade>

          {/* Domain Cards Grid */}
          <Grid container spacing={3}>
            {domains.map((domain, index) => (
              <Grid item xs={12} sm={6} lg={3} key={domain.id}>
                <Zoom in={mounted} timeout={1000 + index * 150}>
                  <Card 
                    sx={{ 
                      height: '100%',
                      cursor: 'pointer',
                      position: 'relative',
                      overflow: 'hidden',
                      background: 'rgba(255,255,255,0.03)',
                      backdropFilter: 'blur(20px)',
                      border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: 3,
                      transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                      '&:hover': {
                        transform: 'translateY(-8px) scale(1.02)',
                        border: `1px solid ${alpha(domain.glowColor, 0.5)}`,
                        boxShadow: `0 20px 60px ${domain.glowColor}, 0 0 40px ${alpha(domain.glowColor, 0.2)}`,
                        '& .domain-icon': {
                          transform: 'scale(1.1) rotate(5deg)',
                          boxShadow: `0 8px 32px ${domain.glowColor}`,
                        },
                        '& .domain-glow': {
                          opacity: 1,
                        },
                        '& .domain-features': {
                          opacity: 1,
                          transform: 'translateY(0)',
                        },
                      },
                    }}
                    onClick={() => navigate(domain.path)}
                    onMouseEnter={() => setHoveredCard(domain.id)}
                    onMouseLeave={() => setHoveredCard(null)}
                  >
                    {/* Glow effect */}
                    <Box
                      className="domain-glow"
                      sx={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '100%',
                        background: domain.bgPattern,
                        opacity: 0,
                        transition: 'opacity 0.4s ease',
                        pointerEvents: 'none',
                      }}
                    />

                    {/* Gradient border top */}
                    <Box sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: 3,
                      background: domain.gradient,
                    }} />

                    <CardContent sx={{ 
                      textAlign: 'center', 
                      py: 3,
                      px: 2,
                      position: 'relative',
                      zIndex: 1,
                    }}>
                      {/* Icon */}
                      <Avatar 
                        className="domain-icon"
                        sx={{
                          width: 64,
                          height: 64,
                          mx: 'auto',
                          mb: 2,
                          background: domain.gradient,
                          boxShadow: `0 8px 24px ${alpha(domain.glowColor, 0.4)}`,
                          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                        }}
                      >
                        {domain.icon}
                      </Avatar>

                      {/* Subtitle */}
                      <Typography 
                        variant="overline" 
                        sx={{ 
                          color: alpha('#fff', 0.5),
                          letterSpacing: 2,
                          fontSize: '0.65rem',
                          fontWeight: 600,
                        }}
                      >
                        {domain.subtitle}
                      </Typography>

                      {/* Title */}
                      <Typography 
                        variant="h5" 
                        sx={{ 
                          mb: 1, 
                          fontWeight: 700,
                          color: '#fff',
                          fontSize: '1.1rem',
                        }}
                      >
                        {domain.title}
                      </Typography>

                      {/* Description */}
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          color: 'rgba(255,255,255,0.6)',
                          lineHeight: 1.5,
                          mb: 1.5,
                          fontSize: '0.8rem',
                        }}
                      >
                        {domain.description}
                      </Typography>

                      {/* Stats */}
                      <Box sx={{ 
                        display: 'flex', 
                        justifyContent: 'center', 
                        gap: 2,
                        mb: 1.5,
                      }}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h6" sx={{ color: '#fff', fontWeight: 700, fontSize: '1rem' }}>
                            {domain.stats.agents}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.7rem' }}>
                            Agents
                          </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h6" sx={{ color: '#fff', fontWeight: 700, fontSize: '1rem' }}>
                            {domain.stats.tools}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.7rem' }}>
                            Tools
                          </Typography>
                        </Box>
                      </Box>

                      {/* Features */}
                      <Box 
                        className="domain-features"
                        sx={{ 
                          display: 'flex', 
                          gap: 0.5, 
                          flexWrap: 'wrap', 
                          justifyContent: 'center',
                          opacity: 0,
                          transform: 'translateY(10px)',
                          transition: 'all 0.4s ease',
                        }}
                      >
                        {domain.features.map((feature) => (
                          <Chip
                            key={feature}
                            label={feature}
                            size="small"
                            sx={{
                              bgcolor: alpha('#fff', 0.08),
                              color: 'rgba(255,255,255,0.8)',
                              fontSize: '0.65rem',
                              height: 22,
                              border: `1px solid ${alpha('#fff', 0.1)}`,
                            }}
                          />
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Zoom>
              </Grid>
            ))}
          </Grid>

          {/* Footer */}
          <Fade in={mounted} timeout={1500}>
            <Box sx={{ textAlign: 'center', mt: 5, pb: 2 }}>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                gap: 1,
                mb: 1,
              }}>
                <SparklesIcon sx={{ color: 'rgba(255,255,255,0.4)', fontSize: 14 }} />
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem' }}>
                  Powered by BeeAI Framework • MCP Protocol • OpenRouter
                </Typography>
                <SparklesIcon sx={{ color: 'rgba(255,255,255,0.4)', fontSize: 14 }} />
              </Box>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.7rem' }}>
                Secure • Scalable • Intelligent
              </Typography>
            </Box>
          </Fade>
        </Box>
      </Box>

      {/* CSS Animations */}
      <style>
        {`
          @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(5deg); }
          }
          @keyframes pulse {
            0%, 100% { transform: scale(1); box-shadow: 0 8px 32px rgba(139,92,246,0.4); }
            50% { transform: scale(1.05); box-shadow: 0 12px 48px rgba(139,92,246,0.6); }
          }
        `}
      </style>
    </Box>
  )
}
