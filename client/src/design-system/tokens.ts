/**
 * NutriMatch Design System Tokens
 * 
 * A modern, calm, premium health-tech design language.
 * Inspired by contemporary nutrition/wellness apps with Apple Health–level clarity.
 */

// ============================================================================
// COLORS
// ============================================================================

export const colors = {
  // Backgrounds
  background: {
    primary: '#FAFBFC',      // Main app background - warm off-white
    secondary: '#F5F7F9',    // Secondary surfaces
    tertiary: '#EBEEF2',     // Subtle contrast areas
  },

  // Surfaces (cards, modals, elevated elements)
  surface: {
    primary: '#FFFFFF',      // Card backgrounds
    secondary: '#F8FAFB',    // Nested surfaces
    elevated: '#FFFFFF',     // Modal backgrounds
    overlay: 'rgba(15, 23, 42, 0.4)', // Backdrop overlay
  },

  // Primary accent - Fresh sage green (calm, wellness-focused)
  primary: {
    50: '#F0F9F4',
    100: '#DCF2E6',
    200: '#BBE5CF',
    300: '#8DD4B0',
    400: '#5CBC8A',
    500: '#3AA76D',          // Main primary
    600: '#2D8A58',
    700: '#276E49',
    800: '#24583D',
    900: '#204934',
    950: '#0F2A1D',
  },

  // Primary muted - for subtle highlights
  primaryMuted: {
    light: 'rgba(58, 167, 109, 0.08)',
    medium: 'rgba(58, 167, 109, 0.12)',
    strong: 'rgba(58, 167, 109, 0.18)',
  },

  // Text
  text: {
    primary: '#1A1F2E',      // Main text - warm dark
    secondary: '#5E6678',    // Secondary/muted text
    tertiary: '#8B93A7',     // Hints, captions
    inverse: '#FFFFFF',      // Text on dark backgrounds
    link: '#3AA76D',         // Interactive text
  },

  // Border colors
  border: {
    light: '#E8ECF0',        // Subtle borders
    default: '#DDE2E8',      // Default borders
    strong: '#C5CCD6',       // Emphasized borders
    focus: '#3AA76D',        // Focus state
  },

  // Semantic colors
  success: {
    50: '#F0FDF4',
    100: '#DCFCE7',
    500: '#22C55E',
    600: '#16A34A',
    700: '#15803D',
  },

  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    500: '#F59E0B',
    600: '#D97706',
    700: '#B45309',
  },

  error: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    500: '#EF4444',
    600: '#DC2626',
    700: '#B91C1C',
  },

  info: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    500: '#3B82F6',
    600: '#2563EB',
    700: '#1D4ED8',
  },

  // Neutral grays
  neutral: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A',
  },
} as const

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  // Font families
  fontFamily: {
    sans: "'Plus Jakarta Sans', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    display: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', monospace",
  },

  // Font sizes with line heights
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],      // 12px
    sm: ['0.875rem', { lineHeight: '1.25rem' }],  // 14px
    md: ['1rem', { lineHeight: '1.5rem' }],       // 16px
    lg: ['1.125rem', { lineHeight: '1.75rem' }],  // 18px
    xl: ['1.25rem', { lineHeight: '1.75rem' }],   // 20px
    '2xl': ['1.5rem', { lineHeight: '2rem' }],    // 24px
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
    '4xl': ['2.25rem', { lineHeight: '2.5rem' }], // 36px
  },

  // Font weights
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },

  // Letter spacing
  letterSpacing: {
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
  },
} as const

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  0: '0',
  0.5: '0.125rem',  // 2px
  1: '0.25rem',     // 4px
  1.5: '0.375rem',  // 6px
  2: '0.5rem',      // 8px
  2.5: '0.625rem',  // 10px
  3: '0.75rem',     // 12px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  8: '2rem',        // 32px
  10: '2.5rem',     // 40px
  12: '3rem',       // 48px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
} as const

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  none: '0',
  sm: '0.375rem',     // 6px - subtle rounding
  md: '0.5rem',       // 8px - default
  lg: '0.75rem',      // 12px - cards, buttons
  xl: '1rem',         // 16px - larger cards
  '2xl': '1.25rem',   // 20px - prominent elements
  '3xl': '1.5rem',    // 24px - modals, bottom sheets
  full: '9999px',     // Pills, circular elements
} as const

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  none: 'none',
  xs: '0 1px 2px rgba(0, 0, 0, 0.04)',
  sm: '0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -1px rgba(0, 0, 0, 0.04)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.06), 0 4px 6px -2px rgba(0, 0, 0, 0.03)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 10px 10px -5px rgba(0, 0, 0, 0.02)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.15)',
  // Colored shadows for emphasis
  primary: '0 4px 14px rgba(58, 167, 109, 0.25)',
  primaryLg: '0 8px 24px rgba(58, 167, 109, 0.3)',
} as const

// ============================================================================
// TRANSITIONS / ANIMATION
// ============================================================================

