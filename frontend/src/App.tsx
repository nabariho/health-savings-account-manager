/**
 * Main App component.
 * 
 * Sets up routing, React Query client, and global providers
 * for the HSA onboarding application.
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PersonalInfoPage } from '@/pages/PersonalInfoPage';
import { ChatPage } from '@/pages/ChatPage';
import { DocumentUploadPage } from '@/pages/DocumentUploadPage';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

/**
 * Main application component with providers.
 * 
 * @returns JSX.Element
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Routes>
            {/* Default route - redirect to chat */}
            <Route path="/" element={<Navigate to="/chat" replace />} />
            
            {/* Chat page - main entry point */}
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/chat/:applicationId" element={<ChatPage />} />
            
            {/* Application flow */}
            <Route path="/personal-info" element={<PersonalInfoPage />} />
            <Route path="/documents" element={<DocumentUploadPage />} />
            
            {/* Catch-all route - redirect to chat */}
            <Route path="*" element={<Navigate to="/chat" replace />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;