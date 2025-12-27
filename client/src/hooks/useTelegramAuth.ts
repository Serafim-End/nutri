import { useState, useCallback } from 'react'
import { useAuthStore } from '../store/auth'
import { authApi } from '../lib/api'

export function useTelegramAuth() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { setAuth, setLoading, token } = useAuthStore()

  const authenticate = useCallback(async () => {
    // If already authenticated, skip
    if (token) {
      setLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const tg = window.Telegram?.WebApp
      let initData: string

      if (tg?.initData) {
        // Real Telegram Mini App environment
        initData = tg.initData
      } else {
        // Development fallback - use test data
        // Format: test_<telegram_user_id>_<first_name>_<last_name>
        initData = 'test_123456789_Test_User'
        console.log('Development mode: Using test initData')
      }

      const response = await authApi.verifyTelegram(initData)
      setAuth(response.access_token, response.profile)

      // Notify Telegram that we're ready
      tg?.ready()
    } catch (err) {
      console.error('Authentication failed:', err)
      setError('Failed to authenticate. Please try again.')
      setLoading(false)
    } finally {
      setIsLoading(false)
    }
  }, [token, setAuth, setLoading])

  return {
    authenticate,
    isLoading,
    error,
  }
}


