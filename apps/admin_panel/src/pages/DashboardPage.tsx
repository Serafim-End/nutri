import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import clsx from 'clsx'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: { value: number; label: string }
  color: 'accent' | 'success' | 'warning' | 'error'
}

function StatCard({ title, value, icon, trend, color }: StatCardProps) {
  const colorClasses = {
    accent: 'from-accent-500/20 to-accent-600/10 border-accent-500/20',
    success: 'from-success-500/20 to-success-600/10 border-success-500/20',
    warning: 'from-warning-500/20 to-warning-600/10 border-warning-500/20',
    error: 'from-error-500/20 to-error-600/10 border-error-500/20',
  }

  const iconColorClasses = {
    accent: 'text-accent-400',
    success: 'text-success-400',
    warning: 'text-warning-400',
    error: 'text-error-400',
  }

  return (
    <div
      className={clsx(
        'p-6 rounded-2xl bg-gradient-to-br border backdrop-blur-sm',
        colorClasses[color]
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={clsx('p-2.5 rounded-xl bg-slate-900/50', iconColorClasses[color])}>
          {icon}
        </div>
        {trend && (
          <span
            className={clsx(
              'text-xs font-medium px-2 py-1 rounded-lg',
              trend.value >= 0
                ? 'text-success-400 bg-success-500/10'
                : 'text-error-400 bg-error-500/10'
            )}
          >
            {trend.value >= 0 ? '+' : ''}
            {trend.value}% {trend.label}
          </span>
        )}
      </div>
      <p className="text-3xl font-display font-bold text-white mb-1">{value}</p>
      <p className="text-sm text-slate-400">{title}</p>
    </div>
  )
}

export function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: adminApi.getStats,
    retry: false,
    staleTime: 0,
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: 30000,
  })

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-slate-400">Welcome back! Here's what's happening.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Users"
          value={isLoading || !stats ? '—' : stats.total_users.toLocaleString()}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          }
          trend={{ value: 12, label: 'this month' }}
          color="accent"
        />
        <StatCard
          title="Nutritionists"
          value={isLoading || !stats ? '—' : stats.total_nutritionists.toLocaleString()}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          }
          color="success"
        />
        <StatCard
          title="Pending Verifications"
          value={isLoading || !stats ? '—' : stats.pending_verifications}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="warning"
        />
        <StatCard
          title="Total Bookings"
          value={isLoading || !stats ? '—' : stats.total_bookings.toLocaleString()}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
          trend={{ value: 8, label: 'this week' }}
          color="accent"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Reviews */}
        <div className="p-6 rounded-2xl bg-slate-925/50 border border-slate-800/50">
          <h2 className="font-display text-lg font-semibold text-white mb-4">Pending Reviews</h2>
          <div className="space-y-3">
            {stats && stats.pending_verifications > 0 ? (
              <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/50 border border-slate-800/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-warning-500/10 flex items-center justify-center">
                    <svg className="w-5 h-5 text-warning-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">
                      {stats.pending_verifications} nutritionists awaiting review
                    </p>
                    <p className="text-xs text-slate-500">Review their credentials to approve</p>
                  </div>
                </div>
                <a
                  href="/admin/nutritionists"
                  className="px-4 py-2 rounded-lg text-sm font-medium text-accent-400 hover:bg-accent-500/10 transition-colors"
                >
                  Review →
                </a>
              </div>
            ) : (
              <div className="flex items-center justify-center p-8 text-slate-500 text-sm">
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 13l4 4L19 7" />
                </svg>
                {stats ? 'All caught up! No pending reviews.' : 'Loading stats...'}
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="p-6 rounded-2xl bg-slate-925/50 border border-slate-800/50">
          <h2 className="font-display text-lg font-semibold text-white mb-4">Recent Activity</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-center p-8 text-slate-500 text-sm">
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Activity feed coming soon
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
