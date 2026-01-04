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
      {/* Иконка или эмодзи */}
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

      {/* Заголовок */}
      <h3 className="text-lg font-semibold text-text-primary">{title}</h3>

      {/* Описание */}
      {description && (
        <p className="mt-2 text-sm text-text-secondary max-w-xs mx-auto">
          {description}
        </p>
      )}

      {/* Действия */}
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
// ГОТОВЫЕ СОСТОЯНИЯ
// ============================================================================

export function NoResultsState({
  onAction,
  actionLabel = 'Изменить фильтры',
}: {
  onAction?: () => void
  actionLabel?: string
}) {
  return (
    <EmptyState
      emoji="🔍"
      title="Ничего не найдено"
      description="Попробуйте изменить параметры поиска, чтобы увидеть больше результатов."
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
      title="Бронирований пока нет"
      description="Забронируйте первую консультацию с нутрициологом."
      action={onAction ? { label: 'Найти нутрициолога', onClick: onAction } : undefined}
    />
  )
}

export function NoSlotsState() {
  return (
    <EmptyState
      emoji="📅"
      title="Нет доступных слотов"
      description="У этого специалиста сейчас нет свободного времени. Попробуйте позже."
    />
  )
}

export function ErrorState({
  title = 'Что-то пошло не так',
  description = 'Произошла ошибка. Пожалуйста, попробуйте ещё раз.',
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
      action={onRetry ? { label: 'Попробовать снова', onClick: onRetry } : undefined}
    />
  )
}

export function NotFoundState({ onBack }: { onBack?: () => void }) {
  return (
    <EmptyState
      emoji="🔎"
      title="Не найдено"
      description="Страница или элемент, который вы ищете, не существует."
      action={onBack ? { label: 'Назад', onClick: onBack } : undefined}
    />
  )
}

export default EmptyState
