import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { Booking, PaymentIntent } from '../types'

export default function PaymentSuccessPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as {
    booking?: Booking
    payment?: PaymentIntent
  } | null

  useEffect(() => {
    // Haptic feedback on success
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
  }, [])

  const handleClose = () => {
    // Try to close the Telegram Mini App
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.close()
    } else {
      navigate('/intake')
    }
  }

  const handleViewBookings = () => {
    // In a real app, navigate to bookings list
    navigate('/intake')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-500 to-primary-600 flex flex-col items-center justify-center px-4 text-white">
      {/* Success animation */}
      <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mb-8 animate-scale-in shadow-xl">
        <svg
          className="w-14 h-14 text-primary-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>

      <h1 className="text-2xl font-display font-bold mb-2 animate-fade-in">
        Booking Confirmed!
      </h1>

      <p className="text-white/80 text-center mb-8 animate-fade-in" style={{ animationDelay: '100ms' }}>
        Your appointment has been successfully booked.
      </p>

      {/* Booking details */}
      {state?.booking && (
        <div
          className="w-full max-w-sm bg-white/10 rounded-2xl p-4 mb-8 animate-slide-up"
          style={{ animationDelay: '200ms' }}
        >
          {state.booking.slot && (
            <div className="text-center">
              <p className="text-white/60 text-sm">Appointment Date</p>
              <p className="font-semibold text-lg">
                {format(parseISO(state.booking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
              </p>
              <p className="text-xl font-bold">
                {format(parseISO(state.booking.slot.start_at), 'HH:mm')}
              </p>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-white/10 text-center">
            <p className="text-white/60 text-sm">Amount Paid</p>
            <p className="font-bold text-xl">
              {state.booking.price_rub.toLocaleString('ru-RU')} ₽
            </p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div
        className="w-full max-w-sm space-y-3 animate-slide-up"
        style={{ animationDelay: '300ms' }}
      >
        <button
          onClick={handleViewBookings}
          className="w-full py-3 px-6 bg-white text-primary-600 font-semibold rounded-xl transition-all duration-200 hover:bg-white/90 active:scale-[0.98]"
        >
          Back to Home
        </button>

        <button
          onClick={handleClose}
          className="w-full py-3 px-6 bg-white/10 text-white font-medium rounded-xl transition-all duration-200 hover:bg-white/20 active:scale-[0.98]"
        >
          Close
        </button>
      </div>

      {/* Reminder */}
      <p
        className="mt-8 text-white/60 text-sm text-center max-w-xs animate-fade-in"
        style={{ animationDelay: '400ms' }}
      >
        You'll receive a reminder before your appointment via Telegram.
      </p>
    </div>
  )
}


