import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Link,
  Chip
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import RefreshIcon from '@mui/icons-material/Refresh';
import { api } from '../services/api';

interface JiraStatus {
  status: 'connected' | 'not_configured' | 'error';
  message: string;
  url?: string;
}

const JiraStatus: React.FC = () => {
  const [status, setStatus] = useState<JiraStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const checkJiraConnection = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/jira/test-connection');
      setStatus(response.data);
    } catch (error) {
      setStatus({
        status: 'error',
        message: 'Failed to check Jira connection'
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkJiraConnection();
  }, []);

  const getStatusIcon = () => {
    if (isLoading) return <CircularProgress size={20} />;
    
    switch (status?.status) {
      case 'connected':
        return <CheckCircleIcon />;
      case 'not_configured':
        return <WarningIcon />;
      case 'error':
        return <ErrorIcon />;
      default:
        return <CircularProgress size={20} />;
    }
  };

  const getStatusColor = () => {
    switch (status?.status) {
      case 'connected':
        return 'success';
      case 'not_configured':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          Jira Integration
          <Chip
            icon={getStatusIcon()}
            label={status?.status || 'checking...'}
            color={getStatusColor()}
            size="small"
          />
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={checkJiraConnection}
          disabled={isLoading}
          size="small"
        >
          Test Connection
        </Button>
      </Box>

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {status?.message}
        </Typography>
        {status?.url && (
          <Typography variant="body2">
            Connected to: <Link href={status.url} target="_blank" rel="noopener noreferrer">{status.url}</Link>
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default JiraStatus; 