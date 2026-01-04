import { forwardRef } from 'react'
import clsx from 'clsx'

export type BadgeVariant = 
  | 'default' 
  | 'primary' 
  | 'success' 
  | 'warning' 
  | 'error' 
  | 'info'
  | 'muted'

export type BadgeSize = 'sm' | 'md'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: BadgeSize
  dot?: boolean
  animated?: boolean
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-neutral-100 text-neutral-700',
  primary: 'bg-primary-100 text-primary-700',
  success: 'bg-success-50 text-success-700',
  warning: 'bg-warning-50 text-warning-700',
  error: 'bg-error-50 text-error-700',
  info: 'bg-info-50 text-info-700',
  muted: 'bg-neutral-50 text-neutral-500',
}

const dotColors: Record<BadgeVariant, string> = {
  default: 'bg-neutral-500',
  primary: 'bg-primary-500',
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  error: 'bg-error-500',
  info: 'bg-info-500',
  muted: 'bg-neutral-400',
}

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      variant = 'default',
      size = 'md',
      dot = false,
      animated = false,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <span
        ref={ref}
        className={clsx(
          'inline-flex items-center gap-1.5',
          'font-medium',
          'rounded-full',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={clsx(
              'w-1.5 h-1.5 rounded-full',
              dotColors[variant],
              animated && 'animate-pulse'
            )}
          />
        )}
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

// Status-specific badge presets
export type StatusBadgeStatus = 
  | 'pending' 
  | 'confirmed' 
  | 'cancelled' 
  | 'completed' 
  | 'refunded' 
  | 'no_show'

const statusConfig: Record<StatusBadgeStatus, { label: string; variant: BadgeVariant; dot?: boolean; animated?: boolean }> = {
  pending: { label: 'Awaiting Payment', variant: 'warning', dot: true, animated: true },
  confirmed: { label: 'Confirmed', variant: 'success' },
  cancelled: { label: 'Cancelled', variant: 'muted' },
  completed: { label: 'Completed', variant: 'info' },
  refunded: { label: 'Refunded', variant: 'default' },
  no_show: { label: 'No Show', variant: 'error' },
}

export interface StatusBadgeProps extends Omit<BadgeProps, 'variant' | 'children'> {
  status: StatusBadgeStatus
}

export function StatusBadge({ status, ...props }: StatusBadgeProps) {
  const config = statusConfig[status]
  return (
    <Badge
      variant={config.variant}
      dot={config.dot}
      animated={config.animated}
      {...props}
    >
      {config.label}
    </Badge>
  )
}

export default Badge


