import { forwardRef } from 'react'
import clsx from 'clsx'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: clsx(
    'bg-primary-500 text-white',
    'hover:bg-primary-600 active:bg-primary-700',
    'shadow-sm hover:shadow-md',
    'disabled:bg-neutral-200 disabled:text-neutral-400 disabled:shadow-none'
  ),
  secondary: clsx(
    'bg-surface-secondary text-text-primary border border-border-default',
    'hover:bg-neutral-100 active:bg-neutral-200',
    'disabled:bg-neutral-50 disabled:text-neutral-400 disabled:border-neutral-200'
  ),
  ghost: clsx(
    'bg-transparent text-text-primary',
    'hover:bg-neutral-100 active:bg-neutral-200',
    'disabled:text-neutral-400'
  ),
  destructive: clsx(
    'bg-error-500 text-white',
    'hover:bg-error-600 active:bg-error-700',
    'shadow-sm',
    'disabled:bg-neutral-200 disabled:text-neutral-400 disabled:shadow-none'
  ),
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5 rounded-lg',
  md: 'h-11 px-5 text-base gap-2 rounded-xl',
  lg: 'h-13 px-6 text-base gap-2 rounded-xl',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      leftIcon,
      rightIcon,
      className,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={clsx(
          // Base styles
          'inline-flex items-center justify-center',
          'font-semibold',
          'transition-all duration-fast',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
          'active:scale-[0.98]',
          'disabled:cursor-not-allowed disabled:active:scale-100',
          // Variant & size
          variantStyles[variant],
          sizeStyles[size],
          // Full width
          fullWidth && 'w-full',
          className
        )}
        {...props}
      >
        {loading ? (
          <Spinner size={size} />
        ) : (
          <>
            {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
          </>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'

// Internal spinner component
function Spinner({ size }: { size: ButtonSize }) {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'
  return (
    <svg
      className={clsx(sizeClass, 'animate-spin')}
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

export default Button


