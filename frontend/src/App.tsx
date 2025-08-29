/**
 * Main App component.
 * 
 * Sets up routing, React Query client, and global providers
 * for the HSA onboarding application.
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PersonalInfoPage } from '@/pages/PersonalInfoPage';

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
      <div className="App">
        <PersonalInfoPage />
      </div>
    </QueryClientProvider>
  );
}

export default App;