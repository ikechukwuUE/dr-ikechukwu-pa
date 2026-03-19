import { Box, Container, Typography, Grid, CardContent, CardActionArea, Chip, Paper } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import CheckroomIcon from '@mui/icons-material/Checkroom'
import CodeIcon from '@mui/icons-material/Code'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser'
import BuildIcon from '@mui/icons-material/Build'
// import ScienceIcon from '@mui/icons-material/Science'

const domains = [
  {
    id: 'clinical',
    title: 'Clinical Decision Support',
    description: 'AI-powered medical diagnosis and treatment recommendations using multimodal analysis with 16 specialist agents',
    icon: LocalHospitalIcon,
    color: '#0F766E',
    gradient: 'linear-gradient(135deg, #0F766E 0%, #14B8A6 100%)',
    orchestration: 'CrewAI Hierarchical',
    tools: 5,
  },
  {
    id: 'finance',
    title: 'Finance',
    description: 'Intelligent financial analysis, investment strategies, and portfolio management with multi-agent collaboration',
    icon: AccountBalanceIcon,
    color: '#059669',
    gradient: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
    orchestration: 'CrewAI Hierarchical',
    tools: 5,
  },
  {
    id: 'fashion',
    title: 'Fashion',
    description: 'Style recommendations, trend analysis, and outfit suggestions with vision AI and multimodal processing',
    icon: CheckroomIcon,
    color: '#DC2626',
    gradient: 'linear-gradient(135deg, #DC2626 0%, #F97316 100%)',
    orchestration: 'Direct API + LangChain',
    tools: 3,
  },
  {
    id: 'aidev',
    title: 'AI Development',
    description: 'Code generation, debugging, and review with LangGraph state machines and tool orchestration',
    icon: CodeIcon,
    color: '#7C3AED',
    gradient: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
    orchestration: 'LangGraph Cyclic',
    tools: 4,
  },
]

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0A0A0F 0%, #0F1419 50%, #0A0F14 100%)',
        py: 4,
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
        },
      }}
    >
      <Container maxWidth="lg" sx={{ position: 'relative', py: 4 }}>
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1,
              mb: 2,
              px: 3,
              py: 1.5,
              borderRadius: 3,
              background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
              border: '1px solid rgba(20, 184, 166, 0.2)',
            }}
          >
            <AutoAwesomeIcon sx={{ color: 'primary.main', fontSize: 24 }} />
            <Typography
              variant="overline"
              sx={{ color: 'primary.main', fontWeight: 700, letterSpacing: 3, fontSize: '0.9rem' }}
            >
              Dr. Ikechukwu PA
            </Typography>
          </Box>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              mb: 2,
              fontSize: { xs: '2rem', md: '3rem' },
              background: 'linear-gradient(135deg, #F1F5F9 0%, #94A3B8 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Your AI-Powered Assistant
          </Typography>
          <Typography
            variant="body1"
            sx={{ color: 'text.secondary', maxWidth: 700, mx: 'auto', fontWeight: 400, fontSize: '1.1rem' }}
          >
            A multimodal, multi-agent system for clinical support, finance, fashion, and AI development
          </Typography>
        </Box>

        {/* Domain Cards */}
        <Grid container spacing={4}>
          {domains.map((domain, index) => (
            <Grid item xs={12} sm={6} key={domain.id}>
              <Paper
                elevation={0}
                sx={{
                  height: '100%',
                  transition: 'all 0.3s ease',
                  background: 'rgba(15, 23, 42, 0.6)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(148, 163, 184, 0.1)',
                  '&:hover': {
                    transform: `translateY(-8px)`,
                    boxShadow: `0 20px 40px -12px ${domain.color}40`,
                    border: `1px solid ${domain.color}40`,
                  },
                }}
              >
                <CardActionArea
                  onClick={() => navigate(`/${domain.id}`)}
                  sx={{ height: '100%', p: 3 }}
                >
                  <CardContent>
                    <Box
                      sx={{
                        width: 56,
                        height: 56,
                        borderRadius: 2,
                        background: domain.gradient,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mb: 2,
                      }}
                    >
                      <domain.icon sx={{ color: 'white', fontSize: 28 }} />
                    </Box>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                      {domain.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                      {domain.description}
                    </Typography>
                    {/* Security & Tools Badges */}
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Chip
                        icon={<VerifiedUserIcon sx={{ fontSize: 16 }} />}
                        label="IBM/Anthropic Secure"
                        size="small"
                        sx={{
                          bgcolor: 'rgba(5, 150, 105, 0.1)',
                          color: '#059669',
                          fontWeight: 500,
                          fontSize: '0.7rem',
                        }}
                      />
                      <Chip
                        icon={<BuildIcon sx={{ fontSize: 16 }} />}
                        label={`${domain.tools} MCP Tools`}
                        size="small"
                        sx={{
                          bgcolor: 'rgba(124, 58, 237, 0.1)',
                          color: '#7C3AED',
                          fontWeight: 500,
                          fontSize: '0.7rem',
                        }}
                      />
                      <Chip
                        label={domain.orchestration}
                        size="small"
                        sx={{
                          bgcolor: 'rgba(15, 118, 110, 0.1)',
                          color: '#0F766E',
                          fontWeight: 500,
                          fontSize: '0.7rem',
                        }}
                      />
                    </Box>
                  </CardContent>
                </CardActionArea>
              </Paper>
            </Grid>
          ))}
        </Grid>

        {/* Footer Info */}
        <Box sx={{ mt: 8, textAlign: 'center' }}>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            Powered by OpenRouter • Built with FastAPI, CrewAI, LangGraph & React
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}
