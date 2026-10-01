import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import { App } from './App'
import { AuthProvider } from './auth/AuthContext'
import './styles/tokens.css'
import './styles/app.css'

const container = document.getElementById('root')

if (container === null) {
  throw new Error('index.html has no #root element for the app to mount into')
}

createRoot(container).render(
  <StrictMode>
    {/* The client is served under /app, so its router is based there too —
        otherwise every link would resolve against the API's root. */}
    <BrowserRouter basename="/app">
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
