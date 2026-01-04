import clsx from 'clsx'
import { Button } from './Button'

export interface EmptyStateProps {
  icon?: React.ReactNode
  emoji?: string
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({
  icon,
  emoji,
  title,
  description,
  action,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={clsx('text-center py-12 px-4', className)}>
      {/* Icon or Emoji */}
      {(icon || emoji) && (
        <div className="mb-4">
          {icon ? (
            <div className="w-16 h-16 mx-auto bg-neutral-100 rounded-full flex items-center justify-center">
              <div className="text-neutral-400">{icon}</div>
            </div>
          ) : (
            <span className="text-5xl">{emoji}</span>
          )}
        </div>
      )}

      {/* Title */}
      <h3 className="text-lg font-semibold text-text-primary">{title}</h3>

      {/* Description */}
      {description && (
        <p className="mt-2 text-sm text-text-secondary max-w-xs mx-auto">
          {description}
        </p>
      )}

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          {action && (
            <Button onClick={action.onClick}>{action.label}</Button>
          )}
          {secondaryAction && (
            <Button variant="secondary" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// PRESET EMPTY STATES
// ============================================================================

export function NoResultsState({
  onAction,
  actionLabel = 'Adjust Filters',
}: {
  onAction?: () => void
  actionLabel?: string
}) {
  return (
    <EmptyState
      emoji="🔍"
      title="No results found"
      description="Try adjusting your filters to see more results."
      action={onAction ? { label: actionLabel, onClick: onAction } : undefined}
    />
  )
}

export function NoBookingsState({ onAction }: { onAction?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      }
      title="No bookings yet"
      description="Book your first consultation with a nutritionist to get started."
      action={onAction ? { label: 'Find a Nutritionist', onClick: onAction } : undefined}
    />
  )
}

export function NoSlotsState() {
  return (
    <EmptyState
      emoji="📅"
      title="No available slots"
      description="This nutritionist doesn't have any available time slots at the moment. Please check back later."
    />
  )
}

export function ErrorState({
  title = 'Something went wrong',
  description = 'An error occurred. Please try again.',
  onRetry,
}: {
  title?: string
  description?: string
  onRetry?: () => void
}) {
  return (
    <EmptyState
      emoji="⚠️"
      title={title}
      description={description}
      action={onRetry ? { label: 'Try Again', onClick: onRetry } : undefined}
    />
  )
}

export function NotFoundState({ onBack }: { onBack?: () => void }) {
  return (
    <EmptyState
      emoji="🔎"
      title="Not found"
      description="The page or item you're looking for doesn't exist."
      action={onBack ? { label: 'Go Back', onClick: onBack } : undefined}
    />
  )
}

export default EmptyState


