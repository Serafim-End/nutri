import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { Payment } from '@/types'
import { format } from 'date-fns'
import clsx from 'clsx'

type StatusFilter = 'all' | 'pending' | 'completed' | 'failed' | 'refunded' | 'expired'

const statusColors: Record<string, string> = {
  pending: 'bg-warning-500/10 text-warning-400 border-warning-500/20',
  completed: 'bg-success-500/10 text-success-400 border-success-500/20',
  failed: 'bg-error-500/10 text-error-400 border-error-500/20',
  refunded: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  expired: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
}

export function PaymentsPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [isExporting, setIsExporting] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'payments', statusFilter, dateFrom, dateTo],
    queryFn: () => adminApi.getPayments({
      status: statusFilter === 'all' ? undefined : statusFilter,
      from: dateFrom || undefined,
      to: dateTo || undefined,
    }),
  })

  const payments: Payment[] = data?.payments || []

  const filterButtons: { value: StatusFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'refunded', label: 'Refunded' },
    { value: 'expired', label: 'Expired' },
  ]

  const handleExportCsv = async () => {
    setIsExporting(true)
    try {
      const blob = await adminApi.exportPaymentsCsv(
        dateFrom || undefined,
        dateTo || undefined
      )
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `payments-export-${format(new Date(), 'yyyy-MM-dd')}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export CSV:', err)
    } finally {
      setIsExporting(false)
    }
  }

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-bold text-white mb-2">Payments</h1>
          <p className="text-slate-400">View and export payment transactions</p>
        </div>
        <button
          onClick={handleExportCsv}
          disabled={isExporting}
          className={clsx(
            'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
            isExporting
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-accent-500 text-white hover:bg-accent-600 shadow-glow'
          )}
        >
          {isExporting ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
              Exporting...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export CSV
            </>
          )}
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Status filter */}
        <div className="flex gap-2 p-1 bg-slate-925/50 border border-slate-800/50 rounded-xl">
          {filterButtons.map((btn) => (
            <button
              key={btn.value}
              onClick={() => setStatusFilter(btn.value)}
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

        {/* Date filters */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-400">From:</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800/50 text-sm text-white focus:outline-none focus:border-accent-500/50 transition-colors"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-400">To:</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800/50 text-sm text-white focus:outline-none focus:border-accent-500/50 transition-colors"
            />
          </div>
          {(dateFrom || dateTo) && (
            <button
              onClick={() => {
                setDateFrom('')
                setDateTo('')
              }}
              className="px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800/50 transition-colors"
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Failed to load payments
          </div>
        ) : payments.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <svg className="w-12 h-12 mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            <p className="font-medium text-slate-400 mb-1">No payments found</p>
            <p className="text-sm">
              {statusFilter !== 'all' || dateFrom || dateTo
                ? 'Try adjusting your filters.'
                : 'No payment transactions yet.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800/50">
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Payment ID
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Booking ID
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Nutritionist
                  </th>
                  <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Amount
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Status
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Provider
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                    Created At
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-slate-900/30 transition-colors">
                    <td className="px-6 py-4">
                      <span className="text-sm font-mono text-slate-300">
                        {payment.id.slice(0, 8)}...
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm font-mono text-slate-400">
                        {payment.booking_id.slice(0, 8)}...
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-white">{payment.nutritionist_name}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-sm font-medium text-white">
                        {formatAmount(payment.amount, payment.currency)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={clsx(
                          'px-2.5 py-1 text-xs font-medium rounded-lg border capitalize',
                          statusColors[payment.status] || statusColors.pending
                        )}
                      >
                        {payment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-400">{payment.provider}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {format(new Date(payment.created_at), 'MMM d, yyyy HH:mm')}
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
