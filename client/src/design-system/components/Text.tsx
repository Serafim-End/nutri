import { forwardRef } from 'react'
import clsx from 'clsx'

// ============================================================================
// TEXT BASE
// ============================================================================

export type TextSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type TextWeight = 'normal' | 'medium' | 'semibold' | 'bold'
export type TextColor = 'primary' | 'secondary' | 'tertiary' | 'inherit' | 'success' | 'warning' | 'error'

export interface TextProps extends React.HTMLAttributes<HTMLElement> {
  size?: TextSize
  weight?: TextWeight
  color?: TextColor
  as?: 'p' | 'span' | 'div' | 'label'
  truncate?: boolean
  lineClamp?: 1 | 2 | 3
}

const sizeStyles: Record<TextSize, string> = {
  xs: 'text-xs',
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl',
}

const weightStyles: Record<TextWeight, string> = {
  normal: 'font-normal',
  medium: 'font-medium',
  semibold: 'font-semibold',
  bold: 'font-bold',
}

const colorStyles: Record<TextColor, string> = {
  primary: 'text-text-primary',
  secondary: 'text-text-secondary',
  tertiary: 'text-text-tertiary',
  inherit: 'text-inherit',
  success: 'text-success-600',
  warning: 'text-warning-600',
  error: 'text-error-600',
}

export const Text = forwardRef<HTMLElement, TextProps>(
  (
    {
      size = 'md',
      weight = 'normal',
      color = 'primary',
      as: Component = 'p',
      truncate = false,
      lineClamp,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <Component
        // @ts-expect-error - ref type mismatch is expected due to polymorphic component
        ref={ref}
        className={clsx(
          sizeStyles[size],
          weightStyles[weight],
          colorStyles[color],
          truncate && 'truncate',
          lineClamp === 1 && 'line-clamp-1',
          lineClamp === 2 && 'line-clamp-2',
          lineClamp === 3 && 'line-clamp-3',
          className
        )}
        {...props}
      />
    )
  }
)

Text.displayName = 'Text'

// ============================================================================
// HEADING COMPONENTS
// ============================================================================

export type HeadingLevel = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'

export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: HeadingLevel
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl'
}

const headingSizes: Record<NonNullable<HeadingProps['size']>, string> = {
  sm: 'text-base',
  md: 'text-lg',
  lg: 'text-xl',
  xl: 'text-2xl',
  '2xl': 'text-3xl',
  '3xl': 'text-4xl',
}

export const Heading = forwardRef<HTMLHeadingElement, HeadingProps>(
  ({ level = 'h2', size = 'lg', className, ...props }, ref) => {
    const Component = level
    return (
      <Component
        ref={ref}
        className={clsx(
          headingSizes[size],
          'font-semibold text-text-primary tracking-tight',
          className
        )}
        {...props}
      />
    )
  }
)

Heading.displayName = 'Heading'

// ============================================================================
// PRESET COMPONENTS
// ============================================================================

// Page title (large, prominent)
export const Title = forwardRef<HTMLHeadingElement, Omit<HeadingProps, 'level' | 'size'>>(
  ({ className, ...props }, ref) => (
    <Heading
      ref={ref}
      level="h1"
      size="xl"
      className={clsx('', className)}
      {...props}
    />
  )
)
Title.displayName = 'Title'

// Section subtitle
export const Subtitle = forwardRef<HTMLHeadingElement, Omit<HeadingProps, 'level' | 'size'>>(
  ({ className, ...props }, ref) => (
    <Heading
      ref={ref}
      level="h2"
      size="md"
      className={clsx('', className)}
      {...props}
    />
  )
)
Subtitle.displayName = 'Subtitle'

// Body text
export const Body = forwardRef<HTMLElement, Omit<TextProps, 'size'>>(
  ({ className, ...props }, ref) => (
    <Text
      ref={ref}
      size="md"
      className={clsx('leading-relaxed', className)}
      {...props}
    />
  )
)
Body.displayName = 'Body'

// Small caption text
export const Caption = forwardRef<HTMLElement, Omit<TextProps, 'size' | 'color'>>(
  ({ className, ...props }, ref) => (
    <Text
      ref={ref}
      size="xs"
      color="tertiary"
      className={clsx('', className)}
      {...props}
    />
  )
)
Caption.displayName = 'Caption'

// Label for form elements
export const Label = forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={clsx(
        'text-sm font-medium text-text-primary',
        className
      )}
      {...props}
    />
  )
)
Label.displayName = 'Label'

export default Text


