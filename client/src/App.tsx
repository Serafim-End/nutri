import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useTelegramAuth } from './hooks/useTelegramAuth'
import { useAuthStore } from './store/auth'
import Layout from './components/Layout'
import IntakePage from './pages/IntakePage'
import ResultsPage from './pages/ResultsPage'
import NutritionistPage from './pages/NutritionistPage'
import BookingPage from './pages/BookingPage'
import PaymentSuccessPage from './pages/PaymentSuccessPage'
import LoadingScreen from './components/LoadingScreen'

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
    return <LoadingScreen />
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
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App


