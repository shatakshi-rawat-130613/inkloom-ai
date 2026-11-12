/**
 * Inkloom AI main application component with client routing and Auth provider.
 */

import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import { Footer } from './components/Footer'
import { Navbar } from './components/Navbar'
import { AuthProvider } from './context/AuthContext'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { SelectBrandPage } from './pages/SelectBrandPage'
import { SubmissionDetailPage } from './pages/SubmissionDetailPage'
import { SubmitPage } from './pages/SubmitPage'
import { TermsPage } from './pages/TermsPage'
import { WorkspacePage } from './pages/WorkspacePage'

function NotFoundPage() {
  return (
    <div className="mx-auto max-w-xl px-6 py-24 text-center space-y-4">
      <h1 className="font-serif text-3xl font-bold text-ink">Page Not Found</h1>
      <p className="text-sm text-ink-soft">
        The requested resource does not exist in the Inkloom AI workspace.
      </p>
      <Link
        to="/"
        className="inline-block mt-4 px-4 py-2 bg-parchment text-ink text-xs font-semibold rounded-sm border border-parchment-deep hover:bg-parchment-deep transition-colors"
      >
        Return to Home
      </Link>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-ivory text-ink selection:bg-sage-soft selection:text-ink">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/select-brand" element={<SelectBrandPage />} />
              <Route path="/workspace" element={<WorkspacePage />} />
              <Route path="/submissions/new" element={<SubmitPage />} />
              <Route path="/submissions/:id" element={<SubmissionDetailPage />} />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
