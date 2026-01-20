import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/auth'

import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { NutritionistsPage } from '@/pages/NutritionistsPage'
import { NutritionistDetailPage } from '@/pages/NutritionistDetailPage'
import { UsersPage } from '@/pages/UsersPage'
import { UserDetailPage } from '@/pages/UserDetailPage'
import { BookingsPage } from '@/pages/BookingsPage'
import { PaymentsPage } from '@/pages/PaymentsPage'
import { ReviewsPage } from '@/pages/ReviewsPage'
import { SupportPage } from '@/pages/SupportPage'
import { SettingsPage } from '@/pages/SettingsPage'

import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'

function App() {
  const { setLoading, isAuthenticated } = useAuthStore()

  // Check if we have persisted auth on mount
  useEffect(() => {
    // Small delay to ensure hydration from localStorage
    const timer = setTimeout(() => {
      setLoading(false)
    }, 100)
    return () => clearTimeout(timer)
  }, [setLoading])

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />

      {/* Protected routes */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="nutritionists" element={<NutritionistsPage />} />
        <Route path="nutritionists/:id" element={<NutritionistDetailPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="users/:id" element={<UserDetailPage />} />
        <Route path="bookings" element={<BookingsPage />} />
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="reviews" element={<ReviewsPage />} />
        <Route path="support" element={<SupportPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
