import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import PublishIcon from '@mui/icons-material/Publish';
import { api } from '../services/api';
import { useProject } from '../contexts/ProjectContext';

interface Story {
  id: string;
  title: string;
  description: string;
  published: boolean;
  jira_key?: string;
}

interface EditDialogProps {
  open: boolean;
  story: Story | null;
  onClose: () => void;
  onSave: (editedStory: Story) => void;
}

const EditDialog: React.FC<EditDialogProps> = ({ open, story, onClose, onSave }) => {
  const [editedTitle, setEditedTitle] = useState(story?.title || '');
  const [editedDescription, setEditedDescription] = useState(story?.description || '');

  useEffect(() => {
    if (story) {
      setEditedTitle(story.title);
      setEditedDescription(story.description);
    }
  }, [story]);

  const handleSave = () => {
    if (story) {
      onSave({
        ...story,
        title: editedTitle,
        description: editedDescription
      });
    }
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Edit Story</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Title"
            fullWidth
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={4}
            value={editedDescription}
            onChange={(e) => setEditedDescription(e.target.value)}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained" color="primary">
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const Stories: React.FC = () => {
  const { selectedProject } = useProject();
  const [stories, setStories] = useState<Story[]>([]);
  const [editingStory, setEditingStory] = useState<Story | null>(null);
  const [isPublishing, setIsPublishing] = useState<string | null>(null); // Store publishing story ID
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    const fetchStories = async () => {
      try {
        const response = await api.get(`/stories/${selectedProject}`);
        setStories(response.data.stories);
      } catch (error) {
        console.error('Failed to fetch stories:', error);
        setMessage({
          type: 'error',
          text: 'Failed to fetch stories. Please try again.'
        });
      }
    };

    if (selectedProject) {
      fetchStories();
    }
  }, [selectedProject]);

  const handlePublish = async (story: Story) => {
    if (!selectedProject) {
      setMessage({ type: 'error', text: 'Please select a project first' });
      return;
    }

    setIsPublishing(story.id);
    setMessage(null);
    try {
      const response = await api.post(`/stories/${selectedProject}/${story.id}/publish`);

      setStories(prev => prev.map(s => 
        s.id === story.id ? { ...s, published: true, jira_key: response.data.jira_key } : s
      ));

      setMessage({
        type: 'success',
        text: `Story successfully published to Jira as ${response.data.jira_key}`
      });
    } catch (error) {
      console.error('Failed to publish story:', error);
      setMessage({
        type: 'error',
        text: 'Failed to publish story. Please try again.'
      });
    } finally {
      setIsPublishing(null);
    }
  };

  const handleEdit = (story: Story) => {
    setEditingStory(story);
  };

  const handleSaveEdit = async (editedStory: Story) => {
    try {
      await api.put(`/stories/${selectedProject}/${editedStory.id}`, {
        updates: {
          title: editedStory.title,
          description: editedStory.description
        }
      });

      setStories(prev => prev.map(story =>
        story.id === editedStory.id ? editedStory : story
      ));
      setMessage({
        type: 'success',
        text: 'Story updated successfully'
      });
    } catch (error) {
      console.error('Failed to update story:', error);
      setMessage({
        type: 'error',
        text: 'Failed to update story. Please try again.'
      });
    }
    setEditingStory(null);
  };

  if (!selectedProject) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          Please select a project to view stories
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Generated Stories
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

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stories.map((story) => (
              <TableRow key={story.id}>
                <TableCell>{story.title}</TableCell>
                <TableCell>{story.description}</TableCell>
                <TableCell>
                  {story.published ? (
                    <Chip 
                      label={story.jira_key || 'Published'} 
                      color="success" 
                      size="small"
                    />
                  ) : (
                    <Chip 
                      label="Draft" 
                      color="default" 
                      size="small"
                    />
                  )}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    onClick={() => handleEdit(story)}
                    disabled={story.published}
                    size="small"
                  >
                    <EditIcon />
                  </IconButton>
                  <Button
                    variant="contained"
                    startIcon={<PublishIcon />}
                    onClick={() => handlePublish(story)}
                    disabled={story.published || isPublishing === story.id}
                    size="small"
                    sx={{ ml: 1 }}
                  >
                    {isPublishing === story.id ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : story.published ? (
                      'Published'
                    ) : (
                      'Publish'
                    )}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {stories.length === 0 && (
        <Paper sx={{ p: 3, textAlign: 'center', mt: 2 }}>
          <Typography color="text.secondary">
            No stories generated yet. Try asking me to generate user stories in the chat!
          </Typography>
        </Paper>
      )}

      <EditDialog
        open={editingStory !== null}
        story={editingStory}
        onClose={() => setEditingStory(null)}
        onSave={handleSaveEdit}
      />
    </Box>
  );
};

export default Stories; 