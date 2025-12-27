import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Profile } from '../types'

interface AuthState {
  token: string | null
  profile: Profile | null
  isAuthenticated: boolean
  isLoading: boolean
  setAuth: (token: string, profile: Profile) => void
  clearAuth: () => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      profile: null,
      isAuthenticated: false,
      isLoading: true,
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
        }),
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: 'nutrimatch-auth',
      partialize: (state) => ({ token: state.token, profile: state.profile }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.isAuthenticated = !!state.token
          state.isLoading = false
        }
      },
    }
  )
)


