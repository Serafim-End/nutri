import axios, { AxiosError } from 'axios'
import { useAuthStore } from '../store/auth'
import type {
  AuthResponse,
  NutritionistProfile,
  NutritionistSearchResult,
  Service,
  AvailabilitySlot,
  IntakeAnswers,
  BookingResponse,
  Booking,
  SearchFilters,
  FiltersResponse,
  FilterOptions,
  IntakeResponse,
  PaymentIntent,
  PaymentResponse,
} from '../types'

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  } else {
    // Log warning in development to help debug auth issues
    if (import.meta.env.DEV) {
      console.warn('API request made without authentication token:', config.url)
    }
  }
  return config
})

// Handle auth errors with retry capability
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: Error | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }
    
    if (error.response?.status === 401 && !originalRequest?._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => api(originalRequest!))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Try dev login if in development mode
        if (import.meta.env.DEV) {
          const response = await api.post<AuthResponse>('/auth/dev-login')
          const { access_token, profile } = response.data
          useAuthStore.getState().setAuth(access_token, profile)
          processQueue()
          isRefreshing = false
          return api(originalRequest!)
        }
      } catch {
        processQueue(new Error('Re-authentication failed'))
        useAuthStore.getState().clearAuth()
      }
      
      isRefreshing = false
    }
    
    // Create a more descriptive error
    const errorMessage = 
      (error.response?.data as { error?: string; message?: string })?.error ||
      (error.response?.data as { error?: string; message?: string })?.message ||
      error.message ||
      'Network error'
    
    const enhancedError = new Error(errorMessage)
    ;(enhancedError as Error & { status?: number }).status = error.response?.status
    
    return Promise.reject(enhancedError)
  }
)

// Auth API
export const authApi = {
  verifyTelegram: async (initData: string): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>('/auth/telegram/verify', {
      init_data: initData,
    })
    return data
  },

  /**
   * Development-only login endpoint.
   * Uses seeded test user (telegram_user_id=300000001) by default.
   */
  devLogin: async (telegramUserId?: number): Promise<AuthResponse> => {
    const { data } = await api.post<AuthResponse>('/auth/dev-login', {
      telegram_user_id: telegramUserId,
    })
    return data
  },
}

// Client API
export const clientApi = {
  createIntake: async (answers: IntakeAnswers): Promise<IntakeResponse> => {
    const { data } = await api.post('/clients/intakes', answers)
    return data
  },

  getMatches: async (intakeId: string): Promise<{ matches: NutritionistProfile[]; total: number }> => {
    const { data } = await api.get('/clients/matches', {
      params: { intake_id: intakeId },
    })
    return data
  },

  getBookings: async (): Promise<{ bookings: Booking[] }> => {
    const { data } = await api.get('/clients/bookings')
    return data
  },

  /**
   * Get client's bookings with full details (service, slot, nutritionist).
   */
  getMyBookings: async (): Promise<{ bookings: Booking[] }> => {
    const { data } = await api.get('/clients/me/bookings')
    return data
  },

  /**
   * Get client's current filters and defaults from onboarding.
   */
  getFilters: async (): Promise<FiltersResponse> => {
    const { data } = await api.get('/clients/me/filters')
    return data
  },

  /**
   * Update client's current filters.
   */
  updateFilters: async (filters: SearchFilters): Promise<{ filters: SearchFilters; updated_at: string }> => {
    const { data } = await api.put('/clients/me/filters', { filters })
    return data
  },
}

// Public API
export const publicApi = {
  getNutritionists: async (params?: {
    specialization?: string
    budget?: number
    tags?: string[]
  }): Promise<{ nutritionists: NutritionistProfile[]; total: number }> => {
    const { data } = await api.get('/public/nutritionists', { params })
    return data
  },

  getNutritionist: async (id: string): Promise<{ nutritionist: NutritionistProfile }> => {
    const { data } = await api.get(`/public/nutritionists/${id}`)
    return data
  },

  getServices: async (nutritionistId: string): Promise<{ services: Service[] }> => {
    const { data } = await api.get(`/public/nutritionists/${nutritionistId}/services`)
    return data
  },

  getSlots: async (
    nutritionistId: string,
    serviceId?: string
  ): Promise<{ slots: AvailabilitySlot[] }> => {
    const { data } = await api.get(`/public/nutritionists/${nutritionistId}/slots`, {
      params: serviceId ? { service_id: serviceId } : undefined,
    })
    return data
  },

  /**
   * Search nutritionists with filters and scoring.
   */
  searchNutritionists: async (
    filters: SearchFilters
  ): Promise<{ nutritionists: NutritionistSearchResult[]; total: number }> => {
    const { data } = await api.post('/public/nutritionists/search', { filters })
    return data
  },

  /**
   * Get available filter options for the UI.
   */
  getFilterOptions: async (): Promise<FilterOptions> => {
    const { data } = await api.get('/public/filters/options')
    return data
  },
}

// Booking API
export const bookingApi = {
  createBooking: async (
    serviceId: string,
    slotId: string,
    clientNote?: string
  ): Promise<BookingResponse> => {
    const { data } = await api.post('/bookings', {
      service_id: serviceId,
      slot_id: slotId,
      client_note: clientNote,
    })
    return data
  },

  getBooking: async (id: string): Promise<{ booking: Booking }> => {
    const { data } = await api.get(`/bookings/${id}`)
    return data
  },

  cancelBooking: async (id: string, reason?: string): Promise<{ booking: Booking; message: string }> => {
    const { data } = await api.post(`/bookings/${id}/cancel`, { reason })
    return data
  },

  /**
   * Mark a booking as paid (DEV shortcut).
   * Routes through payment abstraction layer.
   * @deprecated Use paymentApi.simulatePayment() for new code
   */
  markPaid: async (id: string): Promise<{ booking: Booking; message: string }> => {
    const { data } = await api.post(`/bookings/${id}/mark-paid`)
    return data
  },

  /**
   * Release expired slot holds (cron endpoint).
   */
  releaseExpiredHolds: async (): Promise<{ released_count: number; message: string }> => {
    const { data } = await api.post('/bookings/release-expired-holds')
    return data
  },
}

// Payment API
export const paymentApi = {
  /**
   * Create a payment intent for a booking.
   * Returns payment URL and provider info.
   */
  createPaymentIntent: async (bookingId: string): Promise<PaymentIntent> => {
    const { data } = await api.post('/payments/create', { booking_id: bookingId })
    return data
  },

  /**
   * Simulate successful payment (DEV/mock provider only).
   * Triggers the mock webhook internally.
   */
  simulatePayment: async (bookingId: string): Promise<PaymentResponse> => {
    const { data } = await api.post(`/payments/mock-pay/${bookingId}`)
    return data
  },

  /**
   * Get payment status for a booking.
   */
  getPaymentStatus: async (bookingId: string): Promise<{ payment: PaymentResponse['payment'] }> => {
    const { data } = await api.get(`/payments/${bookingId}/status`)
    return data
  },
}

export default api
