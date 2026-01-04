import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { Booking, BookingsListResponse } from '@/types'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'

type StatusFilter = 'all' | 'pending_payment' | 'paid' | 'completed' | 'cancelled' | 'refunded'

const statusColors: Record<string, string> = {
  pending_payment: 'bg-warning-500/10 text-warning-400 border-warning-500/20',
  paid: 'bg-accent-500/10 text-accent-400 border-accent-500/20',
  completed: 'bg-success-500/10 text-success-400 border-success-500/20',
  cancelled: 'bg-error-500/10 text-error-400 border-error-500/20',
  no_show: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  refunded: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
}

const statusLabels: Record<string, string> = {
  pending_payment: 'Pending Payment',
  paid: 'Paid',
  completed: 'Completed',
  cancelled: 'Cancelled',
  no_show: 'No Show',
  refunded: 'Refunded',
}

export function BookingsPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery<BookingsListResponse>({
    queryKey: ['admin', 'bookings', statusFilter, dateFrom, dateTo, page],
    queryFn: () =>
      adminApi.getBookings({
        page,
        limit: 20,
        status: statusFilter === 'all' ? undefined : statusFilter,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
  })

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      adminApi.cancelBooking(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'bookings'] })
      setSelectedBooking(null)
    },
  })

  const completeMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      adminApi.completeBooking(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'bookings'] })
      setSelectedBooking(null)
    },
  })

  const bookings: Booking[] = data?.bookings || []
  const totalPages = data?.pages || 1

  const filterButtons: { value: StatusFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'pending_payment', label: 'Pending' },
    { value: 'paid', label: 'Paid' },
    { value: 'completed', label: 'Completed' },
    { value: 'cancelled', label: 'Cancelled' },
  ]

  const formatDateTime = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—'
    try {
      return format(parseISO(dateStr), 'MMM d, yyyy HH:mm')
    } catch {
      return '—'
    }
  }

  const formatCurrency = (amount: number, currency: string = 'RUB') => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-bold text-white mb-2">Bookings</h1>
          <p className="text-slate-400">View and manage all platform bookings</p>
        </div>
        {data && (
          <div className="text-sm text-slate-500">
            {data.total} total booking{data.total !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Status filter */}
        <div className="flex gap-2 p-1 bg-slate-925/50 border border-slate-800/50 rounded-xl">
          {filterButtons.map((btn) => (
            <button
              key={btn.value}
              onClick={() => {
                setStatusFilter(btn.value)
                setPage(1)
              }}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                statusFilter === btn.value
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {/* Date range filter */}
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 bg-slate-925/50 border border-slate-800/50 rounded-lg text-sm text-white focus:border-accent-500 focus:outline-none"
            placeholder="From"
          />
          <span className="text-slate-500">—</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 bg-slate-925/50 border border-slate-800/50 rounded-lg text-sm text-white focus:border-accent-500 focus:outline-none"
            placeholder="To"
          />
          {(dateFrom || dateTo) && (
            <button
              onClick={() => {
                setDateFrom('')
                setDateTo('')
                setPage(1)
              }}
              className="px-3 py-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center p-12">
            <div className="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center p-12 text-error-400">
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Failed to load bookings
          </div>
        ) : bookings.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <svg
              className="w-12 h-12 mb-4 text-slate-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="font-medium text-slate-400 mb-1">No bookings found</p>
            <p className="text-sm">
              {statusFilter !== 'all'
                ? `No ${statusLabels[statusFilter]?.toLowerCase()} bookings.`
                : 'No bookings have been made yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800/50">
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    ID
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Nutritionist
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Client
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Date/Time
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Status
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Amount
                  </th>
                  <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {bookings.map((booking) => (
                  <tr key={booking.id} className="hover:bg-slate-900/30 transition-colors">
                    <td className="px-6 py-4">
                      <span className="font-mono text-xs text-slate-400">
                        {booking.id.slice(0, 8)}...
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                          <span className="text-xs font-semibold text-slate-300">
                            {booking.nutritionist?.full_name?.charAt(0).toUpperCase() || '?'}
                          </span>
                        </div>
                        <span className="text-sm text-white">
                          {booking.nutritionist?.full_name || 'Unknown'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {booking.client?.photo_url ? (
                          <img
                            src={booking.client.photo_url}
                            alt=""
                            className="w-8 h-8 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                            <span className="text-xs font-semibold text-slate-300">
                              {booking.client?.full_name?.charAt(0).toUpperCase() || '?'}
                            </span>
                          </div>
                        )}
                        <span className="text-sm text-white">
                          {booking.client?.full_name || 'Unknown'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300">
                      {booking.slot ? formatDateTime(booking.slot.start_at) : formatDateTime(booking.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={clsx(
                          'px-2.5 py-1 text-xs font-medium rounded-lg border',
                          statusColors[booking.status] || statusColors.pending_payment
                        )}
                      >
                        {statusLabels[booking.status] || booking.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-300 font-medium">
                      {formatCurrency(booking.price_rub, booking.currency)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedBooking(booking)}
                        className="px-3 py-1.5 text-sm font-medium text-accent-400 hover:bg-accent-500/10 rounded-lg transition-colors"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              page === 1
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            )}
          >
            Previous
          </button>
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = i + 1
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={clsx(
                    'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                    page === pageNum
                      ? 'bg-accent-500 text-white'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  )}
                >
                  {pageNum}
                </button>
              )
            })}
            {totalPages > 5 && (
              <>
                <span className="text-slate-600 px-2">...</span>
                <button
                  onClick={() => setPage(totalPages)}
                  className={clsx(
                    'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                    page === totalPages
                      ? 'bg-accent-500 text-white'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  )}
                >
                  {totalPages}
                </button>
              </>
            )}
          </div>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className={clsx(
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              page === totalPages
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            )}
          >
            Next
          </button>
        </div>
      )}

      {/* Detail Modal */}
      {selectedBooking && (
        <BookingDetailModal
          booking={selectedBooking}
          onClose={() => setSelectedBooking(null)}
          onCancel={(reason) => cancelMutation.mutate({ id: selectedBooking.id, reason })}
          onComplete={(notes) => completeMutation.mutate({ id: selectedBooking.id, notes })}
          isCancelling={cancelMutation.isPending}
          isCompleting={completeMutation.isPending}
        />
      )}
    </div>
  )
}

// ============================================================================
// BOOKING DETAIL MODAL
// ============================================================================

interface BookingDetailModalProps {
  booking: Booking
  onClose: () => void
  onCancel: (reason?: string) => void
  onComplete: (notes?: string) => void
  isCancelling: boolean
  isCompleting: boolean
}

function BookingDetailModal({
  booking,
  onClose,
  onCancel,
  onComplete,
  isCancelling,
  isCompleting,
}: BookingDetailModalProps) {
  const [cancelReason, setCancelReason] = useState('')
  const [showCancelConfirm, setShowCancelConfirm] = useState(false)
  const [showCompleteConfirm, setShowCompleteConfirm] = useState(false)

  const formatDateTime = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—'
    try {
      return format(parseISO(dateStr), 'MMM d, yyyy HH:mm')
    } catch {
      return '—'
    }
  }

  const formatCurrency = (amount: number, currency: string = 'RUB') => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
    }).format(amount)
  }

  const canCancel = !['cancelled', 'completed', 'refunded'].includes(booking.status)
  const canComplete = booking.status === 'paid'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h2 className="font-display text-lg font-semibold text-white">Booking Details</h2>
            <p className="text-sm text-slate-400 font-mono">{booking.id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
          {/* Status Badge */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">Status:</span>
            <span
              className={clsx(
                'px-3 py-1 text-sm font-medium rounded-lg border',
                statusColors[booking.status] || statusColors.pending_payment
              )}
            >
              {statusLabels[booking.status] || booking.status}
            </span>
          </div>

          {/* Info Grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Nutritionist */}
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Nutritionist</p>
              <p className="text-white font-medium">{booking.nutritionist?.full_name || 'Unknown'}</p>
            </div>

            {/* Client */}
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Client</p>
              <p className="text-white font-medium">{booking.client?.full_name || 'Unknown'}</p>
              {booking.client?.telegram_user_id && (
                <p className="text-xs text-slate-500 mt-1">TG: {booking.client.telegram_user_id}</p>
              )}
            </div>

            {/* Service */}
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Service</p>
              <p className="text-white font-medium">{booking.service?.title || 'Unknown'}</p>
              {booking.service?.duration_minutes && (
                <p className="text-xs text-slate-500 mt-1">{booking.service.duration_minutes} min</p>
              )}
            </div>

            {/* Amount */}
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Amount</p>
              <p className="text-white font-medium text-lg">
                {formatCurrency(booking.price_rub, booking.currency)}
              </p>
            </div>
          </div>

          {/* Slot Time */}
          {booking.slot && (
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Slot Time</p>
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-sm text-slate-400">Start</p>
                  <p className="text-white font-medium">{formatDateTime(booking.slot.start_at)}</p>
                </div>
                <div className="text-slate-600">→</div>
                <div>
                  <p className="text-sm text-slate-400">End</p>
                  <p className="text-white font-medium">{formatDateTime(booking.slot.end_at)}</p>
                </div>
              </div>
            </div>
          )}

          {/* Payment Info */}
          {booking.payment && (
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Payment</p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-400">Provider</p>
                  <p className="text-white">{booking.payment.provider}</p>
                </div>
                <div>
                  <p className="text-slate-400">Status</p>
                  <p className="text-white capitalize">{booking.payment.status}</p>
                </div>
                {booking.payment.paid_at && (
                  <div className="col-span-2">
                    <p className="text-slate-400">Paid At</p>
                    <p className="text-white">{formatDateTime(booking.payment.paid_at)}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Meeting Link */}
          {booking.meeting_link && (
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Meeting Link</p>
              <a
                href={booking.meeting_link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-400 hover:text-accent-300 break-all"
              >
                {booking.meeting_link}
              </a>
            </div>
          )}

          {/* Timestamps */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-slate-400">Created</p>
              <p className="text-slate-300">{formatDateTime(booking.created_at)}</p>
            </div>
            {booking.paid_at && (
              <div>
                <p className="text-slate-400">Paid</p>
                <p className="text-slate-300">{formatDateTime(booking.paid_at)}</p>
              </div>
            )}
            {booking.cancelled_at && (
              <div>
                <p className="text-slate-400">Cancelled</p>
                <p className="text-slate-300">{formatDateTime(booking.cancelled_at)}</p>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            Close
          </button>

          <div className="flex items-center gap-3">
            {canComplete && !showCancelConfirm && (
              showCompleteConfirm ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">Confirm complete?</span>
                  <button
                    onClick={() => onComplete()}
                    disabled={isCompleting}
                    className="px-4 py-2 bg-success-500 text-white text-sm font-medium rounded-lg hover:bg-success-600 transition-colors disabled:opacity-50"
                  >
                    {isCompleting ? 'Completing...' : 'Yes, Complete'}
                  </button>
                  <button
                    onClick={() => setShowCompleteConfirm(false)}
                    className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowCompleteConfirm(true)}
                  className="px-4 py-2 bg-success-500/10 text-success-400 text-sm font-medium rounded-lg hover:bg-success-500/20 transition-colors"
                >
                  Mark Completed
                </button>
              )
            )}

            {canCancel && !showCompleteConfirm && (
              showCancelConfirm ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                    placeholder="Reason (optional)"
                    className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:border-error-500 focus:outline-none w-48"
                  />
                  <button
                    onClick={() => onCancel(cancelReason || undefined)}
                    disabled={isCancelling}
                    className="px-4 py-2 bg-error-500 text-white text-sm font-medium rounded-lg hover:bg-error-600 transition-colors disabled:opacity-50"
                  >
                    {isCancelling ? 'Cancelling...' : 'Confirm Cancel'}
                  </button>
                  <button
                    onClick={() => {
                      setShowCancelConfirm(false)
                      setCancelReason('')
                    }}
                    className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
                  >
                    Back
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowCancelConfirm(true)}
                  className="px-4 py-2 bg-error-500/10 text-error-400 text-sm font-medium rounded-lg hover:bg-error-500/20 transition-colors"
                >
                  Cancel Booking
                </button>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
