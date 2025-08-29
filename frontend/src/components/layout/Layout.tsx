/**
 * Layout component providing consistent page structure.
 * 
 * Provides header, main content area, and footer with consistent
 * spacing and responsive design.
 */

import React from 'react';

export interface LayoutProps {
  /** Page content */
  children: React.ReactNode;
}

/**
 * Main layout component with header and footer.
 * 
 * @param props - Layout properties
 * @returns JSX.Element
 */
export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="flex items-center space-x-2">
                  <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">HSA</span>
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-gray-900">
                      Health Savings Account
                    </h1>
                    <p className="text-sm text-gray-500">Onboarding System</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Secure Application Process
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              © 2024 HSA Onboarding System. All rights reserved.
            </div>
            <div className="flex items-center space-x-6">
              <span>Secure</span>
              <span>•</span>
              <span>Compliant</span>
              <span>•</span>
              <span>Trusted</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};