/**
 * Application entry point.
 * 
 * Renders the React application with necessary providers and
 * global CSS imports.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)