import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { checkJiraConnection, api } from '../services/api';

interface Project {
  id: string;
  name: string;
  key: string;
}

interface ProjectContextType {
  selectedProject: string | null;
  setSelectedProject: (project: string | null) => void;
  projects: Project[];
  setProjects: (projects: Project[]) => void;
  loading: boolean;
  error: string | null;
  isJiraConnected: boolean;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isJiraConnected, setIsJiraConnected] = useState(false);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const healthData = await checkJiraConnection();
        const jiraConnected = healthData.services.jira === 'connected';
        setIsJiraConnected(jiraConnected);
        
        if (!jiraConnected) {
          setError('Failed to connect to Jira. Please check your connection.');
          setProjects([]);
          return;
        }

        // Fetch real projects from Jira
        const response = await api.get('/jira/projects');
        const projectData = response.data;
        
        // Ensure we have an array of projects
        if (Array.isArray(projectData)) {
          setProjects(projectData);
        } else {
          console.error('Unexpected projects data format:', projectData);
          setProjects([]);
          setError('Failed to load projects. Unexpected data format.');
        }
      } catch (err) {
        console.error('Failed to check Jira connection:', err);
        setError('Failed to connect to Jira. Please check your connection.');
        setIsJiraConnected(false);
        setProjects([]);
      } finally {
        setLoading(false);
      }
    };

    checkConnection();
  }, []);

  return (
    <ProjectContext.Provider
      value={{
        selectedProject,
        setSelectedProject,
        projects,
        setProjects,
        loading,
        error,
        isJiraConnected
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}; 