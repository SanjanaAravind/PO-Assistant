import React, { useCallback, useState } from 'react';
import { Box, Typography, Paper, Button, LinearProgress } from '@mui/material';
import { useDropzone } from 'react-dropzone';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { api } from '../services/api';
import { useProject } from '../contexts/ProjectContext';

const BrdUpload = () => {
  const { selectedProject } = useProject();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!selectedProject) {
      alert('Please select a project first');
      return;
    }

    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_key', selectedProject);

    try {
      await api.post('/upload_brd', formData, {
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        },
      });

      // Reset states after successful upload
      setUploading(false);
      setUploadProgress(0);
    } catch (error) {
      console.error('Upload failed:', error);
      setUploading(false);
      setUploadProgress(0);
      alert('Failed to upload file. Please try again.');
    }
  }, [selectedProject]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    multiple: false,
  });

  return (
    <Box sx={{ height: '100%', p: 3 }}>
      <Paper
        {...getRootProps()}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          borderRadius: 2,
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop your BRD here' : 'Drag & Drop your BRD here'}
        </Typography>
        <Typography variant="body2" color="text.secondary" align="center">
          or click to select file
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
          Supported formats: PDF, DOC, DOCX, TXT
        </Typography>

        {uploading && (
          <Box sx={{ width: '80%', mt: 3 }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              Uploading... {uploadProgress}%
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default BrdUpload; 