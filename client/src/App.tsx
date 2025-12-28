import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useTelegramAuth } from './hooks/useTelegramAuth'
import { useAuthStore } from './store/auth'
import Layout from './components/Layout'
import IntakePage from './pages/IntakePage'
import ResultsPage from './pages/ResultsPage'
import NutritionistPage from './pages/NutritionistPage'
import BookingPage from './pages/BookingPage'
import PaymentSuccessPage from './pages/PaymentSuccessPage'
import MyBookingsPage from './pages/MyBookingsPage'
import LoadingScreen from './components/LoadingScreen'

// Dev login button component
function DevLoginButton() {
  const { devLogin, isLoading, error } = useTelegramAuth()
  const [showButton, setShowButton] = useState(false)

  useEffect(() => {
    // Only show in development and when not in Telegram
    const tg = window.Telegram?.WebApp
    if (import.meta.env.DEV && !tg?.initData) {
      setShowButton(true)
    }
  }, [])

  if (!showButton) return null

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {error && (
        <div className="mb-2 p-2 bg-red-100 text-red-700 text-xs rounded">
          {error}
        </div>
      )}
      <button
        onClick={() => devLogin()}
        disabled={isLoading}
        className="px-4 py-2 bg-gray-800 text-white text-sm rounded-lg shadow-lg hover:bg-gray-700 disabled:opacity-50"
      >
        {isLoading ? 'Logging in...' : '🔧 Dev Login'}
      </button>
    </div>
  )
}

function App() {
  const { authenticate, isLoading: authLoading } = useTelegramAuth()
  const { isAuthenticated, isLoading } = useAuthStore()

  useEffect(() => {
    // Attempt authentication on mount
    authenticate()
  }, [authenticate])

  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.ready()
      tg.expand()
      // Set header color
      tg.setHeaderColor('#22c55e')
      tg.setBackgroundColor('#ffffff')
    }
  }, [])

  if (isLoading || authLoading) {
    return (
      <>
        <LoadingScreen />
        <DevLoginButton />
      </>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/intake" replace />} />
          <Route path="intake" element={<IntakePage />} />
          <Route path="results" element={<ResultsPage />} />
          <Route path="nutritionist/:id" element={<NutritionistPage />} />
          <Route path="book/:nutritionistId/:serviceId" element={<BookingPage />} />
          <Route path="payment-success" element={<PaymentSuccessPage />} />
          <Route path="my-bookings" element={<MyBookingsPage />} />
          <Route path="bookings" element={<Navigate to="/my-bookings" replace />} />
        </Route>
      </Routes>
      <DevLoginButton />
    </BrowserRouter>
  )
}

export default App


