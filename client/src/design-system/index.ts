/**
 * NutriMatch Design System
 * 
 * A cohesive design system for building consistent, accessible, and beautiful
 * health-tech interfaces. Inspired by modern wellness apps with Apple Health–level clarity.
 * 
 * @example
 * import { Button, Card, Text, Stack, colors } from '@/design-system'
 */

// ============================================================================
// TOKENS
// ============================================================================

export {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  animation,
  zIndex,
  breakpoints,
  components,
  generateCSSVariables,
} from './tokens'

export type {
  Colors,
  Typography,
  Spacing,
  BorderRadius,
  Shadows,
  Animation,
} from './tokens'

// ============================================================================
// COMPONENTS
// ============================================================================

// Button
export { Button } from './components/Button'
export type { ButtonProps, ButtonVariant, ButtonSize } from './components/Button'

// Card
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from './components/Card'
export type { CardProps, CardVariant, CardPadding } from './components/Card'

// Badge
export { Badge, StatusBadge } from './components/Badge'
export type { BadgeProps, BadgeVariant, BadgeSize, StatusBadgeStatus, StatusBadgeProps } from './components/Badge'

// Text & Typography
export {
  Text,
  Heading,
  Title,
  Subtitle,
  Body,
  Caption,
  Label,
} from './components/Text'
export type {
  TextProps,
  TextSize,
  TextWeight,
  TextColor,
  HeadingProps,
  HeadingLevel,
} from './components/Text'

// Input
export { Input, Textarea } from './components/Input'
export type { InputProps, InputSize, TextareaProps } from './components/Input'

// Select
export { Select, MultiSelect } from './components/Select'
export type { SelectProps, SelectOption, MultiSelectProps } from './components/Select'

// Modal & BottomSheet
export { BottomSheet, Modal } from './components/BottomSheet'
export type { BottomSheetProps, ModalProps } from './components/BottomSheet'

// Divider
export { Divider } from './components/Divider'
export type { DividerProps } from './components/Divider'

// Loader
export {
  Spinner,
  Skeleton,
  SkeletonCard,
  LoadingOverlay,
  PageLoader,
} from './components/Loader'
export type { SpinnerProps, SkeletonProps, LoadingOverlayProps, PageLoaderProps } from './components/Loader'

// EmptyState
export {
  EmptyState,
  NoResultsState,
  NoBookingsState,
  NoSlotsState,
  ErrorState,
  NotFoundState,
} from './components/EmptyState'
export type { EmptyStateProps } from './components/EmptyState'

// Toast & Alert
export { Alert, ToastProvider, useToast } from './components/Toast'
export type { AlertProps, AlertVariant, ToastData } from './components/Toast'

// Layout
export {
  PageContainer,
  Section,
  Stack,
  Inline,
  Grid,
  Center,
  Header,
  Footer,
} from './components/Layout'
export type {
  PageContainerProps,
  SectionProps,
  StackProps,
  InlineProps,
  GridProps,
  CenterProps,
  HeaderProps,
  FooterProps,
} from './components/Layout'

// Icons
export { Icons } from './components/Icon'
export type { IconProps, IconSize } from './components/Icon'


