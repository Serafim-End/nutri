import { useState, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientApi, publicApi } from '../lib/api'
import FilterDrawer from '../components/FilterDrawer'
import type { SearchFilters, NutritionistSearchResult } from '../types'
import {
  PageContainer,
  Header,
  Section,
  Stack,
  Inline,
  Badge,
  Heading,
  Text,
  SkeletonCard,
  NoResultsState,
  Icons,
} from '../design-system'
import { PageLoader } from '../design-system/components/Loader'
import clsx from 'clsx'

// Default empty filters
const EMPTY_FILTERS: SearchFilters = {
  goals: [],
  topics: [],
  budget_max_rub: null,
  dietary: [],
  help_mode: null,
  specializations: [],
  tags: [],
}

// Label mappings for display
const GOAL_LABELS: Record<string, string> = {
  weight_loss: 'Weight Loss',
  muscle_gain: 'Muscle Gain',
  better_nutrition: 'Better Nutrition',
  gut_health: 'Gut Health',
  sports_nutrition: 'Sports Nutrition',
  diabetes: 'Diabetes',
  mental_wellness: 'Mental Wellness',
  pregnancy: 'Pregnancy',
}

const HELP_MODE_LABELS: Record<string, string> = {
  one_time: 'One-time',
  plan: 'Meal Plan',
  long_term: 'Long-term',
}

// Filter chip component
function FilterChip({ children, variant = 'primary' }: { children: React.ReactNode; variant?: 'primary' | 'warning' | 'info' | 'default' }) {
  const variants = {
    primary: 'bg-primary-100 text-primary-700',
    warning: 'bg-warning-100 text-warning-700',
    info: 'bg-info-100 text-info-700',
    default: 'bg-neutral-100 text-neutral-600',
  }
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium', variants[variant])}>
      {children}
    </span>
  )
}

// Bottom navigation
function BottomNav({ activeTab }: { activeTab: 'browse' | 'bookings' }) {
  const navigate = useNavigate()
  
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-surface-primary border-t border-border-light safe-area-bottom z-fixed">
      <div className="flex">
        <button
          onClick={() => navigate('/results')}
          className={clsx(
            'flex-1 py-4 flex flex-col items-center gap-1 transition-colors',
            activeTab === 'browse' ? 'text-primary-600' : 'text-text-tertiary'
          )}
        >
          <Icons.Search size="lg" />
          <span className={clsx('text-xs', activeTab === 'browse' && 'font-medium')}>Browse</span>
        </button>
        <button
          onClick={() => navigate('/my-bookings')}
          className={clsx(
            'flex-1 py-4 flex flex-col items-center gap-1 transition-colors',
            activeTab === 'bookings' ? 'text-primary-600' : 'text-text-tertiary'
          )}
        >
          <Icons.Calendar size="lg" />
          <span className={clsx('text-xs', activeTab === 'bookings' && 'font-medium')}>My Bookings</span>
        </button>
      </div>
    </div>
  )
}

