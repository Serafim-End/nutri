import clsx from 'clsx'

// ============================================================================
// SPINNER
// ============================================================================

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeStyles = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <svg
      className={clsx('animate-spin text-primary-500', sizeStyles[size], className)}
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  )
}

// ============================================================================
// SKELETON
// ============================================================================

export interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded'
  width?: string | number
  height?: string | number
  className?: string
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  className,
}: SkeletonProps) {
  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  }

  return (
    <div
      className={clsx(
        'animate-pulse bg-neutral-200',
        variant === 'text' && 'h-4 rounded',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && '',
        variant === 'rounded' && 'rounded-xl',
        className
      )}
      style={style}
    />
  )
}

// ============================================================================
// SKELETON CARD (Common pattern)
// ============================================================================

export function SkeletonCard() {
  return (
    <div className="bg-surface-primary rounded-2xl border border-border-light p-4 animate-pulse">
      <div className="flex gap-4">
        <Skeleton variant="rounded" width={64} height={64} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="100%" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// LOADING OVERLAY
// ============================================================================

export interface LoadingOverlayProps {
  isLoading: boolean
  children: React.ReactNode
  text?: string
}

export function LoadingOverlay({ isLoading, children, text }: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-surface-primary/80 backdrop-blur-sm flex flex-col items-center justify-center gap-3 rounded-2xl">
          <Spinner size="lg" />
          {text && <p className="text-sm text-text-secondary">{text}</p>}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// FULL PAGE LOADER
// ============================================================================

export interface PageLoaderProps {
  text?: string
  logo?: React.ReactNode
}

export function PageLoader({ text = 'Loading...', logo }: PageLoaderProps) {
  return (
    <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center gap-6">
      {logo ? (
        <div className="animate-pulse">{logo}</div>
      ) : (
        <div className="w-16 h-16 bg-primary-500 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/20 animate-pulse">
          <svg
            className="w-10 h-10 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
      )}
      <div className="text-center">
        <h1 className="text-xl font-semibold text-text-primary">NutriMatch</h1>
        <p className="mt-1 text-sm text-text-secondary">{text}</p>
      </div>
    </div>
  )
}

export default Spinner


