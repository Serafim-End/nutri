import { useState, useCallback, createContext, useContext } from 'react'
import clsx from 'clsx'

export type AlertVariant = 'info' | 'success' | 'warning' | 'error'

// ============================================================================
// TOAST DATA TYPE
// ============================================================================

export interface ToastData {
  id: string
  variant: AlertVariant
  title?: string
  message: string
  duration?: number
}

// ============================================================================
// TOAST ITEM COMPONENT
// ============================================================================

const alertStyles: Record<AlertVariant, string> = {
  info: 'bg-info-50 border-info-200 text-info-700',
  success: 'bg-success-50 border-success-200 text-success-700',
  warning: 'bg-warning-50 border-warning-200 text-warning-700',
  error: 'bg-error-50 border-error-200 text-error-700',
}

const alertIcons: Record<AlertVariant, React.ReactNode> = {
  info: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  success: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
}

interface ToastItemProps extends ToastData {
  onRemove: (id: string) => void
}

function ToastItem({ id, variant, title, message, duration = 4000, onRemove }: ToastItemProps) {
  // Auto-remove after duration
  useState(() => {
    if (duration > 0) {
      const timer = setTimeout(() => onRemove(id), duration)
      return () => clearTimeout(timer)
    }
  })

  return (
    <div
      className={clsx(
        'w-full max-w-sm rounded-xl border px-4 py-3 shadow-lg',
        'flex items-start gap-3',
        'animate-slide-up',
        alertStyles[variant]
      )}
      role="alert"
    >
      <div className="flex-shrink-0 mt-0.5">{alertIcons[variant]}</div>
      <div className="flex-1 min-w-0">
        {title && <p className="font-medium">{title}</p>}
        <p className={clsx('text-sm', title && 'mt-0.5')}>{message}</p>
      </div>
      <button
        onClick={() => onRemove(id)}
        className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  )
}

// ============================================================================
// TOAST CONTEXT & PROVIDER
// ============================================================================

interface ToastContextValue {
  toast: (options: Omit<ToastData, 'id'>) => void
  success: (message: string) => void
  error: (message: string) => void
  warning: (message: string) => void
  info: (message: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastData[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback((options: Omit<ToastData, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    setToasts((prev) => [...prev, { ...options, id }])
  }, [])

  const toast = useCallback(
    (options: Omit<ToastData, 'id'>) => addToast(options),
    [addToast]
  )

  const success = useCallback(
    (message: string) => addToast({ variant: 'success', message }),
    [addToast]
  )

  const error = useCallback(
    (message: string) => addToast({ variant: 'error', message }),
    [addToast]
  )

  const warning = useCallback(
    (message: string) => addToast({ variant: 'warning', message }),
    [addToast]
  )

  const info = useCallback(
    (message: string) => addToast({ variant: 'info', message }),
    [addToast]
  )

  return (
    <ToastContext.Provider value={{ toast, success, error, warning, info }}>
      {children}
      {/* Toast container */}
      <div className="fixed top-4 right-4 left-4 z-toast flex flex-col items-end gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto w-full flex justify-end">
            <ToastItem {...t} onRemove={removeToast} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

