import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { clientApi, bookingApi } from '../lib/api'
import { useCountdown } from '../hooks/useCountdown'
import type { Booking } from '../types'
import {
  PageContainer,
  Section,
  Stack,
  Inline,
  Card,
  Button,
  Heading,
  Text,
  StatusBadge,
  NoBookingsState,
  Icons,
} from '../design-system'
import { PageLoader } from '../design-system/components/Loader'

// Countdown display for pending bookings
function HoldCountdown({ expiresAt }: { expiresAt: string }) {
  const countdown = useCountdown(expiresAt)

  if (countdown.isExpired) {
    return (
      <Text size="xs" weight="medium" color="error">
        Expired
      </Text>
    )
  }

  return (
    <Text
      size="xs"
      weight="medium"
      className={countdown.totalSeconds <= 60 ? 'text-error-600' : 'text-warning-600'}
    >
      {countdown.formatted} left
    </Text>
  )
}

// Single booking card
function BookingCard({ booking }: { booking: Booking }) {
  const queryClient = useQueryClient()

  // Mutations for actions
  const markPaidMutation = useMutation({
    mutationFn: () => bookingApi.markPaid(booking.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-bookings'] })
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
    },
  })

  const cancelMutation = useMutation({
    mutationFn: () => bookingApi.cancelBooking(booking.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-bookings'] })
    },
  })

  const isPending = booking.status === 'pending_payment'
  const isPaid = booking.status === 'paid'
  const holdExpiresAt = booking.slot?.hold_expires_at

  // Get nutritionist name
  const nutritionistName = booking.nutritionist?.profile?.full_name || 'Nutritionist'

  // Map status to StatusBadge status
  const getStatusBadgeStatus = (status: Booking['status']) => {
    const statusMap: Record<Booking['status'], 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'refunded' | 'no_show'> = {
      pending_payment: 'pending',
      paid: 'confirmed',
      cancelled: 'cancelled',
      completed: 'completed',
      refunded: 'refunded',
      no_show: 'no_show',
    }
    return statusMap[status] || 'pending'
  }

  return (
    <Card variant="default" padding="md" className="animate-slide-up">
      {/* Header with status */}
      <Inline justify="between" align="center" className="mb-3">
        <StatusBadge status={getStatusBadgeStatus(booking.status)} />
        {isPending && holdExpiresAt && (
          <HoldCountdown expiresAt={holdExpiresAt} />
        )}
      </Inline>

      {/* Service and nutritionist info */}
      <div className="mb-3">
        <Text weight="semibold">
          {booking.service?.title || 'Consultation'}
        </Text>
        <Text size="sm" color="secondary">
          with {nutritionistName}
        </Text>
      </div>

      {/* Slot time */}
      {booking.slot && (
        <Inline gap={2} className="mb-3 text-text-secondary">
          <Icons.Calendar size="sm" className="text-text-tertiary" />
          <Text size="sm" color="secondary">
            {format(parseISO(booking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
          </Text>
          <span className="text-text-tertiary">•</span>
          <Text size="sm" weight="medium">
            {format(parseISO(booking.slot.start_at), 'HH:mm')}
          </Text>
        </Inline>
      )}

      {/* Price */}
      <Inline justify="between" className="pt-3 border-t border-border-light">
        <Text size="sm" color="secondary">Total</Text>
        <Text weight="bold">
          {booking.price_rub.toLocaleString('ru-RU')} ₽
        </Text>
      </Inline>

      {/* Actions for pending bookings */}
      {isPending && (
        <Inline gap={3} className="mt-4 pt-4 border-t border-border-light">
          <Button
            onClick={() => markPaidMutation.mutate()}
            loading={markPaidMutation.isPending}
            size="sm"
            className="flex-1"
          >
            Pay Now
          </Button>
          <Button
            variant="ghost"
            onClick={() => cancelMutation.mutate()}
            loading={cancelMutation.isPending}
            size="sm"
            className="text-text-secondary"
          >
            Cancel
          </Button>
        </Inline>
      )}

      {/* Meeting link for paid bookings */}
      {isPaid && booking.meeting_link && (
        <div className="mt-4 pt-4 border-t border-border-light">
          <a
            href={booking.meeting_link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-primary-600 font-medium text-sm hover:text-primary-700"
          >
            <Icons.Video size="sm" />
            Join Meeting
          </a>
        </div>
      )}
    </Card>
  )
}

// Bottom navigation
function BottomNav() {
  const navigate = useNavigate()
  
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-surface-primary border-t border-border-light safe-area-bottom z-fixed">
      <div className="flex">
        <button
          onClick={() => navigate('/results')}
          className="flex-1 py-4 flex flex-col items-center gap-1 text-text-tertiary transition-colors"
        >
          <Icons.Search size="lg" />
          <span className="text-xs">Browse</span>
        </button>
        <button
          className="flex-1 py-4 flex flex-col items-center gap-1 text-primary-600 transition-colors"
        >
          <Icons.Calendar size="lg" />
          <span className="text-xs font-medium">My Bookings</span>
        </button>
      </div>
    </div>
  )
}

export default function MyBookingsPage() {
  const navigate = useNavigate()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['my-bookings'],
    queryFn: () => clientApi.getMyBookings(),
    refetchInterval: 30000, // Refetch every 30 seconds to update countdowns
  })

  if (isLoading) {
    return <PageLoader text="Loading your bookings..." />
  }

  if (error) {
    return (
      <PageContainer>
        <div className="min-h-screen flex items-center justify-center px-4">
          <div className="text-center">
            <Text color="error" weight="medium">Failed to load bookings.</Text>
            <Button onClick={() => refetch()} className="mt-4">
              Try Again
            </Button>
          </div>
        </div>
      </PageContainer>
    )
  }

  const bookings = data?.bookings || []

  // Separate bookings by status
  const pendingBookings = bookings.filter(b => b.status === 'pending_payment')
  const upcomingBookings = bookings.filter(b => b.status === 'paid')
  const pastBookings = bookings.filter(b => 
    ['completed', 'cancelled', 'refunded', 'no_show'].includes(b.status)
  )

  return (
    <PageContainer background="gradient" withBottomNav>
      {/* Header */}
      <Section spacing="md">
        <Heading level="h1" size="xl">My Bookings</Heading>
        <Text color="secondary" className="mt-1">
          {bookings.length} booking{bookings.length !== 1 ? 's' : ''}
        </Text>
      </Section>

      <Section spacing="none" className="pb-8">
        {bookings.length === 0 ? (
          <NoBookingsState onAction={() => navigate('/results')} />
        ) : (
          <Stack gap={6}>
            {/* Pending payment section */}
            {pendingBookings.length > 0 && (
              <section>
                <Inline gap={2} align="center" className="mb-3">
                  <div className="w-2 h-2 rounded-full bg-warning-500 animate-pulse" />
                  <Text size="sm" weight="semibold" className="text-warning-600 uppercase tracking-wide">
                    Awaiting Payment ({pendingBookings.length})
                  </Text>
                </Inline>
                <Stack gap={3}>
                  {pendingBookings.map((booking, index) => (
                    <div key={booking.id} style={{ animationDelay: `${index * 50}ms` }}>
                      <BookingCard booking={booking} />
                    </div>
                  ))}
                </Stack>
              </section>
            )}

            {/* Upcoming bookings section */}
            {upcomingBookings.length > 0 && (
              <section>
                <Text size="sm" weight="semibold" className="text-success-600 uppercase tracking-wide mb-3">
                  Upcoming ({upcomingBookings.length})
                </Text>
                <Stack gap={3}>
                  {upcomingBookings.map((booking, index) => (
                    <div key={booking.id} style={{ animationDelay: `${index * 50}ms` }}>
                      <BookingCard booking={booking} />
                    </div>
                  ))}
                </Stack>
              </section>
            )}

            {/* Past bookings section */}
            {pastBookings.length > 0 && (
              <section>
                <Text size="sm" weight="semibold" color="tertiary" className="uppercase tracking-wide mb-3">
                  Past ({pastBookings.length})
                </Text>
                <Stack gap={3}>
                  {pastBookings.map((booking, index) => (
                    <div key={booking.id} style={{ animationDelay: `${index * 50}ms` }}>
                      <BookingCard booking={booking} />
                    </div>
                  ))}
                </Stack>
              </section>
            )}
          </Stack>
        )}
      </Section>

      {/* Bottom navigation */}
      <BottomNav />
    </PageContainer>
  )
}
