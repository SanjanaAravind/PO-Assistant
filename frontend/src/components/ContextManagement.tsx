import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  TextField,
  CircularProgress,
  Alert,
  Grid
} from '@mui/material';
import JiraIcon from '@mui/icons-material/BugReport';
import ConfluenceIcon from '@mui/icons-material/Article';
import { api } from '../services/api';
import { useProject } from '../contexts/ProjectContext';
import JiraStatus from './JiraStatus';

const ContextManagement: React.FC = () => {
  const { selectedProject } = useProject();
  const [isJiraSyncing, setIsJiraSyncing] = useState(false);
  const [isConfluenceSyncing, setIsConfluenceSyncing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [confluenceSpace, setConfluenceSpace] = useState('');
  const [confluenceQuery, setConfluenceQuery] = useState('');

  const handleJiraSync = async () => {
    if (!selectedProject) {
      setMessage({ type: 'error', text: 'Please select a project first' });
      return;
    }

    setIsJiraSyncing(true);
    setMessage(null);
    try {
      const response = await api.post('/sync_jira', {
        project_key: selectedProject,
        max_results: 50
      });
      setMessage({ 
        type: 'success', 
        text: `Successfully synced ${response.data.message}` 
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: 'Failed to sync Jira data. Please check your configuration.' 
      });
    } finally {
      setIsJiraSyncing(false);
    }
  };

  const handleConfluenceSync = async () => {
    if (!selectedProject) {
      setMessage({ type: 'error', text: 'Please select a project first' });
      return;
    }

    if (!confluenceSpace.trim()) {
      setMessage({ type: 'error', text: 'Please enter a Confluence space key' });
      return;
    }

    setIsConfluenceSyncing(true);
    setMessage(null);
    try {
      const response = await api.post('/sync_confluence', {
        space_key: confluenceSpace,
        search_query: confluenceQuery.trim() || undefined,
        max_results: 50
      });
      setMessage({ 
        type: 'success', 
        text: `Successfully synced ${response.data.message}` 
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: 'Failed to sync Confluence data. Please check your configuration.' 
      });
    } finally {
      setIsConfluenceSyncing(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Context Management
      </Typography>
      
      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 3 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      {/* Jira Status */}
      <JiraStatus />

      <Grid container spacing={3}>
        {/* Jira Sync */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Sync Jira Issues
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Import issues from your Jira project to use as context for AI responses.
            </Typography>
            <Button
              variant="contained"
              startIcon={isJiraSyncing ? <CircularProgress size={20} /> : <JiraIcon />}
              onClick={handleJiraSync}
              disabled={isJiraSyncing || !selectedProject}
              fullWidth
            >
              {isJiraSyncing ? 'Syncing...' : 'Sync Jira Issues'}
            </Button>
          </Paper>
        </Grid>

        {/* Confluence Sync */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Sync Confluence Pages
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Import pages from Confluence to use as context for AI responses.
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Space Key"
                value={confluenceSpace}
                onChange={(e) => setConfluenceSpace(e.target.value)}
                size="small"
                required
              />
              <TextField
                label="Search Query (Optional)"
                value={confluenceQuery}
                onChange={(e) => setConfluenceQuery(e.target.value)}
                size="small"
                helperText="Filter pages by search terms"
              />
              <Button
                variant="contained"
                startIcon={isConfluenceSyncing ? <CircularProgress size={20} /> : <ConfluenceIcon />}
                onClick={handleConfluenceSync}
                disabled={isConfluenceSyncing || !selectedProject}
              >
                {isConfluenceSyncing ? 'Syncing...' : 'Sync Confluence Pages'}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ContextManagement; 