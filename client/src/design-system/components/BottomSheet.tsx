import { useEffect, useRef } from 'react'
import clsx from 'clsx'

export interface BottomSheetProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  showHandle?: boolean
  className?: string
}

export function BottomSheet({
  isOpen,
  onClose,
  title,
  children,
  showHandle = true,
  className,
}: BottomSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null)

  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-modal">
      {/* Backdrop */}
      <div
        className={clsx(
          // Semi-transparent backdrop over the underlying page,
          // while the sheet itself remains fully opaque.
          'absolute inset-0 bg-surface-overlay',
          'animate-fade-in'
        )}
        onClick={onClose}
      />

      {/* Sheet */}
      <div
        ref={sheetRef}
        className={clsx(
          'absolute bottom-0 left-0 right-0',
          // Force solid sheet background
          'bg-white rounded-t-3xl',
          'max-h-[90vh] overflow-hidden flex flex-col',
          'shadow-2xl',
          'animate-slide-up',
          className
        )}
      >
        {/* Handle */}
        {showHandle && (
          <div className="flex justify-center pt-3 pb-1">
            <div className="w-10 h-1 rounded-full bg-neutral-300" />
          </div>
        )}

        {/* Header */}
        {title && (
          <div className="sticky top-0 bg-surface-elevated border-b border-border-light px-4 py-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
            <button
              onClick={onClose}
              className="p-2 -mr-2 text-text-tertiary hover:text-text-primary transition-colors"
            >
              <CloseIcon />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto overscroll-contain">
          {children}
        </div>

        {/* Safe area padding */}
        <div className="safe-area-bottom" />
      </div>
    </div>
  )
}

// ============================================================================
// MODAL (Center-positioned)
// ============================================================================

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  className,
}: ModalProps) {
  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-modal flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className={clsx(
          'absolute inset-0 bg-surface-overlay backdrop-blur-sm',
          'animate-fade-in'
        )}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={clsx(
          'relative w-full',
          'bg-surface-elevated rounded-2xl',
          'shadow-2xl',
          'animate-scale-in',
          sizeStyles[size],
          className
        )}
      >
        {/* Header */}
        {(title || description) && (
          <div className="px-6 pt-6 pb-4">
            {title && (
              <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
            )}
            {description && (
              <p className="mt-1 text-sm text-text-secondary">{description}</p>
            )}
          </div>
        )}

        {/* Content */}
        <div className="px-6 pb-6">{children}</div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-text-tertiary hover:text-text-primary transition-colors"
        >
          <CloseIcon />
        </button>
      </div>
    </div>
  )
}

// ============================================================================
// HELPER ICONS
// ============================================================================

function CloseIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

export default BottomSheet


