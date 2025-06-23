import React from 'react';
import { Tabs, Tab, Box } from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import StorageIcon from '@mui/icons-material/Storage';
import ListAltIcon from '@mui/icons-material/ListAlt';

interface NavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Navigation: React.FC<NavigationProps> = ({ activeTab, onTabChange }) => {
  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    onTabChange(newValue);
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
      <Tabs 
        value={activeTab} 
        onChange={handleChange}
        variant="fullWidth"
      >
        <Tab 
          icon={<ChatIcon />} 
          label="Chat" 
          value="chat"
          sx={{ textTransform: 'none' }}
        />
        <Tab 
          icon={<StorageIcon />} 
          label="Context Management" 
          value="context"
          sx={{ textTransform: 'none' }}
        />
        <Tab 
          icon={<ListAltIcon />} 
          label="Stories" 
          value="stories"
          sx={{ textTransform: 'none' }}
        />
      </Tabs>
    </Box>
  );
};

export default Navigation; 