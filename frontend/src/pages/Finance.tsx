import { useState } from 'react'
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  CardContent,
  Grid,
  MenuItem,
  Alert,
  CircularProgress,
  Paper,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import api from '../services/api'

export default function Finance() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<unknown>(null)
  const [formData, setFormData] = useState({
    query_type: 'investment' as 'investment' | 'budget' | 'tax' | 'retirement' | 'debt' | 'general',
    question: '',
    risk_tolerance: 'moderate' as 'conservative' | 'moderate' | 'aggressive',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await api.analyzeFinance(formData)
      setResult(response.data)
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setLoading(false)
    }
  }

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
          background: 'radial-gradient(ellipse at 20% 20%, rgba(5, 150, 105, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.06) 0%, transparent 50%)',
          pointerEvents: 'none',
        },
      }}
    >
      <Container maxWidth="lg" sx={{ position: 'relative' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mb: 3, color: 'text.secondary' }}
        >
          Back to Dashboard
        </Button>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <AccountBalanceIcon sx={{ color: 'white' }} />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Finance
            </Typography>
            <Typography variant="body2" color="text.secondary">
              AI-powered financial analysis and investment strategies
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Paper
              elevation={0}
              sx={{
                height: '100%',
                background: 'rgba(15, 23, 42, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(148, 163, 184, 0.1)',
                borderRadius: 3,
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Financial Query
                </Typography>
                <form onSubmit={handleSubmit}>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        select
                        label="Query Type"
                        value={formData.query_type}
                        onChange={(e) => setFormData({ ...formData, query_type: e.target.value as typeof formData.query_type })}
                      >
                        <MenuItem value="investment">Investment</MenuItem>
                        <MenuItem value="budget">Budget</MenuItem>
                        <MenuItem value="tax">Tax</MenuItem>
                        <MenuItem value="retirement">Retirement</MenuItem>
                        <MenuItem value="debt">Debt</MenuItem>
                        <MenuItem value="general">General</MenuItem>
                      </TextField>
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        select
                        label="Risk Tolerance"
                        value={formData.risk_tolerance}
                        onChange={(e) => setFormData({ ...formData, risk_tolerance: e.target.value as typeof formData.risk_tolerance })}
                      >
                        <MenuItem value="conservative">Conservative</MenuItem>
                        <MenuItem value="moderate">Moderate</MenuItem>
                        <MenuItem value="aggressive">Aggressive</MenuItem>
                      </TextField>
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
                        placeholder="e.g., What are the best investment options for retirement?"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Button
                        type="submit"
                        variant="contained"
                        fullWidth
                        size="large"
                        disabled={loading}
                        sx={{
                          background: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
                          py: 1.5,
                        }}
                      >
                        {loading ? <CircularProgress size={24} color="inherit" /> : 'Analyze Finance'}
                      </Button>
                    </Grid>
                  </Grid>
                </form>
              </CardContent>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper
              elevation={0}
              sx={{
                height: '100%',
                background: 'rgba(15, 23, 42, 0.6)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(148, 163, 184, 0.1)',
                borderRadius: 3,
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Analysis Results
                </Typography>
                {result ? (
                  <Box>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      Analysis completed.
                    </Alert>
                    <Typography variant="body2" color="text.secondary">
                      {JSON.stringify(result, null, 2)}
                    </Typography>
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
                    <AccountBalanceIcon sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
                    <Typography>Enter your financial question</Typography>
                  </Box>
                )}
              </CardContent>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
