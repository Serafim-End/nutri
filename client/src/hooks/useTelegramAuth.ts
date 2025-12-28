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

      if (tg?.initData) {
        // Real Telegram Mini App environment
        console.log('Authenticating with Telegram initData')
        const response = await authApi.verifyTelegram(tg.initData)
        setAuth(response.access_token, response.profile)
        tg.ready()
      } else if (import.meta.env.DEV) {
        // Development mode fallback - use dev login endpoint
        console.log('Development mode: Using dev login endpoint')
        try {
          const response = await authApi.devLogin()
          setAuth(response.access_token, response.profile)
          console.log('Dev login successful:', response.profile.full_name)
        } catch (devError) {
          console.error('Dev login failed:', devError)
          // Try legacy test initData as fallback
          const initData = 'test_300000001_Test_Client'
          try {
            const response = await authApi.verifyTelegram(initData)
            setAuth(response.access_token, response.profile)
          } catch {
            throw new Error('Development authentication failed. Make sure to run "make seed" first.')
          }
        }
      } else {
        // Production mode without Telegram - show error
        setError('Please open this app in Telegram.')
        setLoading(false)
        return
      }
    } catch (err) {
      console.error('Authentication failed:', err)
      setError('Failed to authenticate. Please try again.')
      setLoading(false)
    } finally {
      setIsLoading(false)
    }
  }, [token, setAuth, setLoading])

  /**
   * Manual dev login (for UI button in development)
   */
  const devLogin = useCallback(async (telegramUserId?: number) => {
    if (!import.meta.env.DEV) {
      setError('Dev login is only available in development mode.')
      return false
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await authApi.devLogin(telegramUserId)
      setAuth(response.access_token, response.profile)
      console.log('Dev login successful:', response.profile.full_name)
      return true
    } catch (err) {
      console.error('Dev login failed:', err)
      setError('Dev login failed. Make sure backend is running and seeded.')
      return false
    } finally {
      setIsLoading(false)
    }
  }, [setAuth])

  return {
    authenticate,
    devLogin,
    isLoading,
    error,
  }
}
