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

export interface AdminUserEntry {
  id: string
  role: 'client' | 'nutritionist' | 'admin'
  telegram_user_id: number
  telegram_username: string | null
  full_name: string
  photo_url: string | null
  first_mini_app_at: string | null
  last_mini_app_at: string | null
  first_bot_start_at: string | null
  last_bot_start_at: string | null
  first_nutritionist_intent_at: string | null
  last_nutritionist_intent_at: string | null
  last_seen_at: string | null
  last_seen_source: 'mini_app' | 'bot_start' | 'nutritionist_intent' | null
  has_nutritionist_profile: boolean
  is_client: boolean
  user_statuses: Array<'client' | 'nutritionist' | 'nutritionist_intent'>
  login_count: number
  login_sessions: AdminUserSession[]
  last_session: AdminUserSession | null
  created_at: string
  updated_at: string
}

export interface AdminUserSession {
  id: string
  source: 'mini_app' | 'bot_start' | 'nutritionist_intent'
  started_at: string
  booking_made: boolean
  payment_made: boolean
}

export interface AdminUsersResponse {
  users: AdminUserEntry[]
  total: number
  page: number
  pages: number
  stats: {
    total_users: number
    mini_app_users: number
    bot_start_users: number
    nutritionist_intent_users: number
    clients_only?: number
    nutritionists_only?: number
    nutritionists_and_clients?: number
  }
}

export interface Nutritionist {
  id: string
  nutritionist_id: string
  full_name: string
  bio: string | null
  specializations: string[]
  languages?: string[] // Optional - not currently stored in backend
  hourly_rate?: number // Optional - not currently stored in backend
  currency?: string // Optional - not currently stored in backend
  years_experience?: number // Optional - not currently stored in backend
  verification_status: 'pending' | 'approved' | 'rejected' | 'needs_update'
  is_active: boolean
  submitted_at: string | null
  verified_at: string | null
  created_at: string
  profile?: {
    telegram_user_id: number
    telegram_username?: string | null
    photo_url: string | null
  }
}

export interface NutritionistDocument {
  id: string
  nutritionist_id: string
  type: string
  file_path: string
  status: 'uploaded' | 'accepted' | 'rejected'
  review_note: string | null
  uploaded_at: string
}

export interface NutritionistDetail extends Nutritionist {
  documents?: NutritionistDocument[]
}

export interface BookingSlot {
  id: string
  nutritionist_id: string
  start_at: string
  end_at: string
  status: string
}

export interface BookingService {
  id: string
  title: string
  description?: string
  duration_minutes: number
  price_rub: number
}

export interface AdminService {
  id: string
  nutritionist_id: string
  title: string
  description: string | null
  duration_minutes: number
  price_rub: number
  is_active: boolean
  created_at: string
}

export interface WorkingHoursTemplate {
  id: string | null
  nutritionist_id: string
  weekly_schedule: Record<string, Array<{ start: string; end: string }>>
  created_at: string | null
  updated_at: string | null
}

export interface BookingClient {
  id: string
  full_name: string
  photo_url: string | null
  telegram_user_id: number
}

export interface BookingNutritionist {
  id: string
  full_name: string
}

export interface BookingPayment {
  id: string
  provider: string
  status: string
  amount: number
  currency: string
  created_at: string
  paid_at: string | null
}

export interface Booking {
  id: string
  client_id: string | null
  nutritionist_id: string | null
  service_id: string | null
  slot_id: string | null
  status: 'pending_payment' | 'paid' | 'completed' | 'cancelled' | 'no_show' | 'refunded'
  price_rub: number
  currency: string
  meeting_link: string | null
  created_at: string
  paid_at: string | null
  cancelled_at: string | null
  // Expanded relations
  client?: BookingClient
  nutritionist?: BookingNutritionist
  slot?: BookingSlot
  service?: BookingService
  payment?: BookingPayment
}

export interface BookingsListResponse {
  bookings: Booking[]
  total: number
  page: number
  pages: number
}

export interface DashboardStats {
  total_users: number
  total_nutritionists: number
  pending_verifications: number
  total_bookings: number
  revenue_this_month: number
}

export interface SupportTicket {
  id: string
  author_id: string
  author_name: string | null
  role: 'client' | 'nutritionist'
  text: string
  booking_id: string | null
  status: 'open' | 'closed'
  created_at: string
}

export interface Review {
  id: string
  booking_id: string
  rating: number
  text: string | null
  nutritionist_id: string
  nutritionist_name: string
  client_id: string
  is_hidden: boolean
  is_problematic: boolean
  created_at: string
}

export interface Payment {
  id: string
  booking_id: string
  nutritionist_name: string
  amount: number
  currency: string
  status: 'pending' | 'completed' | 'failed' | 'refunded'
  provider: string
  created_at: string
}
