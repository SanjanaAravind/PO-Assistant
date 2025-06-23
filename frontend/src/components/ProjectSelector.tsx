import React, { useState, useEffect } from 'react';
import { Box, TextField, Autocomplete, CircularProgress } from '@mui/material';
import { useProject } from '../contexts/ProjectContext';

const ProjectSelector = () => {
  const { projects, selectedProject, setSelectedProject, loading } = useProject();
  const [inputValue, setInputValue] = useState('');
  const [open, setOpen] = useState(false);

  // Filter out any invalid project objects
  const validProjects = Array.isArray(projects) 
    ? projects.filter(project => project && typeof project === 'object' && 'key' in project && 'name' in project)
    : [];

  return (
    <Box sx={{ width: '100%', mb: 2 }}>
      <Autocomplete
        id="project-selector"
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        value={validProjects.find(p => p.key === selectedProject) || null}
        onChange={(event, newValue) => {
          setSelectedProject(newValue?.key || '');
        }}
        inputValue={inputValue}
        onInputChange={(event, newInputValue) => {
          setInputValue(newInputValue);
        }}
        options={validProjects}
        getOptionLabel={(option) => `${option.name} (${option.key})`}
        loading={loading}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Project"
            placeholder="Select a project"
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <React.Fragment>
                  {loading ? <CircularProgress color="inherit" size={20} /> : null}
                  {params.InputProps.endAdornment}
                </React.Fragment>
              ),
            }}
          />
        )}
        sx={{
          '& .MuiOutlinedInput-root': {
            backgroundColor: 'background.paper',
            '&:hover': {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: 'primary.main',
              },
            },
          },
          '& .MuiAutocomplete-popupIndicator': {
            transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 200ms',
          },
        }}
        ListboxProps={{
          sx: {
            maxHeight: '300px',
            '& .MuiAutocomplete-option': {
              padding: '8px 16px',
              '&:hover': {
                backgroundColor: 'action.hover',
              },
              '&.Mui-focused': {
                backgroundColor: 'action.selected',
              },
            },
          },
        }}
        noOptionsText="No projects found"
        filterOptions={(options, { inputValue }) => {
          const searchTerm = inputValue.toLowerCase();
          return options.filter(
            option => 
              option.name.toLowerCase().includes(searchTerm) || 
              option.key.toLowerCase().includes(searchTerm)
          );
        }}
      />
    </Box>
  );
};

export default ProjectSelector; 