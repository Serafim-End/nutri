import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/store/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await api.post('/admin/auth/login', { email, password })
    return response.data
  },
  
  logout: async () => {
    await api.post('/admin/auth/logout')
  },
  
  me: async () => {
    const response = await api.get('/admin/auth/me')
    return response.data
  },
}

// Admin API
export const adminApi = {
  // Dashboard
  getStats: async () => {
    const response = await api.get('/admin/stats')
    return response.data
  },

  // Nutritionists
  getNutritionists: async (status?: string) => {
    const params = status ? { status } : {}
    const response = await api.get('/admin/nutritionists', { params })
    return response.data
  },

  // Users
  getUsers: async (params?: { page?: number; limit?: number }) => {
    const response = await api.get('/admin/users', { params })
    return response.data
  },

  getNutritionist: async (id: string) => {
    const response = await api.get(`/admin/nutritionists/${id}`)
    return response.data
  },

  updateNutritionistBio: async (id: string, bio: string | null) => {
    const response = await api.put(`/admin/nutritionists/${id}/bio`, { bio })
    return response.data
  },

  getNutritionistServices: async (id: string) => {
    const response = await api.get(`/admin/nutritionists/${id}/services`)
    return response.data
  },

  createNutritionistService: async (id: string, payload: {
    title: string
    description?: string | null
    duration_minutes: number
    price_rub: number
    is_active?: boolean
  }) => {
    const response = await api.post(`/admin/nutritionists/${id}/services`, payload)
    return response.data
  },

  updateNutritionistService: async (nutritionistId: string, serviceId: string, payload: {
    title?: string
    description?: string | null
    duration_minutes?: number
    price_rub?: number
    is_active?: boolean
  }) => {
    const response = await api.put(
      `/admin/nutritionists/${nutritionistId}/services/${serviceId}`,
      payload
    )
    return response.data
  },

  deleteNutritionistService: async (nutritionistId: string, serviceId: string) => {
    const response = await api.delete(
      `/admin/nutritionists/${nutritionistId}/services/${serviceId}`
    )
    return response.data
  },

  getWorkingHoursTemplate: async (nutritionistId: string) => {
    const response = await api.get(
      `/admin/nutritionists/${nutritionistId}/working-hours-template`
    )
    return response.data
  },

  updateWorkingHoursTemplate: async (
    nutritionistId: string,
    weeklySchedule: Record<string, Array<{ start: string; end: string }>>
  ) => {
    const response = await api.put(
      `/admin/nutritionists/${nutritionistId}/working-hours-template`,
      { weekly_schedule: weeklySchedule }
    )
    return response.data
  },

  approveNutritionist: async (id: string, note?: string) => {
    const response = await api.post(`/admin/nutritionists/${id}/approve`, { note })
    return response.data
  },

  rejectNutritionist: async (id: string, reason: string) => {
    const response = await api.post(`/admin/nutritionists/${id}/reject`, { reason })
    return response.data
  },

  requestUpdate: async (id: string, notes: string) => {
    const response = await api.post(`/admin/nutritionists/${id}/request-update`, { notes })
    return response.data
  },

  disableNutritionist: async (id: string) => {
    const response = await api.post(`/admin/nutritionists/${id}/disable`)
    return response.data
  },

  getDocumentUrl: async (id: string) => {
    const response = await api.get(`/admin/documents/${id}/url`)
    return response.data
  },

  // Documents
  reviewDocument: async (id: string, status: 'accepted' | 'rejected', note?: string) => {
    const response = await api.post(`/admin/documents/${id}/review`, { status, note })
    return response.data
  },

  // Bookings
  getBookings: async (params: {
    page?: number
    limit?: number
    status?: string
    date_from?: string
    date_to?: string
  } = {}) => {
    const response = await api.get('/admin/bookings', { params })
    return response.data
  },

  getBooking: async (id: string) => {
    const response = await api.get(`/admin/bookings/${id}`)
    return response.data
  },

  cancelBooking: async (id: string, reason?: string) => {
    const response = await api.post(`/admin/bookings/${id}/cancel`, { reason })
    return response.data
  },

  completeBooking: async (id: string, notes?: string) => {
    const response = await api.post(`/admin/bookings/${id}/complete`, { notes })
    return response.data
  },

  // Reviews
  getReviews: async (params?: {
    rating_lte?: number
    nutritionist_id?: string
    page?: number
    limit?: number
  }) => {
    const response = await api.get('/admin/reviews', { params })
    return response.data
  },

  hideReview: async (id: string) => {
    const response = await api.post(`/admin/reviews/${id}/hide`)
    return response.data
  },

  showReview: async (id: string) => {
    const response = await api.post(`/admin/reviews/${id}/show`)
    return response.data
  },

  updateReview: async (id: string, payload: { rating?: number; comment?: string | null }) => {
    const response = await api.put(`/admin/reviews/${id}`, payload)
    return response.data
  },

  markReviewProblematic: async (id: string, problematic: boolean) => {
    const response = await api.post(`/admin/reviews/${id}/problematic`, { problematic })
    return response.data
  },

  deleteReview: async (id: string) => {
    const response = await api.delete(`/admin/reviews/${id}`)
    return response.data
  },

  // Payments
  getPayments: async (params?: {
    status?: string
    from?: string
    to?: string
  }) => {
    const response = await api.get('/admin/payments', { params })
    return response.data
  },

  exportPaymentsCsv: async (from?: string, to?: string) => {
    const params: Record<string, string> = {}
    if (from) params.from = from
    if (to) params.to = to
    const response = await api.get('/admin/payments/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  // Support
  getSupportTickets: async (status?: string) => {
    const params = status ? { status } : {}
    const response = await api.get('/admin/support/tickets', { params })
    return response.data
  },

  closeSupportTicket: async (id: string) => {
    const response = await api.post(`/admin/support/tickets/${id}/close`)
    return response.data
  },
}