export default function ResultsPage() {
  const queryClient = useQueryClient()
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [currentFilters, setCurrentFilters] = useState<SearchFilters | null>(null)
  const [defaultFilters, setDefaultFilters] = useState<SearchFilters>(EMPTY_FILTERS)

  // Fetch client's saved filters
  const {
    isLoading: isLoadingFilters,
  } = useQuery({
    queryKey: ['clientFilters'],
    queryFn: async () => {
      const data = await clientApi.getFilters()
      if (!currentFilters) {
        setCurrentFilters(data.filters)
      }
      setDefaultFilters(data.defaults)
      return data
    },
    staleTime: 30000,
  })

  // Search nutritionists with current filters
  const {
    data: searchData,
    isLoading: isSearching,
    error: searchError,
    refetch: refetchSearch,
  } = useQuery({
    queryKey: ['nutritionistSearch', currentFilters],
    queryFn: async () => {
      const filters = currentFilters || EMPTY_FILTERS
      return publicApi.searchNutritionists(filters)
    },
    enabled: currentFilters !== null,
  })

  // Mutation to save filters
  const saveFiltersMutation = useMutation({
    mutationFn: (filters: SearchFilters) => clientApi.updateFilters(filters),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientFilters'] })
    },
  })

  // Handle applying filters
  const handleApplyFilters = useCallback(
    (filters: SearchFilters) => {
      setCurrentFilters(filters)
      saveFiltersMutation.mutate(filters)
    },
    [saveFiltersMutation]
  )

  // Handle reset to defaults
  const handleResetFilters = useCallback(() => {
    setCurrentFilters(defaultFilters)
    saveFiltersMutation.mutate(defaultFilters)
  }, [defaultFilters, saveFiltersMutation])

  // Count active filters
  const countActiveFilters = (filters: SearchFilters): number => {
    let count = 0
    if (filters.goals.length > 0) count += filters.goals.length
    if (filters.topics.length > 0) count += filters.topics.length
    if (filters.dietary.length > 0) count += filters.dietary.length
    if (filters.budget_max_rub !== null) count += 1
    if (filters.help_mode !== null) count += 1
    return count
  }

  const activeFilterCount = currentFilters ? countActiveFilters(currentFilters) : 0

  // Loading state
  if (isLoadingFilters) {
    return <PageLoader text="Loading your preferences..." />
  }

  const nutritionists = searchData?.nutritionists || []

  return (
    <PageContainer background="gradient" withBottomNav>
      {/* Header */}
      <Header sticky bordered blurred>
        <Inline justify="between" align="start">
          <div>
            <Heading level="h1" size="lg">Find Your Nutritionist</Heading>
            <Text size="sm" color="secondary" className="mt-0.5">
              {isSearching
                ? 'Searching...'
                : `${nutritionists.length} specialist${nutritionists.length !== 1 ? 's' : ''} found`}
            </Text>
          </div>
          <button
            onClick={() => setIsDrawerOpen(true)}
            className={clsx(
              'relative flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all',
              activeFilterCount > 0
                ? 'bg-primary-500 text-white shadow-sm'
                : 'bg-neutral-100 text-text-secondary hover:bg-neutral-200'
            )}
          >
            <Icons.Filter size="md" />
            <span className="text-sm">Filters</span>
            {activeFilterCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-surface-primary text-primary-600 text-xs font-bold rounded-full flex items-center justify-center shadow">
                {activeFilterCount}
              </span>
            )}
          </button>
        </Inline>

        {/* Active filter chips */}
        {currentFilters && activeFilterCount > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5 overflow-x-auto pb-1">
            {currentFilters.goals.slice(0, 3).map((goal) => (
              <FilterChip key={goal} variant="primary">
                {GOAL_LABELS[goal] || goal}
              </FilterChip>
            ))}
            {currentFilters.goals.length > 3 && (
              <FilterChip variant="default">+{currentFilters.goals.length - 3} more</FilterChip>
            )}
            {currentFilters.budget_max_rub && (
              <FilterChip variant="warning">
                Up to {currentFilters.budget_max_rub.toLocaleString()} ₽
              </FilterChip>
            )}
            {currentFilters.help_mode && (
              <FilterChip variant="info">
                {HELP_MODE_LABELS[currentFilters.help_mode] || currentFilters.help_mode}
              </FilterChip>
            )}
            {currentFilters.dietary.length > 0 && (
              <FilterChip variant="primary">
                {currentFilters.dietary.length} dietary
              </FilterChip>
            )}
          </div>
        )}
      </Header>

      {/* Results list */}
      <Section spacing="sm">
        {searchError ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚠️</div>
            <Text weight="medium" color="error">Failed to load results</Text>
            <button
              onClick={() => refetchSearch()}
              className="mt-4 text-primary-600 font-medium hover:underline"
            >
              Try again
            </button>
          </div>
        ) : isSearching ? (
          <Stack gap={3}>
            {[1, 2, 3].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </Stack>
        ) : nutritionists.length === 0 ? (
          <NoResultsState onAction={() => setIsDrawerOpen(true)} />
        ) : (
          <Stack gap={3}>
            {nutritionists.map((nutritionist, index) => (
              <NutritionistResultCard
                key={nutritionist.nutritionist_id}
                nutritionist={nutritionist}
                animationDelay={index * 50}
              />
            ))}
          </Stack>
        )}
      </Section>

      {/* Bottom navigation */}
      <BottomNav activeTab="browse" />

      {/* Filter drawer */}
      <FilterDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        filters={currentFilters || EMPTY_FILTERS}
        defaults={defaultFilters}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
      />
    </PageContainer>
  )
}

// Extended nutritionist card with matched reasons
interface NutritionistResultCardProps {
  nutritionist: NutritionistSearchResult
  animationDelay?: number
}

function NutritionistResultCard({
  nutritionist,
  animationDelay = 0,
}: NutritionistResultCardProps) {
  const profile = nutritionist.profile
  const matchedReasons = nutritionist.matched_reasons || []

  return (
    <Link
      to={`/nutritionist/${nutritionist.nutritionist_id}`}
      className={clsx(
        'block rounded-2xl bg-surface-primary border border-border-light p-4',
        'shadow-xs hover:shadow-md transition-all duration-fast',
        'animate-slide-up opacity-0'
      )}
      style={{ animationDelay: `${animationDelay}ms`, animationFillMode: 'forwards' }}
    >
      <Inline gap={4} align="start">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {profile?.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.full_name}
              className="w-16 h-16 rounded-2xl object-cover bg-neutral-100"
            />
          ) : (
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
              <span className="text-white text-xl font-bold">
                {profile?.full_name?.charAt(0) || 'N'}
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <Inline justify="between" gap={2}>
            <Text weight="semibold" truncate>
              {profile?.full_name || 'Nutritionist'}
            </Text>
            <Inline gap={2} className="flex-shrink-0">
              {nutritionist.score > 0 && (
                <Badge variant="primary" size="sm">
                  {nutritionist.score.toFixed(0)}% match
                </Badge>
              )}
              <Inline gap={1}>
                <Icons.Star size="sm" className="text-accent-amber" />
                <Text size="sm" weight="medium">{nutritionist.rating.toFixed(1)}</Text>
              </Inline>
            </Inline>
          </Inline>

          <Text size="sm" color="secondary" lineClamp={2} className="mt-1">
            {nutritionist.bio || 'Professional nutritionist ready to help you.'}
          </Text>

          {/* Matched reasons */}
          {matchedReasons.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {matchedReasons.slice(0, 3).map((reason, idx) => (
                <Badge key={idx} variant="success" size="sm">
                  ✓ {reason}
                </Badge>
              ))}
            </div>
          )}

          {/* Specializations fallback */}
          {matchedReasons.length === 0 && nutritionist.specializations?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {nutritionist.specializations.slice(0, 3).map((spec) => (
                <Badge key={spec} variant="primary" size="sm">
                  {spec.replace(/_/g, ' ')}
                </Badge>
              ))}
              {nutritionist.specializations.length > 3 && (
                <Text size="xs" color="tertiary">
                  +{nutritionist.specializations.length - 3}
                </Text>
              )}
            </div>
          )}
        </div>
      </Inline>
    </Link>
  )
}
