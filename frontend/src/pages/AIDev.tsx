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
  ToggleButton,
  ToggleButtonGroup,
  Paper,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import CodeIcon from '@mui/icons-material/Code'
import api from '../services/api'

export default function AIDev() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<unknown>(null)
  const [mode, setMode] = useState<'generate' | 'debug' | 'review'>('generate')
  const [formData, setFormData] = useState({
    language: 'python',
    task_description: '',
    code: '',
    error_message: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      let response
      if (mode === 'generate') {
        response = await api.generateCode({
          language: formData.language,
          task_description: formData.task_description,
        })
      } else if (mode === 'debug') {
        response = await api.debugCode({
          language: formData.language,
          code: formData.code,
          error_message: formData.error_message || undefined,
        })
      } else {
        response = await api.reviewCode(formData.code, formData.language)
      }
      setResult(response.data)
    } catch (error) {
      console.error('Request failed:', error)
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
          background: 'radial-gradient(ellipse at 20% 20%, rgba(124, 58, 237, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(167, 139, 250, 0.06) 0%, transparent 50%)',
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
              background: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CodeIcon sx={{ color: 'white' }} />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              AI Development
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Code generation, debugging, and review with LangGraph
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
                  Code Tool
                </Typography>
                
                <ToggleButtonGroup
                  value={mode}
                  exclusive
                  onChange={(_, newMode) => newMode && setMode(newMode)}
                  fullWidth
                  sx={{ mb: 3 }}
                >
                  <ToggleButton value="generate">Generate</ToggleButton>
                  <ToggleButton value="debug">Debug</ToggleButton>
                  <ToggleButton value="review">Review</ToggleButton>
                </ToggleButtonGroup>

                <form onSubmit={handleSubmit}>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        select
                        label="Language"
                        value={formData.language}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                      >
                        <MenuItem value="python">Python</MenuItem>
                        <MenuItem value="javascript">JavaScript</MenuItem>
                        <MenuItem value="typescript">TypeScript</MenuItem>
                        <MenuItem value="java">Java</MenuItem>
                        <MenuItem value="csharp">C#</MenuItem>
                        <MenuItem value="go">Go</MenuItem>
                        <MenuItem value="rust">Rust</MenuItem>
                      </TextField>
                    </Grid>
                    
                    {mode === 'generate' && (
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Task Description"
                          value={formData.task_description}
                          onChange={(e) => setFormData({ ...formData, task_description: e.target.value })}
                          required
                          multiline
                          rows={4}
                          placeholder="e.g., Write a function to calculate factorial"
                        />
                      </Grid>
                    )}
                    
                    {(mode === 'debug' || mode === 'review') && (
                      <>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Code"
                            value={formData.code}
                            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                            required
                            multiline
                            rows={8}
                            sx={{ fontFamily: 'monospace' }}
                          />
                        </Grid>
                        {mode === 'debug' && (
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="Error Message (optional)"
                              value={formData.error_message}
                              onChange={(e) => setFormData({ ...formData, error_message: e.target.value })}
                              multiline
                              rows={2}
                            />
                          </Grid>
                        )}
                      </>
                    )}
                    
                    <Grid item xs={12}>
                      <Button
                        type="submit"
                        variant="contained"
                        fullWidth
                        size="large"
                        disabled={loading}
                        sx={{
                          background: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
                          py: 1.5,
                        }}
                      >
                        {loading ? <CircularProgress size={24} color="inherit" /> : 
                          mode === 'generate' ? 'Generate Code' : 
                          mode === 'debug' ? 'Debug Code' : 'Review Code'}
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
                  Output
                </Typography>
                {result ? (
                  <Box>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      Completed successfully.
                    </Alert>
                    <Typography 
                      variant="body2" 
                      color="text.secondary" 
                      component="pre"
                      sx={{ 
                        whiteSpace: 'pre-wrap', 
                        fontFamily: 'monospace',
                        bgcolor: '#1E293B',
                        color: '#E2E8F0',
                        p: 2,
                        borderRadius: 1,
                      }}
                    >
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
                    <CodeIcon sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
                    <Typography>Enter code or task description</Typography>
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
