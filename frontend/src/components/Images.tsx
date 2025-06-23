import React, { useState } from 'react';
import { Box, Typography, Button, CircularProgress, Grid } from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { api } from '../services/api';
import { useProject } from '../contexts/ProjectContext';

interface ImageUploadResponse {
  message: string;
  description: string;
  image_path: string;
  filename: string;
}

const Images = () => {
  const { selectedProject } = useProject();
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<ImageUploadResponse[]>([]);

  const onDrop = async (acceptedFiles: File[]) => {
    if (!selectedProject) {
      alert('Please select a project first');
      return;
    }

    setIsLoading(true);
    try {
      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_key', selectedProject);

        const response = await api.post<ImageUploadResponse>('/upload_image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        setUploadedImages(prev => [...prev, response.data]);
      }
    } catch (error) {
      console.error('Failed to upload image:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif']
    }
  });

  return (
    <Box p={3}>
      <Typography variant="h6" gutterBottom>
        Upload Images
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Upload images to analyze with AI. Supported formats: PNG, JPG, JPEG, GIF
      </Typography>

      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          borderRadius: 2,
          p: 3,
          mb: 3,
          textAlign: 'center',
          cursor: 'pointer',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
        }}
      >
        <input {...getInputProps()} />
        {isLoading ? (
          <CircularProgress size={24} />
        ) : (
          <Typography>
            {isDragActive
              ? 'Drop the images here...'
              : 'Drag and drop images here, or click to select files'}
          </Typography>
        )}
      </Box>

      <Grid container spacing={2}>
        {uploadedImages.map((image, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Box
              sx={{
                border: '1px solid',
                borderColor: 'grey.200',
                borderRadius: 1,
                overflow: 'hidden',
              }}
            >
              <img
                src={image.image_path}
                alt={image.description}
                style={{
                  width: '100%',
                  height: '200px',
                  objectFit: 'cover',
                }}
              />
              <Box p={2}>
                <Typography variant="body2" color="text.secondary">
                  {image.description}
                </Typography>
              </Box>
            </Box>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Images; 