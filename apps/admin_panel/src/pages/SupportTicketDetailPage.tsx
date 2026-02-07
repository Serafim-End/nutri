import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { format } from 'date-fns'
import { adminApi } from '@/lib/api'
import type {
  SupportTicketDetailResponse,
  AdminUserSession,
  Booking,
} from '@/types'
import clsx from 'clsx'

const SOURCE_LABELS: Record<string, string> = {
  mini_app: 'Mini app',
  bot_start: 'Bot /start',
  nutritionist_intent: 'Nutritionist intent',
}

const statusColors: Record<string, string> = {
  open: 'bg-warning-500/10 text-warning-400 border-warning-500/20',
  closed: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
}

const roleColors: Record<string, string> = {
  client: 'bg-accent-500/10 text-accent-400 border-accent-500/20',
  nutritionist: 'bg-success-500/10 text-success-400 border-success-500/20',
}

const formatDate = (value?: string | null) => {
  if (!value) return '—'
  return format(new Date(value), 'MMM d, yyyy HH:mm')
}

function telegramContactUrl(ticket: SupportTicketDetailResponse['ticket']): string {
  const username = ticket.telegram_username
  const userId = ticket.telegram_user_id
  if (username) return `https://t.me/${username.replace(/^@/, '')}`
  if (userId) return `https://t.me/user?id=${userId}`
  return '#'
}

