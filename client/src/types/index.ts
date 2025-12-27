// API Types

export interface Profile {
  id: string
  role: 'client' | 'nutritionist' | 'admin'
  telegram_user_id: number
  full_name: string
  photo_url: string | null
  created_at: string
  updated_at: string
}

export interface NutritionistProfile {
  nutritionist_id: string
  bio: string | null
  tags: string[]
  specializations: string[]
  verification_status: 'draft' | 'pending' | 'approved' | 'rejected' | 'needs_update'
  rating: number
  reviews_count: number
  is_active: boolean
  submitted_at: string | null
  verified_at: string | null
  profile?: Profile
}

export interface Service {
  id: string
  nutritionist_id: string
  title: string
  description: string | null
  duration_minutes: number
  price_rub: number
  is_active: boolean
  created_at: string
}

export interface AvailabilitySlot {
  id: string
  nutritionist_id: string
  start_at: string
  end_at: string
  status: 'free' | 'held' | 'booked' | 'cancelled'
  hold_expires_at: string | null
  created_at: string
}

export interface Booking {
  id: string
  client_id: string | null
  nutritionist_id: string | null
  service_id: string | null
  slot_id: string | null
  status: 'pending_payment' | 'paid' | 'cancelled' | 'completed' | 'no_show' | 'refunded'
  price_rub: number
  currency: string
  meeting_link: string | null
  created_at: string
  paid_at: string | null
  cancelled_at: string | null
  service?: Service
  slot?: AvailabilitySlot
}

export interface Intake {
  id: string
  client_id: string
  answers: IntakeAnswers
  created_at: string
  updated_at: string
}

export interface IntakeAnswers {
  goals: string[]
  dietary_restrictions: string[]
  budget_min: number | null
  budget_max: number | null
  preferred_schedule: string | null
  health_conditions: string[]
  additional_notes: string | null
}

export interface PaymentIntent {
  payment_id: string
  provider: string
  amount_rub: number
  currency: string
  payment_url: string
  expires_at: string | null
}

// API Response Types
export interface AuthResponse {
  access_token: string
  token_type: string
  profile: Profile
}

export interface BookingResponse {
  booking: Booking
  payment: PaymentIntent
}


