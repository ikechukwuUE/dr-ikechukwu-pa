import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline, Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography, useMediaQuery, useTheme, Divider } from '@mui/material'
import { Toaster } from 'react-hot-toast'
import { useState } from 'react'
// import MenuIcon from '@mui/icons-material/Menu'
import DashboardIcon from '@mui/icons-material/Dashboard'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import CheckroomIcon from '@mui/icons-material/Checkroom'
import CodeIcon from '@mui/icons-material/Code'
import ScienceIcon from '@mui/icons-material/Science'

// Pages
import Dashboard from './pages/Dashboard'
import Clinical from './pages/Clinical'
import Finance from './pages/Finance'
import Fashion from './pages/Fashion'
import AIDev from './pages/AIDev'

// Advanced dark theme with glass morphism and modern aesthetics
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#14B8A6',
      light: '#5EEAD4',
      dark: '#0F766E',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#8B5CF6',
      light: '#A78BFA',
      dark: '#6D28D9',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#0A0A0F',
      paper: 'rgba(18, 18, 24, 0.8)',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#94A3B8',
      disabled: '#64748B',
    },
    divider: 'rgba(148, 163, 184, 0.12)',
    action: {
      hover: 'rgba(20, 184, 166, 0.08)',
      selected: 'rgba(20, 184, 166, 0.16)',
    },
  },
  typography: {
    fontFamily: '"Plus Jakarta Sans", "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif',
    h1: { fontWeight: 800, fontSize: '2.5rem', letterSpacing: '-0.02em' },
    h2: { fontWeight: 700, fontSize: '2rem', letterSpacing: '-0.01em' },
    h3: { fontWeight: 600, fontSize: '1.75rem' },
    h4: { fontWeight: 600, fontSize: '1.5rem' },
    h5: { fontWeight: 600, fontSize: '1.25rem' },
    h6: { fontWeight: 600, fontSize: '1rem' },
    body1: { fontSize: '1rem', lineHeight: 1.7 },
    body2: { fontSize: '0.875rem', lineHeight: 1.6 },
    button: { fontWeight: 600, textTransform: 'none' },
  },
  shape: {
    borderRadius: 16,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(148, 163, 184, 0.05)',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(148, 163, 184, 0.2)',
            borderRadius: 4,
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: 'rgba(148, 163, 184, 0.3)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          padding: '12px 28px',
          borderRadius: 12,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: -100,
            width: 100,
            height: 100,
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
            transition: 'left 0.5s',
          },
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 25px -5px rgba(20, 184, 166, 0.4)',
            '&::before': {
              left: 100,
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(145deg, rgba(18, 18, 24, 0.9) 0%, rgba(26, 26, 36, 0.9) 100%)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(148, 163, 184, 0.08)',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            border: '1px solid rgba(20, 184, 166, 0.2)',
            boxShadow: '0 20px 40px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(20, 184, 166, 0.1)',
            transform: 'translateY(-4px)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            transition: 'all 0.2s ease',
            '&:hover fieldset': {
              borderColor: 'rgba(20, 184, 166, 0.5)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#14B8A6',
              boxShadow: '0 0 0 3px rgba(20, 184, 166, 0.1)',
            },
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(148, 163, 184, 0.12)',
        },
        indicator: {
          height: 3,
          borderRadius: '3px 3px 0 0',
          background: 'linear-gradient(90deg, #14B8A6, #8B5CF6)',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.95rem',
          borderRadius: '12px 12px 0 0',
          transition: 'all 0.2s ease',
          '&:hover': {
            bgcolor: 'rgba(20, 184, 166, 0.05)',
          },
          '&.Mui-selected': {
            color: '#14B8A6',
            bgcolor: 'rgba(20, 184, 166, 0.08)',
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          margin: '4px 12px',
          transition: 'all 0.2s ease',
          '&:hover': {
            bgcolor: 'rgba(20, 184, 166, 0.08)',
            transform: 'translateX(4px)',
          },
          '&.Mui-selected': {
            bgcolor: 'rgba(20, 184, 166, 0.15)',
            border: '1px solid rgba(20, 184, 166, 0.2)',
            '&:hover': {
              bgcolor: 'rgba(20, 184, 166, 0.2)',
            },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backdropFilter: 'blur(10px)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 600,
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'scale(1.05)',
          },
        },
      },
    },
  },
})

