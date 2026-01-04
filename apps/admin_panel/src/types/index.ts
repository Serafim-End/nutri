export interface AdminUser {
  id: string
  email: string
  name: string
  role: 'admin'
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: AdminUser
}

export interface Nutritionist {
  id: string
  profile_id: string
  full_name: string
  bio: string | null
  specializations: string[]
  languages: string[]
  hourly_rate: number
  currency: string
  years_experience: number
  verification_status: 'pending' | 'approved' | 'rejected' | 'needs_update'
  is_active: boolean
  submitted_at: string | null
  verified_at: string | null
  created_at: string
  profile?: {
    telegram_user_id: number
    photo_url: string | null
  }
}

export interface Document {
  id: string
  nutritionist_id: string
  document_type: string
  file_url: string
  status: 'pending' | 'accepted' | 'rejected'
  review_note: string | null
  created_at: string
}

export interface Booking {
  id: string
  client_id: string
  nutritionist_id: string
  service_id: string
  start_time: string
  end_time: string
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled'
  created_at: string
}

export interface DashboardStats {
  total_users: number
  total_nutritionists: number
  pending_verifications: number
  total_bookings: number
  revenue_this_month: number
}

