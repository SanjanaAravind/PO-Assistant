import React, { useState } from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ProjectSelector from './components/ProjectSelector';
import Chat from './components/Chat';
import Navigation from './components/Navigation';
import { ProjectProvider } from './contexts/ProjectContext';
import ContextManagement from './components/ContextManagement';
import Stories from './components/Stories';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#f0f4f8',
      paper: '#ffffff',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    subtitle1: {
      color: '#5c6b7c',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <ThemeProvider theme={theme}>
      <ProjectProvider>
        <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
          <Container maxWidth="lg">
            {/* Header */}
            <Typography variant="h4" component="h1" gutterBottom>
              PO Assist
            </Typography>

            {/* Main Content */}
            <Paper sx={{ p: 4, mb: 3 }}>
              <Box sx={{ mb: 3 }}>
                <ProjectSelector />
              </Box>

              <Navigation activeTab={activeTab} onTabChange={setActiveTab} />

              <Box sx={{ 
                height: 'calc(100vh - 300px)', 
                bgcolor: 'background.default',
                borderRadius: 2,
                overflow: 'auto'
              }}>
                {activeTab === 'chat' && <Chat />}
                {activeTab === 'context' && <ContextManagement />}
                {activeTab === 'stories' && <Stories />}
              </Box>
            </Paper>
          </Container>
        </Box>
      </ProjectProvider>
    </ThemeProvider>
  );
}

export default App;