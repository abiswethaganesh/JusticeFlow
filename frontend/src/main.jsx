import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ComplaintWorkflowProvider } from './context/ComplaintWorkflowContext'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ComplaintWorkflowProvider>
        <App />
      </ComplaintWorkflowProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
