import axios from 'axios';

const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  services: {
    storage: string;
    jira: 'connected' | 'not_configured';
    llm_providers: string[];
  };
}

// API functions
export const checkJiraConnection = async () => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

export const syncJiraProject = async (projectKey: string) => {
  const response = await api.post('/sync_jira', {
    project_key: projectKey,
    max_results: 50
  });
  return response.data;
}; 