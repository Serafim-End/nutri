import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { SupportTicket } from '@/types'
import { format } from 'date-fns'
import clsx from 'clsx'

type StatusFilter = 'all' | 'open' | 'closed'

const statusColors: Record<string, string> = {
  open: 'bg-warning-500/10 text-warning-400 border-warning-500/20',
  closed: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
}

const roleColors: Record<string, string> = {
  client: 'bg-accent-500/10 text-accent-400 border-accent-500/20',
  nutritionist: 'bg-success-500/10 text-success-400 border-success-500/20',
}

export function SupportPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<StatusFilter>('all')
  const [closingId, setClosingId] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'support', filter === 'all' ? undefined : filter],
    queryFn: () => adminApi.getSupportTickets(filter === 'all' ? undefined : filter),
  })

  const closeMutation = useMutation({
    mutationFn: (id: string) => adminApi.closeSupportTicket(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'support'] })
      setClosingId(null)
    },
    onError: () => {
      setClosingId(null)
    },
  })

  const tickets: SupportTicket[] = data?.tickets || []

  const filterButtons: { value: StatusFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'open', label: 'Open' },
    { value: 'closed', label: 'Closed' },
  ]

  const handleClose = (id: string) => {
    setClosingId(id)
    closeMutation.mutate(id)
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-bold text-white mb-2">Support Tickets</h1>
          <p className="text-slate-400">Manage support requests from clients and nutritionists</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6 p-1 bg-slate-925/50 border border-slate-800/50 rounded-xl w-fit">
        {filterButtons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => setFilter(btn.value)}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
              filter === btn.value
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            )}
          >
            {btn.label}
          </button>
        ))}
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Failed to load support tickets
          </div>
        ) : tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <svg className="w-12 h-12 mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <p className="font-medium text-slate-400 mb-1">No support tickets</p>
            <p className="text-sm">
              {filter !== 'all' ? `No ${filter} tickets at the moment.` : 'No support tickets have been submitted yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800/50">
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Author
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Role
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4 max-w-md">
                    Message
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Booking ID
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Status
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Created
                  </th>
                  <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {tickets.map((ticket) => (
                  <tr
                    key={ticket.id}
                    onClick={() => navigate(`/support/${ticket.id}`)}
                    className="hover:bg-slate-900/30 transition-colors cursor-pointer"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center flex-shrink-0">
                          <span className="text-sm font-semibold text-slate-300">
                            {ticket.author_name?.charAt(0).toUpperCase() || '?'}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-white truncate">{ticket.author_name || 'Unknown'}</p>
                          <p className="text-xs text-slate-500 truncate">ID: {ticket.author_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={clsx(
                          'px-2.5 py-1 text-xs font-medium rounded-lg border capitalize',
                          roleColors[ticket.role] || roleColors.client
                        )}
                      >
                        {ticket.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 max-w-md">
                      <p className="text-sm text-slate-300 line-clamp-2" title={ticket.text}>
                        {ticket.text}
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      {ticket.booking_id ? (
                        <span className="text-sm text-slate-300 font-mono">
                          {ticket.booking_id.slice(0, 8)}...
                        </span>
                      ) : (
                        <span className="text-sm text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={clsx(
                          'px-2.5 py-1 text-xs font-medium rounded-lg border capitalize',
                          statusColors[ticket.status] || statusColors.open
                        )}
                      >
                        {ticket.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500 whitespace-nowrap">
                      {ticket.created_at ? format(new Date(ticket.created_at), 'MMM d, yyyy HH:mm') : '—'}
                    </td>
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      {ticket.status === 'open' ? (
                        <button
                          onClick={() => handleClose(ticket.id)}
                          disabled={closingId === ticket.id}
                          className={clsx(
                            'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                            closingId === ticket.id
                              ? 'text-slate-500 cursor-not-allowed'
                              : 'text-accent-400 hover:bg-accent-500/10'
                          )}
                        >
                          {closingId === ticket.id ? (
                            <span className="flex items-center gap-2">
                              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                              </svg>
                              Closing...
                            </span>
                          ) : (
                            'Close'
                          )}
                        </button>
                      ) : (
                        <span className="text-sm text-slate-600">Closed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

