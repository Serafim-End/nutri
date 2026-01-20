import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import { Nutritionist } from '@/types'
import { format } from 'date-fns'
import clsx from 'clsx'

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected' | 'needs_update'

const statusColors: Record<string, string> = {
  pending: 'bg-warning-500/10 text-warning-400 border-warning-500/20',
  approved: 'bg-success-500/10 text-success-400 border-success-500/20',
  rejected: 'bg-error-500/10 text-error-400 border-error-500/20',
  needs_update: 'bg-accent-500/10 text-accent-400 border-accent-500/20',
}

export function NutritionistsPage() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState<StatusFilter>('all')

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'nutritionists', filter === 'all' ? undefined : filter],
    queryFn: () => adminApi.getNutritionists(filter === 'all' ? undefined : filter),
  })

  const nutritionists: Nutritionist[] = data?.nutritionists || []

  const filterButtons: { value: StatusFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'approved', label: 'Approved' },
    { value: 'rejected', label: 'Rejected' },
    { value: 'needs_update', label: 'Needs Update' },
  ]

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-bold text-white mb-2">Nutritionists</h1>
          <p className="text-slate-400">Manage nutritionist verification and profiles</p>
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
            Failed to load nutritionists
          </div>
        ) : nutritionists.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <svg className="w-12 h-12 mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="font-medium text-slate-400 mb-1">No nutritionists found</p>
            <p className="text-sm">
              {filter !== 'all' ? `No ${filter} nutritionists at the moment.` : 'No nutritionists have registered yet.'}
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800/50">
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Nutritionist
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Specializations
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Rate
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Status
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Submitted
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Telegram
                </th>
                <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {nutritionists.map((n) => (
                <tr
                  key={n.id}
                  onClick={() => navigate(`/nutritionists/${n.id}`)}
                  className="hover:bg-slate-900/30 transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                        {n.profile?.photo_url ? (
                          <img
                            src={n.profile.photo_url}
                            alt=""
                            className="w-10 h-10 rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-sm font-semibold text-slate-300">
                            {n.full_name?.charAt(0).toUpperCase() || '?'}
                          </span>
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-white">{n.full_name}</p>
                        {n.years_experience && (
                          <p className="text-sm text-slate-500">{n.years_experience} years exp.</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {n.specializations?.slice(0, 2).map((s) => (
                        <span
                          key={s}
                          className="px-2 py-0.5 text-xs rounded-md bg-slate-800 text-slate-300"
                        >
                          {s}
                        </span>
                      ))}
                      {(n.specializations?.length || 0) > 2 && (
                        <span className="px-2 py-0.5 text-xs text-slate-500">
                          +{n.specializations.length - 2}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {n.currency && n.hourly_rate ? `${n.currency} ${n.hourly_rate}/hr` : '—'}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={clsx(
                        'px-2.5 py-1 text-xs font-medium rounded-lg border',
                        statusColors[n.verification_status] || statusColors.pending
                      )}
                    >
                      {n.verification_status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {n.submitted_at ? format(new Date(n.submitted_at), 'MMM d, yyyy') : '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {n.profile?.telegram_username ? (
                      <a
                        href={`https://t.me/${n.profile.telegram_username}`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-accent-400 hover:text-accent-300 transition-colors"
                        target="_blank"
                        rel="noreferrer"
                      >
                        @{n.profile.telegram_username}
                      </a>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/nutritionists/${n.id}`)
                      }}
                      className="px-3 py-1.5 text-sm font-medium text-accent-400 hover:bg-accent-500/10 rounded-lg transition-colors"
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
