import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { publicApi, bookingApi, paymentApi } from '../lib/api'
import { useCountdown } from '../hooks/useCountdown'
import SlotPicker from '../components/SlotPicker'
import type { AvailabilitySlot, Booking, PaymentIntent } from '../types'
import {
  PageContainer,
  Section,
  Header,
  Footer,
  Stack,
  Inline,
  Card,
  Badge,
  Button,
  Alert,
  Heading,
  Text,
  Center,
  NotFoundState,
  Icons,
} from '../design-system'
import { PageLoader } from '../design-system/components/Loader'
import clsx from 'clsx'

type BookingState = 'select_slot' | 'pending_payment' | 'paid' | 'cancelled' | 'expired'

// Countdown timer display
function CountdownTimer({ expiresAt, onExpire }: { expiresAt: string; onExpire: () => void }) {
  const countdown = useCountdown(expiresAt)

  if (countdown.isExpired) {
    onExpire()
    return null
  }

  const isUrgent = countdown.totalSeconds <= 60

  return (
    <div className={clsx(
      'px-4 py-3 transition-colors',
      isUrgent ? 'bg-error-50' : 'bg-warning-50'
    )}>
      <Inline gap={3} align="center">
        <div className={clsx(
          'w-10 h-10 rounded-full flex items-center justify-center',
          isUrgent ? 'bg-error-100' : 'bg-warning-100'
        )}>
          <Icons.Clock size="md" className={isUrgent ? 'text-error-600' : 'text-warning-600'} />
        </div>
        <div>
          <Text weight="semibold" className={isUrgent ? 'text-error-700' : 'text-warning-700'}>
            Time remaining: {countdown.formatted}
          </Text>
          <Text size="sm" className={isUrgent ? 'text-error-600' : 'text-warning-600'}>
            Complete payment before the hold expires
          </Text>
        </div>
      </Inline>
    </div>
  )
}