const drawerWidth = 280

interface NavItem {
  id: string
  label: string
  icon: React.ReactNode
  path: string
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { id: 'clinical', label: 'Clinical Decision Support', icon: <LocalHospitalIcon />, path: '/clinical' },
  { id: 'finance', label: 'Financial Analysis', icon: <AccountBalanceIcon />, path: '/finance' },
  { id: 'fashion', label: 'Fashion AI', icon: <CheckroomIcon />, path: '/fashion' },
  { id: 'aidev', label: 'AI Development', icon: <CodeIcon />, path: '/aidev' },
]

function AppContent() {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar sx={{ px: 3, py: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(20, 184, 166, 0.3)',
            }}
          >
            <ScienceIcon sx={{ color: 'white', fontSize: 24 }} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.1rem', background: 'linear-gradient(135deg, #F1F5F9 0%, #94A3B8 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Dr. Ikechukwu PA
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              Multi-Agent AI System
            </Typography>
          </Box>
        </Box>
      </Toolbar>
      <Divider sx={{ mx: 2, mb: 1, opacity: 0.2 }} />
      <List sx={{ flex: 1, px: 2, py: 1 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path
          return (
            <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={isActive}
                onClick={() => {
                  if (isMobile) handleDrawerToggle()
                }}
                sx={{
                  borderRadius: 2,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    background: 'rgba(20, 184, 166, 0.1)',
                  },
                  '&.Mui-selected': {
                    background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%)',
                    border: '1px solid rgba(20, 184, 166, 0.3)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
                    }
                  }
                }}
              >
                <ListItemIcon sx={{ 
                  color: isActive ? 'primary.main' : 'text.secondary',
                  minWidth: 40,
                  '& .MuiSvgIcon-root': { fontSize: 22 }
                }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  primaryTypographyProps={{
                    fontWeight: isActive ? 700 : 500,
                    fontSize: '0.95rem',
                  }}
                />
              </ListItemButton>
            </ListItem>
          )
        })}
      </List>
      <Box sx={{ p: 2, mt: 'auto' }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', opacity: 0.6 }}>
          Version 1.0.0
        </Typography>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            background: 'linear-gradient(180deg, rgba(10, 10, 15, 0.98) 0%, rgba(15, 20, 25, 0.98) 100%)',
            backdropFilter: 'blur(20px)',
            borderRight: '1px solid rgba(148, 163, 184, 0.08)',
          },
        }}
      >
        {drawer}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            background: 'linear-gradient(180deg, rgba(10, 10, 15, 0.98) 0%, rgba(15, 20, 25, 0.98) 100%)',
            backdropFilter: 'blur(20px)',
            borderRight: '1px solid rgba(148, 163, 184, 0.08)',
          },
        }}
        open
      >
        {drawer}
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 3 },
          ml: { md: `${drawerWidth}px` },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          background: 'linear-gradient(135deg, #0A0A0F 0%, #0F1419 50%, #0A0F14 100%)',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'fixed',
            top: 0,
            left: { md: `${drawerWidth}px` },
            right: 0,
            bottom: 0,
            background: 'radial-gradient(ellipse at 20% 20%, rgba(20, 184, 166, 0.05) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.04) 0%, transparent 50%)',
            pointerEvents: 'none',
            zIndex: 0,
          },
        }}
      >
        <Toolbar />
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clinical" element={<Clinical />} />
            <Route path="/finance" element={<Finance />} />
            <Route path="/fashion" element={<Fashion />} />
            <Route path="/aidev" element={<AIDev />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Box>
      </Box>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            borderRadius: '12px',
            padding: '14px 20px',
            background: 'rgba(18, 18, 24, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(148, 163, 184, 0.1)',
            color: '#F1F5F9',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
          },
          duration: 4000,
        }}
      />
    </Box>
  )
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
