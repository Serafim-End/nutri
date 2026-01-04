import { forwardRef } from 'react'
import clsx from 'clsx'

export type InputSize = 'sm' | 'md' | 'lg'

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  size?: InputSize
  error?: boolean
  errorMessage?: string
  label?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const sizeStyles: Record<InputSize, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-11 px-4 text-base',
  lg: 'h-13 px-4 text-base',
}

const iconSizeStyles: Record<InputSize, string> = {
  sm: 'pl-9',
  md: 'pl-11',
  lg: 'pl-12',
}

const rightIconSizeStyles: Record<InputSize, string> = {
  sm: 'pr-9',
  md: 'pr-11',
  lg: 'pr-12',
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      size = 'md',
      error = false,
      errorMessage,
      label,
      hint,
      leftIcon,
      rightIcon,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s/g, '-') : undefined)

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-text-primary mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              'w-full rounded-xl',
              'bg-surface-primary',
              'border transition-all duration-fast',
              error
                ? 'border-error-500 focus:ring-2 focus:ring-error-500/20'
                : 'border-border-default focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
              'placeholder:text-text-tertiary',
              'focus:outline-none',
              'disabled:bg-neutral-50 disabled:text-text-tertiary disabled:cursor-not-allowed',
              sizeStyles[size],
              leftIcon && iconSizeStyles[size],
              rightIcon && rightIconSizeStyles[size],
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary">
              {rightIcon}
            </div>
          )}
        </div>
        {(errorMessage || hint) && (
          <p
            className={clsx(
              'mt-1.5 text-sm',
              error ? 'text-error-600' : 'text-text-tertiary'
            )}
          >
            {errorMessage || hint}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

// Textarea variant
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
  errorMessage?: string
  label?: string
  hint?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      error = false,
      errorMessage,
      label,
      hint,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const textareaId = id || (label ? label.toLowerCase().replace(/\s/g, '-') : undefined)

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-text-primary mb-1.5"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={clsx(
            'w-full rounded-xl px-4 py-3 min-h-[100px]',
            'bg-surface-primary',
            'border transition-all duration-fast',
            error
              ? 'border-error-500 focus:ring-2 focus:ring-error-500/20'
              : 'border-border-default focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
            'placeholder:text-text-tertiary',
            'focus:outline-none resize-none',
            'disabled:bg-neutral-50 disabled:text-text-tertiary disabled:cursor-not-allowed',
            className
          )}
          {...props}
        />
        {(errorMessage || hint) && (
          <p
            className={clsx(
              'mt-1.5 text-sm',
              error ? 'text-error-600' : 'text-text-tertiary'
            )}
          >
            {errorMessage || hint}
          </p>
        )}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'

export default Input


