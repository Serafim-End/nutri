import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { clientApi, bookingApi } from '../lib/api'
import { useCountdown } from '../hooks/useCountdown'
import LoadingScreen from '../components/LoadingScreen'
import type { Booking } from '../types'

// Status badge component
function StatusBadge({ status }: { status: Booking['status'] }) {
  const config: Record<Booking['status'], { label: string; className: string }> = {
    pending_payment: {
      label: 'Awaiting Payment',
      className: 'bg-amber-100 text-amber-800',
    },
    paid: {
      label: 'Confirmed',
      className: 'bg-green-100 text-green-800',
    },
    cancelled: {
      label: 'Cancelled',
      className: 'bg-gray-100 text-gray-600',
    },
    completed: {
      label: 'Completed',
      className: 'bg-blue-100 text-blue-800',
    },
    refunded: {
      label: 'Refunded',
      className: 'bg-purple-100 text-purple-800',
    },
    no_show: {
      label: 'No Show',
      className: 'bg-red-100 text-red-800',
    },
  }

  const { label, className } = config[status] || { label: status, className: 'bg-gray-100 text-gray-600' }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {label}
    </span>
  )
}

// Countdown display for pending bookings
function HoldCountdown({ expiresAt }: { expiresAt: string }) {
  const countdown = useCountdown(expiresAt)

  if (countdown.isExpired) {
    return (
      <span className="text-red-600 text-xs font-medium">
        Expired
      </span>
    )
  }

  return (
    <span className={`text-xs font-medium ${
      countdown.totalSeconds <= 60 ? 'text-red-600' : 'text-amber-600'
    }`}>
      {countdown.formatted} left
    </span>
  )
}

// Single booking card
function BookingCard({ booking }: { booking: Booking }) {
  const navigate = useNavigate()
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

  return (
    <div className="card animate-slide-up">
      {/* Header with status */}
      <div className="flex items-center justify-between mb-3">
        <StatusBadge status={booking.status} />
        {isPending && holdExpiresAt && (
          <HoldCountdown expiresAt={holdExpiresAt} />
        )}
      </div>

      {/* Service and nutritionist info */}
      <div className="mb-3">
        <h3 className="font-semibold text-gray-900">
          {booking.service?.title || 'Consultation'}
        </h3>
        <p className="text-sm text-gray-500">
          with {nutritionistName}
        </p>
      </div>

      {/* Slot time */}
      {booking.slot && (
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>
            {format(parseISO(booking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
          </span>
          <span className="text-gray-400">•</span>
          <span className="font-medium">
            {format(parseISO(booking.slot.start_at), 'HH:mm')}
          </span>
        </div>
      )}

      {/* Price */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <span className="text-sm text-gray-500">Total</span>
        <span className="font-bold text-gray-900">
          {booking.price_rub.toLocaleString('ru-RU')} ₽
        </span>
      </div>

      {/* Actions for pending bookings */}
      {isPending && (
        <div className="mt-4 pt-4 border-t border-gray-100 flex gap-3">
          <button
            onClick={() => markPaidMutation.mutate()}
            disabled={markPaidMutation.isPending}
            className="flex-1 py-2 px-4 bg-primary-500 text-white font-medium rounded-lg text-sm hover:bg-primary-600 disabled:opacity-50"
          >
            {markPaidMutation.isPending ? 'Processing...' : 'Pay Now'}
          </button>
          <button
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
            className="py-2 px-4 text-gray-500 font-medium text-sm hover:text-gray-700"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Meeting link for paid bookings */}
      {isPaid && booking.meeting_link && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <a
            href={booking.meeting_link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-primary-600 font-medium text-sm hover:text-primary-700"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            Join Meeting
          </a>
        </div>
      )}
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
    return <LoadingScreen />
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-500">Failed to load bookings.</p>
          <button
            onClick={() => refetch()}
            className="mt-4 btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
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
    <div className="min-h-screen bg-gradient-to-b from-primary-50/50 to-white">
      {/* Header */}
      <div className="px-4 pt-6 pb-4">
        <h1 className="text-2xl font-display font-bold text-gray-900">
          My Bookings
        </h1>
        <p className="text-gray-500 mt-1">
          {bookings.length} booking{bookings.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="px-4 pb-8 space-y-6">
        {bookings.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <p className="text-gray-500 mb-4">
              No bookings yet
            </p>
            <button
              onClick={() => navigate('/results')}
              className="btn-primary"
            >
              Find a Nutritionist
            </button>
          </div>
        ) : (
          <>
            {/* Pending payment section */}
            {pendingBookings.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-amber-600 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  Awaiting Payment ({pendingBookings.length})
                </h2>
                <div className="space-y-3">
                  {pendingBookings.map((booking, index) => (
                    <div key={booking.id} style={{ animationDelay: `${index * 50}ms` }}>
                      <BookingCard booking={booking} />
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Upcoming bookings section */}
            {upcomingBookings.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-green-600 uppercase tracking-wide mb-3">
                  Upcoming ({upcomingBookings.length})
                </h2>
                <div className="space-y-3">
                  {upcomingBookings.map((booking, index) => (
                    <div key={booking.id} style={{ animationDelay: `${index * 50}ms` }}>
                      <BookingCard booking={booking} />
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Past bookings section */}
            {pastBookings.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                  Past ({pastBookings.length})
                </h2>
                <div className="space-y-3">
                  {pastBookings.map((booking, index) => (
                    <div key={booking.id} style={{ animationDelay: `${index * 50}ms` }}>
                      <BookingCard booking={booking} />
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>

      {/* Bottom navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 safe-area-bottom">
        <div className="flex">
          <button
            onClick={() => navigate('/results')}
            className="flex-1 py-4 flex flex-col items-center gap-1 text-gray-500"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="text-xs">Browse</span>
          </button>
          <button
            className="flex-1 py-4 flex flex-col items-center gap-1 text-primary-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-xs font-medium">My Bookings</span>
          </button>
        </div>
      </div>
    </div>
  )
}

