import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { adminApi } from '@/lib/api'
import type { AdminUserEntry, AdminUsersResponse } from '@/types'

const SOURCE_LABELS: Record<string, string> = {
  mini_app: 'Мини‑приложение',
  bot_start: 'Бот /start',
  nutritionist_intent: 'Я нутрициолог',
}

const STATUS_LABELS: Record<string, string> = {
  client: 'Клиент',
  nutritionist: 'Нутрициолог',
  nutritionist_intent: 'Пробовал стать нутрициологом',
}

const STATUS_CLASSES: Record<string, string> = {
  client: 'bg-accent-500/10 text-accent-300 border-accent-500/30',
  nutritionist: 'bg-success-500/10 text-success-300 border-success-500/30',
  nutritionist_intent: 'bg-warning-500/10 text-warning-300 border-warning-500/30',
}

const formatDate = (value?: string | null) => {
  if (!value) return '—'
  return format(new Date(value), 'dd.MM.yyyy HH:mm')
}

export function UsersPage() {
  const { data, isLoading, error } = useQuery<AdminUsersResponse>({
    queryKey: ['admin', 'users'],
    queryFn: () => adminApi.getUsers({ page: 1, limit: 50 }),
    staleTime: 0,
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: 30000,
  })

  const users: AdminUserEntry[] = data?.users || []
  const stats = data?.stats

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-bold text-white mb-2">Users</h1>
          <p className="text-slate-400">Активность пользователей по Mini App и Telegram</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="rounded-xl bg-slate-925/50 border border-slate-800/50 p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Всего пользователей</p>
          <p className="text-2xl font-semibold text-white mt-1">{stats?.total_users ?? '—'}</p>
        </div>
        <div className="rounded-xl bg-slate-925/50 border border-slate-800/50 p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Mini App</p>
          <p className="text-2xl font-semibold text-white mt-1">{stats?.mini_app_users ?? '—'}</p>
        </div>
        <div className="rounded-xl bg-slate-925/50 border border-slate-800/50 p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Бот /start</p>
          <p className="text-2xl font-semibold text-white mt-1">{stats?.bot_start_users ?? '—'}</p>
        </div>
        <div className="rounded-xl bg-slate-925/50 border border-slate-800/50 p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Я нутрициолог</p>
          <p className="text-2xl font-semibold text-white mt-1">{stats?.nutritionist_intent_users ?? '—'}</p>
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Failed to load users
          </div>
        ) : users.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <svg className="w-12 h-12 mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="font-medium text-slate-400 mb-1">No users found</p>
            <p className="text-sm">There are no tracked users yet.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800/50">
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Пользователь
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Telegram
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Статусы
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Последняя активность
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Mini App
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Бот /start
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Я нутрициолог
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Создан
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-900/30 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      {user.photo_url ? (
                        <img
                          src={user.photo_url}
                          alt={user.full_name}
                          className="w-9 h-9 rounded-lg object-cover"
                        />
                      ) : (
                        <div className="w-9 h-9 rounded-lg bg-slate-800/60 flex items-center justify-center text-xs text-slate-400">
                          {user.full_name?.charAt(0) || 'U'}
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-medium text-white">{user.full_name}</p>
                        <p className="text-xs text-slate-500">{user.role}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-200">
                      {user.telegram_username ? `@${user.telegram_username}` : '—'}
                    </div>
                    <div className="text-xs text-slate-500">{user.telegram_user_id}</div>
                  </td>
                  <td className="px-6 py-4">
                    {user.user_statuses?.length ? (
                      <div className="flex flex-wrap gap-2">
                        {user.user_statuses.map((status) => (
                          <span
                            key={status}
                            className={`text-xs px-2 py-1 rounded-full border ${STATUS_CLASSES[status] || 'border-slate-700 text-slate-300'}`}
                          >
                            {STATUS_LABELS[status] || status}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-sm text-slate-500">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-200">
                      {user.last_seen_source ? SOURCE_LABELS[user.last_seen_source] : '—'}
                    </div>
                    <div className="text-xs text-slate-500">{formatDate(user.last_seen_at)}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-200">{formatDate(user.last_mini_app_at)}</td>
                  <td className="px-6 py-4 text-sm text-slate-200">{formatDate(user.last_bot_start_at)}</td>
                  <td className="px-6 py-4 text-sm text-slate-200">{formatDate(user.last_nutritionist_intent_at)}</td>
                  <td className="px-6 py-4 text-sm text-slate-200">{formatDate(user.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
