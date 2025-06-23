import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, TextField, IconButton, Typography, CircularProgress, Grid } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import ImageIcon from '@mui/icons-material/Image';
import ReactMarkdown from 'react-markdown';
import { useDropzone } from 'react-dropzone';
import { api } from '../services/api';
import { useProject } from '../contexts/ProjectContext';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: Array<{
    type: string;
    url: string;
    name: string;
    description?: string;
  }>;
  generatedStories?: Array<{
    id: string;
    title: string;
    description: string;
    published: boolean;
  }>;
}

const Chat = () => {
  const { selectedProject } = useProject();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = async (file: File) => {
    if (!selectedProject) {
      alert('Please select a project first');
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_key', selectedProject);

      let response;
      if (file.type.startsWith('image/')) {
        response = await api.post('/upload_image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        const newMessage: Message = {
          id: Date.now().toString(),
          type: 'user',
          content: 'Uploaded image:',
          timestamp: new Date(),
          attachments: [{
            type: 'image',
            url: response.data.image_path,
            name: file.name,
            description: response.data.description
          }]
        };
        setMessages(prev => [...prev, newMessage]);

        // Add AI's response about the image
        if (response.data.description) {
          const aiResponse: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: response.data.description,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, aiResponse]);
        }
      } else {
        // Handle other file types (BRDs, docs, etc.)
        const fileContent = await file.text();
        const newMessage: Message = {
          id: Date.now().toString(),
          type: 'user',
          content: `Uploaded document: ${file.name}`,
          timestamp: new Date(),
          attachments: [{
            type: 'file',
            url: URL.createObjectURL(file),
            name: file.name
          }]
        };
        setMessages(prev => [...prev, newMessage]);

        // Send the file content to the chat endpoint
        const chatResponse = await api.post('/chat', {
          message: `Please analyze this document:\n${fileContent}`,
          project_key: selectedProject
        });

        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: chatResponse.data.response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedProject) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.post('/chat', {
        message: input,
        project_key: selectedProject
      });

      // Check if the response contains story-like content
      const storyMatch = response.data.response.match(/Story Title: (.*?)\nDescription: (.*?)(?:\n|$)/g);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      };

      // If stories were generated, extract and store them
      if (storyMatch) {
        const stories = storyMatch.map((match: string) => {
          const titleMatch = match.match(/Story Title: (.*?)\n/);
          const descMatch = match.match(/Description: (.*?)(?:\n|$)/);
          return {
            id: Date.now().toString() + Math.random(),
            title: titleMatch ? titleMatch[1] : 'Untitled Story',
            description: descMatch ? descMatch[1] : 'No description',
            published: false
          };
        });

        if (stories.length > 0) {
          assistantMessage.generatedStories = stories;
          
          // Store each story
          for (const story of stories) {
            try {
              await api.post('/stories', {
                project_key: selectedProject,
                story
              });
            } catch (error) {
              console.error('Failed to store story:', error);
            }
          }
        }
      }

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Failed to process your message. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Messages */}
      <Box sx={{ 
        flex: 1, 
        overflowY: 'auto', 
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2
      }}>
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: message.type === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <Paper
              sx={{
                p: 2,
                maxWidth: '70%',
                bgcolor: message.type === 'user' ? 'primary.main' : 'background.paper',
                color: message.type === 'user' ? 'white' : 'text.primary',
              }}
            >
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {message.attachments?.map((attachment, index) => (
                <Box key={index} sx={{ mt: 2 }}>
                  {attachment.type === 'image' ? (
                    <Box>
                      <img
                        src={attachment.url}
                        alt={attachment.description || 'Uploaded image'}
                        style={{
                          maxWidth: '100%',
                          maxHeight: '300px',
                          borderRadius: 4
                        }}
                      />
                      {attachment.description && (
                        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                          {attachment.description}
                        </Typography>
                      )}
                    </Box>
                  ) : (
                    <Typography variant="body2">
                      📎 {attachment.name}
                    </Typography>
                  )}
                </Box>
              ))}
            </Paper>
            <Typography variant="caption" color="text.secondary" sx={{ px: 1 }}>
              {message.timestamp.toLocaleTimeString()}
            </Typography>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileUpload(file);
              e.target.value = ''; // Reset input
            }}
          />
          <input
            type="file"
            ref={imageInputRef}
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileUpload(file);
              e.target.value = ''; // Reset input
            }}
          />
          <IconButton 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading || !selectedProject}
          >
            <AttachFileIcon />
          </IconButton>
          <IconButton 
            onClick={() => imageInputRef.current?.click()}
            disabled={isUploading || !selectedProject}
          >
            <ImageIcon />
          </IconButton>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading || isUploading || !selectedProject}
            sx={{ bgcolor: 'background.default' }}
          />
          <IconButton 
            onClick={handleSend} 
            disabled={!input.trim() || isLoading || isUploading || !selectedProject}
            color="primary"
          >
            {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
          </IconButton>
        </Box>
        {(isUploading || !selectedProject) && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {!selectedProject 
              ? 'Please select a project to start chatting'
              : 'Uploading file...'}
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default Chat;