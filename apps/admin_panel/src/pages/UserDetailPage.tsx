import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { format } from 'date-fns'
import { adminApi } from '@/lib/api'
import type { AdminUserDetailResponse, AdminUserSession, Booking, AdminPaymentRecord } from '@/types'

const SOURCE_LABELS: Record<string, string> = {
  mini_app: 'Мини‑приложение',
  bot_start: 'Бот /start',
  nutritionist_intent: 'Я нутрициолог',
}

const formatDate = (value?: string | null) => {
  if (!value) return '—'
  return format(new Date(value), 'dd.MM.yyyy HH:mm')
}

export function UserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery<AdminUserDetailResponse>({
    queryKey: ['admin', 'user', id],
    queryFn: () => adminApi.getUserDetail(id!),
    enabled: !!id,
  })

  const user = data?.user
  const sessions: AdminUserSession[] = data?.sessions || []
  const bookings: Booking[] = data?.bookings || []
  const payments: AdminPaymentRecord[] = data?.payments || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-400">
        <svg className="w-16 h-16 mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-lg font-medium mb-2">User not found</p>
        <button
          onClick={() => navigate('/users')}
          className="text-accent-400 hover:text-accent-300 transition-colors"
        >
          ← Back to list
        </button>
      </div>
    )
  }

  return (
    <div className="animate-fade-in space-y-6">
      <button
        onClick={() => navigate('/users')}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Users
      </button>

      <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
        <div className="flex items-start gap-4">
          {user.photo_url ? (
            <img
              src={user.photo_url}
              alt={user.full_name}
              className="w-16 h-16 rounded-xl object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-xl bg-slate-800/60 flex items-center justify-center text-sm text-slate-400">
              {user.full_name?.charAt(0) || 'U'}
            </div>
          )}
          <div>
            <h1 className="text-2xl font-bold text-white">{user.full_name}</h1>
            <p className="text-sm text-slate-400">{user.role}</p>
            <div className="text-sm text-slate-300 mt-2">
              {user.telegram_username ? `@${user.telegram_username}` : '—'} · {user.telegram_user_id}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Создан: {formatDate(user.created_at)}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800/50">
            <h2 className="text-sm font-semibold text-slate-200">Все входы</h2>
            <p className="text-xs text-slate-500 mt-1">Всего: {sessions.length}</p>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800/50">
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Источник
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Время
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Бронь
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Оплата
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {sessions.length ? (
                sessions.map((session) => (
                  <tr key={session.id} className="hover:bg-slate-900/30 transition-colors">
                    <td className="px-6 py-3 text-sm text-slate-200">
                      {SOURCE_LABELS[session.source] || session.source}
                    </td>
                    <td className="px-6 py-3 text-sm text-slate-300">
                      {formatDate(session.started_at)}
                    </td>
                    <td className="px-6 py-3 text-sm">
                      <span className={session.booking_made ? 'text-success-300' : 'text-slate-500'}>
                        {session.booking_made ? 'да' : 'нет'}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm">
                      <span className={session.payment_made ? 'text-success-300' : 'text-slate-500'}>
                        {session.payment_made ? 'да' : 'нет'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-6 py-4 text-sm text-slate-500" colSpan={4}>
                    Нет входов
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800/50">
            <h2 className="text-sm font-semibold text-slate-200">Оплаты</h2>
            <p className="text-xs text-slate-500 mt-1">Всего: {payments.length}</p>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800/50">
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Сумма
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Статус
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Провайдер
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                  Время
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {payments.length ? (
                payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-slate-900/30 transition-colors">
                    <td className="px-6 py-3 text-sm text-slate-200">
                      {payment.amount_rub} {payment.currency}
                    </td>
                    <td className="px-6 py-3 text-sm text-slate-300">{payment.status}</td>
                    <td className="px-6 py-3 text-sm text-slate-400">{payment.provider}</td>
                    <td className="px-6 py-3 text-sm text-slate-500">
                      {formatDate(payment.created_at)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-6 py-4 text-sm text-slate-500" colSpan={4}>
                    Оплат нет
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800/50">
          <h2 className="text-sm font-semibold text-slate-200">Бронирования</h2>
          <p className="text-xs text-slate-500 mt-1">Всего: {bookings.length}</p>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800/50">
              <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                Нутрициолог
              </th>
              <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                Услуга
              </th>
              <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                Статус
              </th>
              <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                Цена
              </th>
              <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                Создано
              </th>
              <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-3">
                Оплачено
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {bookings.length ? (
              bookings.map((booking) => (
                <tr key={booking.id} className="hover:bg-slate-900/30 transition-colors">
                  <td className="px-6 py-3 text-sm text-slate-200">
                    {booking.nutritionist?.full_name || '—'}
                  </td>
                  <td className="px-6 py-3 text-sm text-slate-300">
                    {booking.service?.title || '—'}
                  </td>
                  <td className="px-6 py-3 text-sm text-slate-300">{booking.status}</td>
                  <td className="px-6 py-3 text-sm text-slate-300">
                    {booking.price_rub} {booking.currency}
                  </td>
                  <td className="px-6 py-3 text-sm text-slate-500">
                    {formatDate(booking.created_at)}
                  </td>
                  <td className="px-6 py-3 text-sm text-slate-500">
                    {formatDate(booking.paid_at)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-6 py-4 text-sm text-slate-500" colSpan={6}>
                  Бронирований нет
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
