import { forwardRef, useState, useRef, useEffect } from 'react'
import clsx from 'clsx'

// ============================================================================
// SELECT (Single)
// ============================================================================

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps {
  options: SelectOption[]
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  label?: string
  error?: boolean
  errorMessage?: string
  disabled?: boolean
  className?: string
}

export const Select = forwardRef<HTMLDivElement, SelectProps>(
  (
    {
      options,
      value,
      onChange,
      placeholder = 'Select an option',
      label,
      error = false,
      errorMessage,
      disabled = false,
      className,
    },
    ref
  ) => {
    const [isOpen, setIsOpen] = useState(false)
    const containerRef = useRef<HTMLDivElement>(null)

    const selectedOption = options.find((opt) => opt.value === value)

    // Close on click outside
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
          setIsOpen(false)
        }
      }
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const handleSelect = (optionValue: string) => {
      onChange?.(optionValue)
      setIsOpen(false)
    }

    return (
      <div ref={ref} className={clsx('w-full', className)}>
        {label && (
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            {label}
          </label>
        )}
        <div ref={containerRef} className="relative">
          <button
            type="button"
            onClick={() => !disabled && setIsOpen(!isOpen)}
            disabled={disabled}
            className={clsx(
              'w-full h-11 px-4 rounded-xl',
              'bg-surface-primary',
              'border transition-all duration-fast',
              'flex items-center justify-between gap-2',
              'text-left',
              error
                ? 'border-error-500'
                : isOpen
                ? 'border-primary-500 ring-2 ring-primary-500/20'
                : 'border-border-default hover:border-border-strong',
              disabled && 'opacity-50 cursor-not-allowed bg-neutral-50'
            )}
          >
            <span className={clsx(selectedOption ? 'text-text-primary' : 'text-text-tertiary')}>
              {selectedOption?.label || placeholder}
            </span>
            <ChevronIcon isOpen={isOpen} />
          </button>

          {isOpen && (
            <div
              className={clsx(
                'absolute z-dropdown mt-1 w-full',
                'bg-surface-primary rounded-xl',
                'border border-border-default shadow-lg',
                'py-1 max-h-60 overflow-auto',
                'animate-fade-in'
              )}
            >
              {options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => !option.disabled && handleSelect(option.value)}
                  disabled={option.disabled}
                  className={clsx(
                    'w-full px-4 py-2.5 text-left',
                    'transition-colors duration-fast',
                    option.disabled
                      ? 'text-text-tertiary cursor-not-allowed'
                      : option.value === value
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-text-primary hover:bg-neutral-50'
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
        {errorMessage && (
          <p className="mt-1.5 text-sm text-error-600">{errorMessage}</p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

// ============================================================================
// MULTI SELECT (Chip-based)
// ============================================================================

export interface MultiSelectProps {
  options: SelectOption[]
  value: string[]
  onChange: (value: string[]) => void
  label?: string
  placeholder?: string
  error?: boolean
  errorMessage?: string
  className?: string
}

export function MultiSelect({
  options,
  value,
  onChange,
  label,
  placeholder = 'Select options',
  errorMessage,
  className,
}: MultiSelectProps) {
  const toggleOption = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue))
    } else {
      onChange([...value, optionValue])
    }
  }

  return (
    <div className={clsx('w-full', className)}>
      {label && (
        <label className="block text-sm font-medium text-text-primary mb-2">
          {label}
        </label>
      )}
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const isSelected = value.includes(option.value)
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => !option.disabled && toggleOption(option.value)}
              disabled={option.disabled}
              className={clsx(
                'px-3 py-1.5 rounded-full',
                'text-sm font-medium',
                'transition-all duration-fast',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                option.disabled && 'opacity-50 cursor-not-allowed',
                isSelected
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'bg-neutral-100 text-text-secondary hover:bg-neutral-200'
              )}
            >
              {option.label}
            </button>
          )
        })}
      </div>
      {value.length === 0 && placeholder && (
        <p className="mt-2 text-sm text-text-tertiary">{placeholder}</p>
      )}
      {errorMessage && (
        <p className="mt-1.5 text-sm text-error-600">{errorMessage}</p>
      )}
    </div>
  )
}

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

function ChevronIcon({ isOpen }: { isOpen: boolean }) {
  return (
    <svg
      className={clsx(
        'w-5 h-5 text-text-tertiary transition-transform duration-fast',
        isOpen && 'rotate-180'
      )}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  )
}

export default Select