export const animation = {
  // Durations
  duration: {
    instant: '0ms',
    fast: '150ms',
    normal: '200ms',
    slow: '300ms',
    slower: '400ms',
  },

  // Easing functions
  easing: {
    linear: 'linear',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
} as const

// ============================================================================
// Z-INDEX SCALE
// ============================================================================

export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  fixed: 30,
  modalBackdrop: 40,
  modal: 50,
  popover: 60,
  tooltip: 70,
  toast: 80,
} as const

// ============================================================================
// BREAKPOINTS
// ============================================================================

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
} as const

// ============================================================================
// COMPONENT-SPECIFIC TOKENS
// ============================================================================

export const components = {
  // Button specific
  button: {
    height: {
      sm: '2rem',      // 32px
      md: '2.5rem',    // 40px
      lg: '3rem',      // 48px
    },
    padding: {
      sm: '0.5rem 1rem',
      md: '0.625rem 1.25rem',
      lg: '0.75rem 1.5rem',
    },
  },

  // Input specific
  input: {
    height: {
      sm: '2.25rem',   // 36px
      md: '2.75rem',   // 44px
      lg: '3.25rem',   // 52px
    },
  },

  // Card specific
  card: {
    padding: {
      sm: '0.75rem',   // 12px
      md: '1rem',      // 16px
      lg: '1.5rem',    // 24px
    },
  },

  // Bottom navigation
  bottomNav: {
    height: '4rem',    // 64px (excluding safe area)
  },
} as const

// ============================================================================
// CSS VARIABLE GENERATOR
// ============================================================================

export function generateCSSVariables(): string {
  return `
    :root {
      /* Background colors */
      --color-bg-primary: ${colors.background.primary};
      --color-bg-secondary: ${colors.background.secondary};
      --color-bg-tertiary: ${colors.background.tertiary};

      /* Surface colors */
      --color-surface-primary: ${colors.surface.primary};
      --color-surface-secondary: ${colors.surface.secondary};
      --color-surface-elevated: ${colors.surface.elevated};
      --color-surface-overlay: ${colors.surface.overlay};

      /* Primary colors */
      --color-primary-50: ${colors.primary[50]};
      --color-primary-100: ${colors.primary[100]};
      --color-primary-200: ${colors.primary[200]};
      --color-primary-300: ${colors.primary[300]};
      --color-primary-400: ${colors.primary[400]};
      --color-primary-500: ${colors.primary[500]};
      --color-primary-600: ${colors.primary[600]};
      --color-primary-700: ${colors.primary[700]};
      --color-primary-800: ${colors.primary[800]};
      --color-primary-900: ${colors.primary[900]};

      /* Primary muted */
      --color-primary-muted-light: ${colors.primaryMuted.light};
      --color-primary-muted-medium: ${colors.primaryMuted.medium};
      --color-primary-muted-strong: ${colors.primaryMuted.strong};

      /* Text colors */
      --color-text-primary: ${colors.text.primary};
      --color-text-secondary: ${colors.text.secondary};
      --color-text-tertiary: ${colors.text.tertiary};
      --color-text-inverse: ${colors.text.inverse};
      --color-text-link: ${colors.text.link};

      /* Border colors */
      --color-border-light: ${colors.border.light};
      --color-border-default: ${colors.border.default};
      --color-border-strong: ${colors.border.strong};
      --color-border-focus: ${colors.border.focus};

      /* Semantic colors */
      --color-success-50: ${colors.success[50]};
      --color-success-500: ${colors.success[500]};
      --color-success-600: ${colors.success[600]};
      --color-warning-50: ${colors.warning[50]};
      --color-warning-500: ${colors.warning[500]};
      --color-warning-600: ${colors.warning[600]};
      --color-error-50: ${colors.error[50]};
      --color-error-500: ${colors.error[500]};
      --color-error-600: ${colors.error[600]};

      /* Typography */
      --font-family-sans: ${typography.fontFamily.sans};
      --font-family-display: ${typography.fontFamily.display};

      /* Shadows */
      --shadow-xs: ${shadows.xs};
      --shadow-sm: ${shadows.sm};
      --shadow-md: ${shadows.md};
      --shadow-lg: ${shadows.lg};
      --shadow-xl: ${shadows.xl};
      --shadow-primary: ${shadows.primary};

      /* Border radius */
      --radius-sm: ${borderRadius.sm};
      --radius-md: ${borderRadius.md};
      --radius-lg: ${borderRadius.lg};
      --radius-xl: ${borderRadius.xl};
      --radius-2xl: ${borderRadius['2xl']};
      --radius-3xl: ${borderRadius['3xl']};
      --radius-full: ${borderRadius.full};

      /* Animation */
      --duration-fast: ${animation.duration.fast};
      --duration-normal: ${animation.duration.normal};
      --duration-slow: ${animation.duration.slow};
      --easing-default: ${animation.easing.easeOut};
    }
  `
}

// ============================================================================
// TYPE EXPORTS
// ============================================================================

export type Colors = typeof colors
export type Typography = typeof typography
export type Spacing = typeof spacing
export type BorderRadius = typeof borderRadius
export type Shadows = typeof shadows
export type Animation = typeof animation


