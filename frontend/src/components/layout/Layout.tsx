/**
 * Layout component for consistent page structure.
 */

import React from 'react';

export interface LayoutProps {
  /** Layout content */
  children: React.ReactNode;
}

/**
 * Layout component providing consistent page structure.
 */
export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="h-screen flex flex-col">
        {children}
      </div>
    </div>
  );
};

export default Layout;
