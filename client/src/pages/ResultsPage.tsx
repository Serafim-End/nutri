import { useState, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientApi, publicApi } from '../lib/api'
import FilterDrawer from '../components/FilterDrawer'
import LoadingScreen from '../components/LoadingScreen'
import type { SearchFilters, NutritionistSearchResult } from '../types'
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

export default function ResultsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [currentFilters, setCurrentFilters] = useState<SearchFilters | null>(null)
  const [defaultFilters, setDefaultFilters] = useState<SearchFilters>(EMPTY_FILTERS)

  // Fetch client's saved filters
  const {
    data: filtersData,
    isLoading: isLoadingFilters,
  } = useQuery({
    queryKey: ['clientFilters'],
    queryFn: async () => {
      const data = await clientApi.getFilters()
      // Set initial filters from response
      if (!currentFilters) {
        setCurrentFilters(data.filters)
      }
      setDefaultFilters(data.defaults)
      return data
    },
    staleTime: 30000, // 30 seconds
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
    return <LoadingScreen />
  }

  const nutritionists = searchData?.nutritionists || []

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50/50 to-white pb-20">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-display font-bold text-gray-900">
                Find Your Nutritionist
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                {isSearching
                  ? 'Searching...'
                  : `${nutritionists.length} specialist${nutritionists.length !== 1 ? 's' : ''} found`}
              </p>
            </div>
            <button
              onClick={() => setIsDrawerOpen(true)}
              className={clsx(
                'relative flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all',
                activeFilterCount > 0
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
              </svg>
              <span className="text-sm">Filters</span>
              {activeFilterCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-white text-primary-600 text-xs font-bold rounded-full flex items-center justify-center shadow">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </div>

          {/* Active filter chips */}
          {currentFilters && activeFilterCount > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5 overflow-x-auto pb-1">
              {currentFilters.goals.slice(0, 3).map((goal) => (
                <span
                  key={goal}
                  className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700"
                >
                  {GOAL_LABELS[goal] || goal}
                </span>
              ))}
              {currentFilters.goals.length > 3 && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                  +{currentFilters.goals.length - 3} more
                </span>
              )}
              {currentFilters.budget_max_rub && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                  Up to {currentFilters.budget_max_rub.toLocaleString()} ₽
                </span>
              )}
              {currentFilters.help_mode && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                  {HELP_MODE_LABELS[currentFilters.help_mode] || currentFilters.help_mode}
                </span>
              )}
              {currentFilters.dietary.length > 0 && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                  {currentFilters.dietary.length} dietary
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Results list */}
      <div className="px-4 py-4">
        {searchError ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚠️</div>
            <p className="text-red-500 font-medium">Failed to load results</p>
            <button
              onClick={() => refetchSearch()}
              className="mt-4 text-primary-600 font-medium hover:underline"
            >
              Try again
            </button>
          </div>
        ) : isSearching ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="flex gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-gray-200" />
                  <div className="flex-1 space-y-2">
                    <div className="h-5 bg-gray-200 rounded w-2/3" />
                    <div className="h-4 bg-gray-200 rounded w-full" />
                    <div className="h-4 bg-gray-200 rounded w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : nutritionists.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">🔍</div>
            <p className="text-gray-700 font-medium">No specialists found</p>
            <p className="text-gray-500 text-sm mt-2">
              Try adjusting your filters to see more results.
            </p>
            <button
              onClick={() => setIsDrawerOpen(true)}
              className="mt-4 btn-secondary"
            >
              Adjust Filters
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {nutritionists.map((nutritionist, index) => (
              <NutritionistResultCard
                key={nutritionist.nutritionist_id}
                nutritionist={nutritionist}
                animationDelay={index * 50}
              />
            ))}
          </div>
        )}
      </div>

      {/* Bottom navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 safe-area-bottom">
        <div className="flex">
          <button className="flex-1 py-4 flex flex-col items-center gap-1 text-primary-600">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <span className="text-xs font-medium">Browse</span>
          </button>
          <button
            onClick={() => navigate('/my-bookings')}
            className="flex-1 py-4 flex flex-col items-center gap-1 text-gray-500"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span className="text-xs">My Bookings</span>
          </button>
        </div>
      </div>

      {/* Filter drawer */}
      <FilterDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        filters={currentFilters || EMPTY_FILTERS}
        defaults={defaultFilters}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
      />
    </div>
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
        'card block hover:shadow-md transition-all duration-200',
        'animate-slide-up opacity-0'
      )}
      style={{ animationDelay: `${animationDelay}ms`, animationFillMode: 'forwards' }}
    >
      <div className="flex gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {profile?.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.full_name}
              className="w-16 h-16 rounded-2xl object-cover bg-gray-100"
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
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-gray-900 truncate">
              {profile?.full_name || 'Nutritionist'}
            </h3>
            {/* Rating & Score */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {nutritionist.score > 0 && (
                <span className="text-xs font-medium text-primary-600 bg-primary-50 px-1.5 py-0.5 rounded">
                  {nutritionist.score.toFixed(0)}% match
                </span>
              )}
              <div className="flex items-center gap-1">
                <svg
                  className="w-4 h-4 text-amber-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span className="text-sm font-medium text-gray-700">
                  {nutritionist.rating.toFixed(1)}
                </span>
              </div>
            </div>
          </div>

          {/* Bio */}
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">
            {nutritionist.bio || 'Professional nutritionist ready to help you.'}
          </p>

          {/* Matched reasons */}
          {matchedReasons.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {matchedReasons.slice(0, 3).map((reason, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700"
                >
                  ✓ {reason}
                </span>
              ))}
            </div>
          )}

          {/* Specializations fallback */}
          {matchedReasons.length === 0 && nutritionist.specializations?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {nutritionist.specializations.slice(0, 3).map((spec) => (
                <span
                  key={spec}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700"
                >
                  {spec.replace(/_/g, ' ')}
                </span>
              ))}
              {nutritionist.specializations.length > 3 && (
                <span className="text-xs text-gray-400">
                  +{nutritionist.specializations.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}