// Success state
function BookingSuccess({ 
  booking, 
  onViewBookings, 
  onBrowseMore 
}: { 
  booking: Booking
  onViewBookings: () => void
  onBrowseMore: () => void
}) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-500 to-primary-600 flex flex-col items-center justify-center px-4 text-white">
      <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mb-8 animate-scale-in shadow-xl">
        <Icons.CheckCircle size="xl" className="w-14 h-14 text-primary-500" />
      </div>

      <Heading level="h1" size="2xl" className="text-white text-center animate-fade-in">
        Booking Confirmed!
      </Heading>

      <Text className="text-white/80 text-center mt-2 animate-fade-in">
        Your appointment has been successfully booked.
      </Text>

      {booking.slot && (
        <Card variant="elevated" className="w-full max-w-sm mt-8 bg-white/10 border-none animate-slide-up">
          <div className="text-center text-white">
            <Text size="sm" className="text-white/60">Appointment Date</Text>
            <Text weight="semibold" size="lg" className="text-white">
              {format(parseISO(booking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
            </Text>
            <Text size="xl" weight="bold" className="text-white">
              {format(parseISO(booking.slot.start_at), 'HH:mm')}
            </Text>
          </div>

          <div className="mt-4 pt-4 border-t border-white/10 text-center">
            <Text size="sm" className="text-white/60">Amount</Text>
            <Text size="xl" weight="bold" className="text-white">
              {booking.price_rub.toLocaleString('ru-RU')} ₽
            </Text>
          </div>
        </Card>
      )}

      <Stack gap={3} className="w-full max-w-sm mt-8 animate-slide-up">
        <Button
          onClick={onViewBookings}
          variant="secondary"
          fullWidth
          className="bg-white text-primary-600 hover:bg-white/90"
        >
          View My Bookings
        </Button>
        <Button
          onClick={onBrowseMore}
          variant="ghost"
          fullWidth
          className="text-white bg-white/10 hover:bg-white/20"
        >
          Browse More Nutritionists
        </Button>
      </Stack>
    </div>
  )
}

// Expired state
function BookingExpired({ onRetry }: { onRetry: () => void }) {
  return (
    <Center fullHeight className="bg-bg-secondary px-4">
      <div className="text-center">
        <div className="w-20 h-20 bg-warning-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Icons.Clock size="xl" className="text-warning-600" />
        </div>
        <Heading size="lg">Hold Expired</Heading>
        <Text color="secondary" className="mt-2 max-w-xs mx-auto">
          Your slot hold has expired. The slot may have been booked by someone else.
        </Text>
        <Button onClick={onRetry} className="mt-6">
          Choose Another Slot
        </Button>
      </div>
    </Center>
  )
}

// Cancelled state
function BookingCancelled({ onRetry }: { onRetry: () => void }) {
  return (
    <Center fullHeight className="bg-bg-secondary px-4">
      <div className="text-center">
        <div className="w-20 h-20 bg-neutral-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Icons.Close size="xl" className="text-neutral-400" />
        </div>
        <Heading size="lg">Booking Cancelled</Heading>
        <Text color="secondary" className="mt-2">
          Your booking has been cancelled.
        </Text>
        <Button onClick={onRetry} className="mt-6">
          Book Another Slot
        </Button>
      </div>
    </Center>
  )
}

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

  const holdExpiresAt = currentBooking?.slot?.hold_expires_at

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

  // Payment mutation
  const simulatePaymentMutation = useMutation({
    mutationFn: async (): Promise<{ booking: Booking }> => {
      if (paymentInfo?.provider === 'mock') {
        const result = await paymentApi.simulatePayment(currentBooking!.id)
        if (!result.booking) {
          throw new Error('Payment succeeded but booking data was not returned')
        }
        return { booking: result.booking }
      }
      const result = await bookingApi.markPaid(currentBooking!.id)
      return { booking: result.booking }
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
    return <PageLoader text="Loading booking options..." />
  }

  const nutritionist = nutritionistData?.nutritionist
  const service = servicesData?.services?.find((s) => s.id === serviceId)
  const slots = slotsData?.slots || []

  if (!nutritionist || !service) {
    return (
      <PageContainer>
        <Center fullHeight>
          <NotFoundState onBack={() => navigate(-1)} />
        </Center>
      </PageContainer>
    )
  }

  const handleBook = () => {
    if (selectedSlot) {
      setError(null)
      bookingMutation.mutate()
    }
  }

  const handlePayment = () => {
    simulatePaymentMutation.mutate()
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

  // Render different states
  if (bookingState === 'paid' && currentBooking) {
    return (
      <BookingSuccess
        booking={currentBooking}
        onViewBookings={() => navigate('/my-bookings')}
        onBrowseMore={() => navigate('/results')}
      />
    )
  }

  if (bookingState === 'expired') {
    return <BookingExpired onRetry={handleBookAnother} />
  }

  if (bookingState === 'cancelled') {
    return <BookingCancelled onRetry={handleBookAnother} />
  }

  if (bookingState === 'pending_payment' && currentBooking) {
    return (
      <PageContainer background="primary">
        <Header sticky bordered>
          <Heading level="h1" size="lg">Complete Payment</Heading>
          <Text size="sm" color="secondary" className="mt-0.5">
            Secure your appointment
          </Text>
        </Header>

        {/* Countdown warning */}
        {holdExpiresAt && (
          <CountdownTimer
            expiresAt={holdExpiresAt}
            onExpire={() => setBookingState('expired')}
          />
        )}

        {/* Booking summary */}
        <Section>
          <Card padding="lg">
            <Heading level="h2" size="md" className="mb-4">Booking Details</Heading>
            
            <Stack gap={3}>
              <Inline justify="between">
                <Text color="secondary">Service</Text>
                <Text weight="medium">{currentBooking.service?.title}</Text>
              </Inline>
              <Inline justify="between">
                <Text color="secondary">Nutritionist</Text>
                <Text weight="medium">{nutritionist.profile?.full_name}</Text>
              </Inline>
              {currentBooking.slot && (
                <>
                  <Inline justify="between">
                    <Text color="secondary">Date</Text>
                    <Text weight="medium">
                      {format(parseISO(currentBooking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
                    </Text>
                  </Inline>
                  <Inline justify="between">
                    <Text color="secondary">Time</Text>
                    <Text weight="medium">
                      {format(parseISO(currentBooking.slot.start_at), 'HH:mm')}
                    </Text>
                  </Inline>
                </>
              )}
              <div className="pt-3 border-t border-border-light">
                <Inline justify="between">
                  <Text weight="medium">Total</Text>
                  <Text weight="bold" className="text-primary-600 text-lg">
                    {currentBooking.price_rub.toLocaleString('ru-RU')} ₽
                  </Text>
                </Inline>
              </div>
            </Stack>
          </Card>
        </Section>

        {/* Status badge */}
        <Section spacing="sm">
          <Badge variant="warning" dot animated size="md">
            Awaiting Payment
          </Badge>
        </Section>

        {/* Error display */}
        {error && (
          <Section spacing="sm">
            <Alert variant="error">{error}</Alert>
          </Section>
        )}

        {/* Actions */}
        <Footer bordered>
          <Stack gap={3}>
            <Button
              onClick={handlePayment}
              loading={simulatePaymentMutation.isPending}
              fullWidth
              size="lg"
            >
              {paymentInfo?.provider === 'mock'
                ? 'Simulate Payment Success'
                : `Pay ${currentBooking.price_rub.toLocaleString('ru-RU')} ₽`}
            </Button>
            <Button
              variant="ghost"
              onClick={handleCancel}
              loading={cancelMutation.isPending}
              fullWidth
              className="text-text-secondary"
            >
              Cancel Booking
            </Button>
          </Stack>
        </Footer>
      </PageContainer>
    )
  }

  // Default: slot selection state
  return (
    <PageContainer background="primary">
      <Header sticky bordered>
        <Heading level="h1" size="lg">Book Appointment</Heading>
        <Text size="sm" color="secondary" className="mt-0.5">
          Select a convenient time slot
        </Text>
      </Header>

      {/* Service summary */}
      <div className="px-4 py-4 bg-bg-secondary border-b border-border-light">
        <Inline gap={3} align="center">
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
            <Text weight="medium">{service.title}</Text>
            <Text size="sm" color="secondary">
              {nutritionist.profile?.full_name} • {service.duration_minutes} min
            </Text>
          </div>
          <Text weight="bold" className="text-primary-600">
            {service.price_rub.toLocaleString('ru-RU')} ₽
          </Text>
        </Inline>
      </div>

      {/* Error display */}
      {error && (
        <Section spacing="sm">
          <Alert variant="error">{error}</Alert>
        </Section>
      )}

      {/* Slot picker */}
      <Section className="pb-40">
        <SlotPicker
          slots={slots}
          selectedSlot={selectedSlot}
          onSelectSlot={setSelectedSlot}
        />
      </Section>

      {/* Bottom section */}
      <Footer bordered>
        {selectedSlot && (
          <div className="mb-3 px-3 py-2 bg-primary-50 rounded-lg border border-primary-100">
            <Text size="sm" className="text-primary-800">
              <span className="font-medium">Selected:</span>{' '}
              {format(parseISO(selectedSlot.start_at), 'EEEE, d MMMM', { locale: ru })} at{' '}
              {format(parseISO(selectedSlot.start_at), 'HH:mm')}
            </Text>
          </div>
        )}
        <Button
          onClick={handleBook}
          disabled={!selectedSlot}
          loading={bookingMutation.isPending}
          fullWidth
          size="lg"
        >
          {selectedSlot
            ? `Confirm Booking • ${service.price_rub.toLocaleString('ru-RU')} ₽`
            : 'Select a time slot'}
        </Button>
      </Footer>
    </PageContainer>
  )
}
