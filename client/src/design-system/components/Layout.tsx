import { forwardRef } from 'react'
import clsx from 'clsx'

// ============================================================================
// PAGE CONTAINER
// ============================================================================

export interface PageContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Background style */
  background?: 'primary' | 'secondary' | 'gradient'
  /** Add padding for bottom navigation */
  withBottomNav?: boolean
  /** Add safe area insets */
  safeArea?: boolean
}

export const PageContainer = forwardRef<HTMLDivElement, PageContainerProps>(
  (
    {
      background = 'primary',
      withBottomNav = false,
      safeArea = true,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const bgStyles = {
      primary: 'bg-bg-primary',
      secondary: 'bg-bg-secondary',
      gradient: 'bg-gradient-to-b from-primary-50/50 to-bg-primary',
    }

    return (
      <div
        ref={ref}
        className={clsx(
          'min-h-screen',
          bgStyles[background],
          withBottomNav && 'pb-20',
          safeArea && 'safe-area-bottom',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

PageContainer.displayName = 'PageContainer'

// ============================================================================
// SECTION
// ============================================================================

export interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  /** Horizontal padding */
  padded?: boolean
  /** Spacing variant */
  spacing?: 'none' | 'sm' | 'md' | 'lg'
}

const sectionSpacing = {
  none: '',
  sm: 'py-4',
  md: 'py-6',
  lg: 'py-8',
}

export const Section = forwardRef<HTMLElement, SectionProps>(
  ({ padded = true, spacing = 'md', className, children, ...props }, ref) => {
    return (
      <section
        ref={ref}
        className={clsx(
          padded && 'px-4',
          sectionSpacing[spacing],
          className
        )}
        {...props}
      >
        {children}
      </section>
    )
  }
)

Section.displayName = 'Section'

// ============================================================================
// STACK (Vertical spacing)
// ============================================================================

export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Gap between children */
  gap?: 0 | 1 | 2 | 3 | 4 | 6 | 8
  /** Alignment */
  align?: 'start' | 'center' | 'end' | 'stretch'
}

const gapStyles: Record<NonNullable<StackProps['gap']>, string> = {
  0: 'gap-0',
  1: 'gap-1',
  2: 'gap-2',
  3: 'gap-3',
  4: 'gap-4',
  6: 'gap-6',
  8: 'gap-8',
}

const alignStyles: Record<NonNullable<StackProps['align']>, string> = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  stretch: 'items-stretch',
}

export const Stack = forwardRef<HTMLDivElement, StackProps>(
  ({ gap = 4, align = 'stretch', className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('flex flex-col', gapStyles[gap], alignStyles[align], className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Stack.displayName = 'Stack'

// ============================================================================
// INLINE (Horizontal layout)
// ============================================================================

export interface InlineProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Gap between children */
  gap?: 0 | 1 | 2 | 3 | 4 | 6 | 8
  /** Vertical alignment */
  align?: 'start' | 'center' | 'end' | 'baseline' | 'stretch'
  /** Horizontal distribution */
  justify?: 'start' | 'center' | 'end' | 'between' | 'around'
  /** Wrap behavior */
  wrap?: boolean
}

const justifyStyles: Record<NonNullable<InlineProps['justify']>, string> = {
  start: 'justify-start',
  center: 'justify-center',
  end: 'justify-end',
  between: 'justify-between',
  around: 'justify-around',
}

const inlineAlignStyles: Record<NonNullable<InlineProps['align']>, string> = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  baseline: 'items-baseline',
  stretch: 'items-stretch',
}

export const Inline = forwardRef<HTMLDivElement, InlineProps>(
  (
    {
      gap = 2,
      align = 'center',
      justify = 'start',
      wrap = false,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'flex',
          gapStyles[gap],
          inlineAlignStyles[align],
          justifyStyles[justify],
          wrap && 'flex-wrap',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Inline.displayName = 'Inline'

// ============================================================================
// GRID
// ============================================================================

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Number of columns */
  cols?: 1 | 2 | 3 | 4
  /** Gap between items */
  gap?: 2 | 3 | 4 | 6
}

const colStyles: Record<NonNullable<GridProps['cols']>, string> = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
}

export const Grid = forwardRef<HTMLDivElement, GridProps>(
  ({ cols = 2, gap = 3, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('grid', colStyles[cols], gapStyles[gap], className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Grid.displayName = 'Grid'

// ============================================================================
// CENTER
// ============================================================================

export interface CenterProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Make it full height */
  fullHeight?: boolean
}

export const Center = forwardRef<HTMLDivElement, CenterProps>(
  ({ fullHeight = false, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'flex items-center justify-center',
          fullHeight && 'min-h-screen',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Center.displayName = 'Center'

// ============================================================================
// HEADER
// ============================================================================

export interface HeaderProps extends React.HTMLAttributes<HTMLElement> {
  /** Sticky positioning */
  sticky?: boolean
  /** Border on bottom */
  bordered?: boolean
  /** Background blur */
  blurred?: boolean
}

export const Header = forwardRef<HTMLElement, HeaderProps>(
  (
    {
      sticky = true,
      bordered = true,
      blurred = true,
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <header
        ref={ref}
        className={clsx(
          'px-4 pt-4 pb-3',
          sticky && 'sticky top-0 z-sticky',
          bordered && 'border-b border-border-light',
          blurred ? 'bg-surface-primary/80 backdrop-blur-md' : 'bg-surface-primary',
          className
        )}
        {...props}
      >
        {children}
      </header>
    )
  }
)

Header.displayName = 'Header'

// ============================================================================
// FOOTER (Fixed bottom action bar)
// ============================================================================

export interface FooterProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Border on top */
  bordered?: boolean
}

export const Footer = forwardRef<HTMLDivElement, FooterProps>(
  ({ bordered = true, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'fixed bottom-0 left-0 right-0 z-fixed',
          'bg-surface-primary p-4',
          bordered && 'border-t border-border-light',
          'safe-area-bottom',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Footer.displayName = 'Footer'

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  PageContainer,
  Section,
  Stack,
  Inline,
  Grid,
  Center,
  Header,
  Footer,
}