export function SupportTicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery<SupportTicketDetailResponse>({
    queryKey: ['admin', 'support', 'ticket', id],
    queryFn: () => adminApi.getSupportTicketDetail(id!),
    enabled: !!id,
  })

  const closeMutation = useMutation({
    mutationFn: (ticketId: string) => adminApi.closeSupportTicket(ticketId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'support'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'support', 'ticket', id] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !data?.ticket) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-400">
        <svg
          className="w-16 h-16 mb-4 text-slate-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-lg font-medium mb-2">Ticket not found</p>
        <button
          onClick={() => navigate('/support')}
          className="text-accent-400 hover:text-accent-300 transition-colors"
        >
          ← Back to Support
        </button>
      </div>
    )
  }

  const { ticket, author, sessions, booking } = data
  const displayName = author?.full_name ?? ticket.author_name ?? 'Unknown'
  const photoUrl = author?.photo_url ?? null
  const canContactTelegram = !!(ticket.telegram_username || ticket.telegram_user_id)

  return (
    <div className="animate-fade-in space-y-6">
      <button
        onClick={() => navigate('/support')}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10 19l-7-7m0 0l7-7m-7 7h18"
          />
        </svg>
        Back to Support
      </button>

      {/* Header card: author avatar, name, role, status, created */}
      <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
        <div className="flex items-start gap-4">
          {photoUrl ? (
            <img
              src={photoUrl}
              alt={displayName}
              className="w-16 h-16 rounded-xl object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-xl bg-slate-800/60 flex items-center justify-center text-xl font-semibold text-slate-300">
              {displayName.charAt(0).toUpperCase() || '?'}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-white">{displayName}</h1>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span
                className={clsx(
                  'px-2.5 py-1 text-xs font-medium rounded-lg border capitalize',
                  roleColors[ticket.role] ?? roleColors.client
                )}
              >
                {ticket.role}
              </span>
              <span
                className={clsx(
                  'px-2.5 py-1 text-xs font-medium rounded-lg border capitalize',
                  statusColors[ticket.status] ?? statusColors.open
                )}
              >
                {ticket.status}
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-2">Created: {formatDate(ticket.created_at)}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Contact info card */}
        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
          <h2 className="text-sm font-semibold text-slate-200 mb-4">Contact</h2>
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-slate-500">Telegram username</dt>
              <dd className="text-slate-200 font-mono">
                {ticket.telegram_username ? `@${ticket.telegram_username}` : '—'}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Telegram user ID</dt>
              <dd className="text-slate-200 font-mono">
                {ticket.telegram_user_id ?? '—'}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Profile ID</dt>
              <dd className="text-slate-200 font-mono truncate" title={ticket.author_id}>
                {ticket.author_id}
              </dd>
            </div>
          </dl>
          {canContactTelegram && (
            <a
              href={telegramContactUrl(ticket)}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0088cc]/20 text-[#54a9eb] border border-[#0088cc]/30 hover:bg-[#0088cc]/30 transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18 1.897-.962 6.502-1.359 8.627-.168.9-.5 1.201-.82 1.23-.697.064-1.226-.461-1.901-.903-1.056-.693-1.653-1.124-2.678-1.8-1.185-.781-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.44-.752-.244-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.015 3.333-1.386 4.025-1.627 4.477-1.635.099-.002.321.023.465.141.121.1.154.234.17.332.015.098.034.32.019.494z" />
              </svg>
              Contact via Telegram
            </a>
          )}
        </div>

        {/* Actions card */}
        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
          <h2 className="text-sm font-semibold text-slate-200 mb-4">Actions</h2>
          {ticket.status === 'open' ? (
            <button
              onClick={() => closeMutation.mutate(ticket.id)}
              disabled={closeMutation.isPending}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-warning-500/20 text-warning-400 border border-warning-500/30 hover:bg-warning-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {closeMutation.isPending ? 'Closing…' : 'Close ticket'}
            </button>
          ) : (
            <p className="text-sm text-slate-400">This ticket is closed.</p>
          )}
        </div>
      </div>

      {/* Full message card */}
      <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
        <h2 className="text-sm font-semibold text-slate-200 mb-3">Message</h2>
        <p className="text-slate-200 whitespace-pre-wrap break-words">{ticket.text}</p>
      </div>

      {/* Booking card (if linked) */}
      {booking && (
        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800/50">
            <h2 className="text-sm font-semibold text-slate-200">Linked booking</h2>
          </div>
          <div className="p-6">
            <BookingSummary booking={booking} />
          </div>
        </div>
      )}

      {/* Sessions table */}
      <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800/50">
          <h2 className="text-sm font-semibold text-slate-200">Last 100 sessions</h2>
          <p className="text-xs text-slate-500 mt-1">
            {sessions.length === 0
              ? 'No session data (author may not have a profile or has no sessions).'
              : `Total: ${sessions.length}`}
          </p>
        </div>
        {sessions.length > 0 ? (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800/50">
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Source
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Time
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Booking made
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Payment made
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {sessions.map((session: AdminUserSession) => (
                <tr key={session.id} className="hover:bg-slate-900/30 transition-colors">
                  <td className="px-6 py-3 text-sm text-slate-200">
                    {SOURCE_LABELS[session.source] ?? session.source}
                  </td>
                  <td className="px-6 py-3 text-sm text-slate-300">
                    {formatDate(session.started_at)}
                  </td>
                  <td className="px-6 py-3 text-sm">
                    <span
                      className={
                        session.booking_made ? 'text-success-300' : 'text-slate-500'
                      }
                    >
                      {session.booking_made ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-sm">
                    <span
                      className={
                        session.payment_made ? 'text-success-300' : 'text-slate-500'
                      }
                    >
                      {session.payment_made ? 'Yes' : 'No'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="px-6 py-8 text-center text-sm text-slate-500">
            No session data available.
          </div>
        )}
      </div>
    </div>
  )
}

function BookingSummary({ booking }: { booking: Booking }) {
  return (
    <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
      <div>
        <dt className="text-slate-500">Nutritionist</dt>
        <dd className="text-slate-200">{booking.nutritionist?.full_name ?? '—'}</dd>
      </div>
      <div>
        <dt className="text-slate-500">Service</dt>
        <dd className="text-slate-200">{booking.service?.title ?? '—'}</dd>
      </div>
      <div>
        <dt className="text-slate-500">Status</dt>
        <dd className="text-slate-200">{booking.status}</dd>
      </div>
      <div>
        <dt className="text-slate-500">Price</dt>
        <dd className="text-slate-200">
          {booking.price_rub} {booking.currency}
        </dd>
      </div>
      <div>
        <dt className="text-slate-500">Created</dt>
        <dd className="text-slate-200">{formatDate(booking.created_at)}</dd>
      </div>
      <div>
        <dt className="text-slate-500">Paid at</dt>
        <dd className="text-slate-200">{formatDate(booking.paid_at)}</dd>
      </div>
    </dl>
  )
}
