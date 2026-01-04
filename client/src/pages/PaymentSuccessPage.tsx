import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { Booking, PaymentIntent } from '../types'
import {
  Stack,
  Card,
  Button,
  Heading,
  Text,
  Icons,
} from '../design-system'

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
    navigate('/my-bookings')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-500 to-primary-600 flex flex-col items-center justify-center px-4 text-white">
      {/* Success animation */}
      <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mb-8 animate-scale-in shadow-xl">
        <Icons.CheckCircle size="xl" className="w-14 h-14 text-primary-500" />
      </div>

      <Heading level="h1" size="2xl" className="text-white text-center animate-fade-in">
        Booking Confirmed!
      </Heading>

      <Text className="text-white/80 text-center mt-2 animate-fade-in" style={{ animationDelay: '100ms' }}>
        Your appointment has been successfully booked.
      </Text>

      {/* Booking details */}
      {state?.booking && (
        <Card
          variant="elevated"
          padding="lg"
          className="w-full max-w-sm mt-8 bg-white/10 border-none animate-slide-up"
          style={{ animationDelay: '200ms' }}
        >
          {state.booking.slot && (
            <div className="text-center text-white">
              <Text size="sm" className="text-white/60">Appointment Date</Text>
              <Text weight="semibold" size="lg" className="text-white">
                {format(parseISO(state.booking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
              </Text>
              <Text size="xl" weight="bold" className="text-white">
                {format(parseISO(state.booking.slot.start_at), 'HH:mm')}
              </Text>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-white/10 text-center">
            <Text size="sm" className="text-white/60">Amount Paid</Text>
            <Text size="xl" weight="bold" className="text-white">
              {state.booking.price_rub.toLocaleString('ru-RU')} ₽
            </Text>
          </div>
        </Card>
      )}

      {/* Actions */}
      <Stack
        gap={3}
        className="w-full max-w-sm mt-8 animate-slide-up"
        style={{ animationDelay: '300ms' }}
      >
        <Button
          onClick={handleViewBookings}
          variant="secondary"
          fullWidth
          className="bg-white text-primary-600 hover:bg-white/90"
        >
          View My Bookings
        </Button>

        <Button
          onClick={handleClose}
          variant="ghost"
          fullWidth
          className="text-white bg-white/10 hover:bg-white/20"
        >
          Close
        </Button>
      </Stack>

      {/* Reminder */}
      <Text
        size="sm"
        className="mt-8 text-white/60 text-center max-w-xs animate-fade-in"
        style={{ animationDelay: '400ms' }}
      >
        You'll receive a reminder before your appointment via Telegram.
      </Text>
    </div>
  )
}
