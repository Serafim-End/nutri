import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Profile } from '../types'

interface AuthState {
  token: string | null
  profile: Profile | null
  isAuthenticated: boolean
  isLoading: boolean
  hasCompletedOnboarding: boolean
  setAuth: (token: string, profile: Profile) => void
  clearAuth: () => void
  setLoading: (loading: boolean) => void
  setOnboardingCompleted: () => void
  resetOnboarding: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      profile: null,
      isAuthenticated: false,
      isLoading: true,
      hasCompletedOnboarding: false,
      setAuth: (token, profile) =>
        set({
          token,
          profile,
          isAuthenticated: true,
          isLoading: false,
        }),
      clearAuth: () =>
        set({
          token: null,
          profile: null,
          isAuthenticated: false,
          isLoading: false,
          hasCompletedOnboarding: false,
        }),
      setLoading: (loading) => set({ isLoading: loading }),
      setOnboardingCompleted: () => set({ hasCompletedOnboarding: true }),
      resetOnboarding: () => set({ hasCompletedOnboarding: false }),
    }),
    {
      name: 'nutrimatch-auth',
      partialize: (state) => ({
        token: state.token,
        profile: state.profile,
        hasCompletedOnboarding: state.hasCompletedOnboarding,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.isAuthenticated = !!state.token
          state.isLoading = false
        }
      },
    }
  )
)


