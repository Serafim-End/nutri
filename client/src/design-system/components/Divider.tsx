import clsx from 'clsx'

export interface DividerProps {
  orientation?: 'horizontal' | 'vertical'
  className?: string
  label?: string
}

export function Divider({
  orientation = 'horizontal',
  className,
  label,
}: DividerProps) {
  if (label) {
    return (
      <div className={clsx('flex items-center gap-4', className)}>
        <div className="flex-1 h-px bg-border-light" />
        <span className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
          {label}
        </span>
        <div className="flex-1 h-px bg-border-light" />
      </div>
    )
  }

  if (orientation === 'vertical') {
    return <div className={clsx('w-px h-full bg-border-light', className)} />
  }

  return <div className={clsx('h-px w-full bg-border-light', className)} />
}

export default Divider


