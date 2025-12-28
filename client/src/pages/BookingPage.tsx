import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { publicApi, bookingApi, paymentApi } from '../lib/api'
import { useCountdown } from '../hooks/useCountdown'
import SlotPicker from '../components/SlotPicker'
import LoadingScreen from '../components/LoadingScreen'
import type { AvailabilitySlot, Booking, PaymentIntent } from '../types'

type BookingState = 'select_slot' | 'pending_payment' | 'paid' | 'cancelled' | 'expired'

export default function BookingPage() {
  const { nutritionistId, serviceId } = useParams<{
    nutritionistId: string
    serviceId: string
  }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null)
  const [bookingState, setBookingState] = useState<BookingState>('select_slot')
  const [currentBooking, setCurrentBooking] = useState<Booking | null>(null)
  const [paymentInfo, setPaymentInfo] = useState<PaymentIntent | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Countdown for hold expiration
  const holdExpiresAt = currentBooking?.slot?.hold_expires_at
  const countdown = useCountdown(holdExpiresAt)

  // When countdown expires, update state
  if (countdown.isExpired && bookingState === 'pending_payment' && currentBooking) {
    setBookingState('expired')
  }

  const { data: nutritionistData, isLoading: loadingNutritionist } = useQuery({
    queryKey: ['nutritionist', nutritionistId],
    queryFn: () => publicApi.getNutritionist(nutritionistId!),
    enabled: !!nutritionistId,
  })

  const { data: servicesData, isLoading: loadingServices } = useQuery({
    queryKey: ['services', nutritionistId],
    queryFn: () => publicApi.getServices(nutritionistId!),
    enabled: !!nutritionistId,
  })

  const { data: slotsData, isLoading: loadingSlots, refetch: refetchSlots } = useQuery({
    queryKey: ['slots', nutritionistId, serviceId],
    queryFn: () => publicApi.getSlots(nutritionistId!, serviceId),
    enabled: !!nutritionistId,
  })

  // Create booking mutation
  const bookingMutation = useMutation({
    mutationFn: () => bookingApi.createBooking(serviceId!, selectedSlot!.id),
    onSuccess: (data) => {
      setCurrentBooking(data.booking)
      setPaymentInfo(data.payment)
      setBookingState('pending_payment')
      setError(null)
      // Haptic feedback
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')
    },
    onError: (err: Error & { response?: { status?: number; data?: { error?: string } } }) => {
      const errorMessage = err.response?.data?.error || 'Failed to create booking'
      if (err.response?.status === 409) {
        setError('This slot was just booked by someone else. Please choose another.')
        refetchSlots()
      } else {
        setError(errorMessage)
      }
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error')
    },
  })

  // Simulate payment mutation (uses payment abstraction layer)
  const simulatePaymentMutation = useMutation({
    mutationFn: () => {
      // Use the new payment API for mock payments
      // This goes through the proper payment abstraction
      if (paymentInfo?.provider === 'mock') {
        return paymentApi.simulatePayment(currentBooking!.id)
      }
      // Fallback to legacy endpoint for backward compatibility
      return bookingApi.markPaid(currentBooking!.id)
    },
    onSuccess: (data) => {
      setCurrentBooking(data.booking)
      setBookingState('paid')
      queryClient.invalidateQueries({ queryKey: ['my-bookings'] })
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
    },
    onError: (err: Error & { response?: { data?: { error?: string } } }) => {
      const errorMessage = err.response?.data?.error || 'Payment failed'
      if (errorMessage.toLowerCase().includes('expired')) {
        setBookingState('expired')
      }
      setError(errorMessage)
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error')
    },
  })

  // Cancel booking mutation
  const cancelMutation = useMutation({
    mutationFn: () => bookingApi.cancelBooking(currentBooking!.id, 'User cancelled'),
    onSuccess: (data) => {
      setCurrentBooking(data.booking)
      setBookingState('cancelled')
      refetchSlots()
      queryClient.invalidateQueries({ queryKey: ['my-bookings'] })
    },
    onError: (err: Error & { response?: { data?: { error?: string } } }) => {
      setError(err.response?.data?.error || 'Failed to cancel booking')
    },
  })

  if (loadingNutritionist || loadingServices || loadingSlots) {
    return <LoadingScreen />
  }

  const nutritionist = nutritionistData?.nutritionist
  const service = servicesData?.services?.find((s) => s.id === serviceId)
  const slots = slotsData?.slots || []

  if (!nutritionist || !service) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-gray-500">Service not found.</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 text-primary-600 font-medium"
          >
            Go back
          </button>
        </div>
      </div>
    )
  }

  const handleBook = () => {
    if (selectedSlot) {
      setError(null)
      bookingMutation.mutate()
    }
  }

  const handlePayment = () => {
    // For mock provider, simulate payment success
    if (paymentInfo?.provider === 'mock') {
      simulatePaymentMutation.mutate()
      return
    }
    
    // For real providers, redirect to payment URL
    // This will be implemented when real providers are added
    if (paymentInfo?.payment_url) {
      // In future: redirect to payment URL or open payment modal
      // For now, use simulation as fallback
      simulatePaymentMutation.mutate()
    }
  }

  const handleCancel = () => {
    cancelMutation.mutate()
  }

  const handleBookAnother = () => {
    setSelectedSlot(null)
    setCurrentBooking(null)
    setPaymentInfo(null)
    setBookingState('select_slot')
    setError(null)
    refetchSlots()
  }

  const handleViewBookings = () => {
    navigate('/my-bookings')
  }

  // Render different states
  if (bookingState === 'paid') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary-500 to-primary-600 flex flex-col items-center justify-center px-4 text-white">
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

        <p className="text-white/80 text-center mb-8 animate-fade-in">
          Your appointment has been successfully booked.
        </p>

        {currentBooking?.slot && (
          <div className="w-full max-w-sm bg-white/10 rounded-2xl p-4 mb-8 animate-slide-up">
            <div className="text-center">
              <p className="text-white/60 text-sm">Appointment Date</p>
              <p className="font-semibold text-lg">
                {format(parseISO(currentBooking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
              </p>
              <p className="text-xl font-bold">
                {format(parseISO(currentBooking.slot.start_at), 'HH:mm')}
              </p>
            </div>

            <div className="mt-4 pt-4 border-t border-white/10 text-center">
              <p className="text-white/60 text-sm">Amount</p>
              <p className="font-bold text-xl">
                {currentBooking.price_rub.toLocaleString('ru-RU')} ₽
              </p>
            </div>
          </div>
        )}

        <div className="w-full max-w-sm space-y-3 animate-slide-up">
          <button
            onClick={handleViewBookings}
            className="w-full py-3 px-6 bg-white text-primary-600 font-semibold rounded-xl"
          >
            View My Bookings
          </button>
          <button
            onClick={() => navigate('/results')}
            className="w-full py-3 px-6 bg-white/10 text-white font-medium rounded-xl"
          >
            Browse More Nutritionists
          </button>
        </div>
      </div>
    )
  }

  if (bookingState === 'expired') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
        <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mb-6">
          <svg className="w-10 h-10 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <h1 className="text-xl font-display font-bold text-gray-900 mb-2">
          Hold Expired
        </h1>

        <p className="text-gray-500 text-center mb-8 max-w-xs">
          Your slot hold has expired. The slot may have been booked by someone else.
        </p>

        <button
          onClick={handleBookAnother}
          className="btn-primary px-8"
        >
          Choose Another Slot
        </button>
      </div>
    )
  }

  if (bookingState === 'cancelled') {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
          <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>

        <h1 className="text-xl font-display font-bold text-gray-900 mb-2">
          Booking Cancelled
        </h1>

        <p className="text-gray-500 text-center mb-8">
          Your booking has been cancelled.
        </p>

        <button
          onClick={handleBookAnother}
          className="btn-primary px-8"
        >
          Book Another Slot
        </button>
      </div>
    )
  }

  if (bookingState === 'pending_payment' && currentBooking) {
    return (
      <div className="min-h-screen bg-white">
        {/* Header */}
        <div className="px-4 pt-6 pb-4 border-b border-gray-100">
          <h1 className="text-xl font-display font-bold text-gray-900">
            Complete Payment
          </h1>
          <p className="text-gray-500 mt-1">
            Hold expires in {countdown.formatted}
          </p>
        </div>

        {/* Countdown warning */}
        <div className={`px-4 py-3 ${countdown.totalSeconds <= 60 ? 'bg-red-50' : 'bg-amber-50'}`}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              countdown.totalSeconds <= 60 ? 'bg-red-100' : 'bg-amber-100'
            }`}>
              <svg 
                className={`w-5 h-5 ${countdown.totalSeconds <= 60 ? 'text-red-600' : 'text-amber-600'}`} 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className={`font-semibold ${countdown.totalSeconds <= 60 ? 'text-red-700' : 'text-amber-700'}`}>
                Time remaining: {countdown.formatted}
              </p>
              <p className={`text-sm ${countdown.totalSeconds <= 60 ? 'text-red-600' : 'text-amber-600'}`}>
                Complete payment before the hold expires
              </p>
            </div>
          </div>
        </div>

        {/* Booking summary */}
        <div className="px-4 py-6 border-b border-gray-100">
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4">Booking Details</h2>
            
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Service</span>
                <span className="font-medium">{currentBooking.service?.title}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Nutritionist</span>
                <span className="font-medium">{nutritionist.profile?.full_name}</span>
              </div>
              {currentBooking.slot && (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Date</span>
                    <span className="font-medium">
                      {format(parseISO(currentBooking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Time</span>
                    <span className="font-medium">
                      {format(parseISO(currentBooking.slot.start_at), 'HH:mm')}
                    </span>
                  </div>
                </>
              )}
              <div className="flex justify-between pt-3 border-t border-gray-100">
                <span className="text-gray-900 font-medium">Total</span>
                <span className="font-bold text-primary-600">
                  {currentBooking.price_rub.toLocaleString('ru-RU')} ₽
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Status badge */}
        <div className="px-4 py-4">
          <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 rounded-lg">
            <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            <span className="text-sm font-medium text-amber-700">
              Awaiting Payment
            </span>
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="px-4">
            <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 p-4 safe-area-bottom space-y-3">
          {/* Payment button - adapts to provider */}
          {paymentInfo?.provider === 'mock' ? (
            <button
              onClick={handlePayment}
              disabled={simulatePaymentMutation.isPending || countdown.isExpired}
              className="btn-primary w-full"
            >
              {simulatePaymentMutation.isPending ? 'Processing...' : 'Simulate Payment Success'}
            </button>
          ) : (
            <button
              onClick={handlePayment}
              disabled={simulatePaymentMutation.isPending || countdown.isExpired}
              className="btn-primary w-full"
            >
              {simulatePaymentMutation.isPending ? 'Processing...' : `Pay ${currentBooking.price_rub.toLocaleString('ru-RU')} ₽`}
            </button>
          )}
          
          {/* Provider indicator (dev mode) */}
          {import.meta.env.DEV && paymentInfo?.provider && (
            <p className="text-xs text-center text-gray-400">
              Provider: {paymentInfo.provider}
            </p>
          )}
          
          <button
            onClick={handleCancel}
            disabled={cancelMutation.isPending}
            className="w-full py-3 text-gray-500 font-medium"
          >
            {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Booking'}
          </button>
        </div>
      </div>
    )
  }

  // Default: slot selection state
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 border-b border-gray-100">
        <h1 className="text-xl font-display font-bold text-gray-900">
          Book Appointment
        </h1>
        <p className="text-gray-500 mt-1">
          Select a convenient time slot
        </p>
      </div>

      {/* Service summary */}
      <div className="px-4 py-4 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center gap-3">
          {nutritionist.profile?.photo_url ? (
            <img
              src={nutritionist.profile.photo_url}
              alt={nutritionist.profile.full_name}
              className="w-12 h-12 rounded-xl object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-primary-500 flex items-center justify-center">
              <span className="text-white font-bold">
                {nutritionist.profile?.full_name?.charAt(0) || 'N'}
              </span>
            </div>
          )}
          <div className="flex-1">
            <p className="font-medium text-gray-900">{service.title}</p>
            <p className="text-sm text-gray-500">
              {nutritionist.profile?.full_name} • {service.duration_minutes} min
            </p>
          </div>
          <div className="text-right">
            <p className="font-bold text-primary-600">
              {service.price_rub.toLocaleString('ru-RU')} ₽
            </p>
          </div>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="px-4 py-4">
          <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Slot picker */}
      <div className="px-4 py-6 pb-32">
        <SlotPicker
          slots={slots}
          selectedSlot={selectedSlot}
          onSelectSlot={setSelectedSlot}
        />
      </div>

      {/* Bottom section */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 safe-area-bottom">
        {selectedSlot && (
          <div className="px-4 py-3 bg-primary-50 border-b border-primary-100">
            <p className="text-sm text-primary-800">
              <span className="font-medium">Selected:</span>{' '}
              {format(parseISO(selectedSlot.start_at), 'EEEE, d MMMM', { locale: ru })} at{' '}
              {format(parseISO(selectedSlot.start_at), 'HH:mm')}
            </p>
          </div>
        )}
        <div className="p-4">
          <button
            onClick={handleBook}
            disabled={!selectedSlot || bookingMutation.isPending}
            className="btn-primary w-full"
          >
            {bookingMutation.isPending
              ? 'Booking...'
              : selectedSlot
              ? `Confirm Booking • ${service.price_rub.toLocaleString('ru-RU')} ₽`
              : 'Select a time slot'}
          </button>
        </div>
      </div>
    </div>
  )
}
