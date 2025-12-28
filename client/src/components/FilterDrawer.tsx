import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { publicApi } from '../lib/api'
import type { SearchFilters, FilterOptions } from '../types'
import clsx from 'clsx'

interface FilterDrawerProps {
  isOpen: boolean
  onClose: () => void
  filters: SearchFilters
  defaults: SearchFilters
  onApply: (filters: SearchFilters) => void
  onReset: () => void
}

// Default filter options as fallback
const DEFAULT_OPTIONS: FilterOptions = {
  goals: [
    { id: 'weight_loss', label: 'Weight Loss' },
    { id: 'muscle_gain', label: 'Muscle Gain' },
    { id: 'better_nutrition', label: 'Better Nutrition' },
    { id: 'gut_health', label: 'Gut Health' },
    { id: 'sports_nutrition', label: 'Sports Nutrition' },
    { id: 'diabetes', label: 'Diabetes Management' },
    { id: 'mental_wellness', label: 'Mental Wellness' },
    { id: 'pregnancy', label: 'Pregnancy Nutrition' },
  ],
  topics: [
    { id: 'nutrition_basics', label: 'Nutrition Basics' },
    { id: 'meal_planning', label: 'Meal Planning' },
    { id: 'supplements', label: 'Supplements' },
    { id: 'weight_management', label: 'Weight Management' },
    { id: 'sports_performance', label: 'Sports Performance' },
    { id: 'chronic_conditions', label: 'Chronic Conditions' },
  ],
  dietary: [
    { id: 'vegetarian', label: 'Vegetarian' },
    { id: 'vegan', label: 'Vegan' },
    { id: 'gluten_free', label: 'Gluten Free' },
    { id: 'lactose_free', label: 'Lactose Free' },
    { id: 'halal', label: 'Halal' },
    { id: 'kosher', label: 'Kosher' },
  ],
  help_modes: [
    { id: 'one_time', label: 'One-time Consultation' },
    { id: 'plan', label: 'Meal Plan' },
    { id: 'long_term', label: 'Long-term Support' },
  ],
  budget_ranges: [
    { id: 'up_to_2000', max: 2000, label: 'Up to 2,000 ₽' },
    { id: '2000_3000', max: 3000, label: '2,000 - 3,000 ₽' },
    { id: '3000_5000', max: 5000, label: '3,000 - 5,000 ₽' },
    { id: 'above_5000', max: null, label: '5,000+ ₽' },
    { id: 'unknown', max: null, label: 'Not sure' },
  ],
}

export default function FilterDrawer({
  isOpen,
  onClose,
  filters,
  defaults,
  onApply,
  onReset,
}: FilterDrawerProps) {
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters)

  // Fetch filter options from backend
  const { data: options } = useQuery({
    queryKey: ['filterOptions'],
    queryFn: publicApi.getFilterOptions,
    staleTime: Infinity, // Options don't change often
  })

  const filterOptions = options || DEFAULT_OPTIONS

  // Sync local filters when drawer opens
  useEffect(() => {
    if (isOpen) {
      setLocalFilters(filters)
    }
  }, [isOpen, filters])

  const toggleArrayValue = (key: keyof SearchFilters, value: string) => {
    const arr = (localFilters[key] as string[]) || []
    const updated = arr.includes(value)
      ? arr.filter((v) => v !== value)
      : [...arr, value]
    setLocalFilters({ ...localFilters, [key]: updated })
  }

  const setBudgetMax = (max: number | null) => {
    setLocalFilters({ ...localFilters, budget_max_rub: max })
  }

  const setHelpMode = (mode: string | null) => {
    setLocalFilters({
      ...localFilters,
      help_mode: mode as SearchFilters['help_mode'],
    })
  }

  const handleApply = () => {
    onApply(localFilters)
    onClose()
  }

  const handleReset = () => {
    setLocalFilters(defaults)
    onReset()
    onClose()
  }

  const handleClearAll = () => {
    setLocalFilters({
      goals: [],
      topics: [],
      budget_max_rub: null,
      dietary: [],
      help_mode: null,
      specializations: [],
      tags: [],
    })
  }

  // Find matching budget range ID
  const selectedBudgetId =
    localFilters.budget_max_rub === null
      ? null
      : filterOptions.budget_ranges.find(
          (r) => r.max === localFilters.budget_max_rub
        )?.id || null

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={clsx(
          'absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl',
          'max-h-[85vh] overflow-hidden flex flex-col',
          'animate-slide-up shadow-2xl'
        )}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-4 py-4 flex items-center justify-between">
          <h2 className="text-lg font-display font-bold text-gray-900">
            Filters
          </h2>
          <button
            onClick={onClose}
            className="p-2 -mr-2 text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {/* Goals */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Goals</h3>
            <div className="flex flex-wrap gap-2">
              {filterOptions.goals.map((goal) => (
                <button
                  key={goal.id}
                  onClick={() => toggleArrayValue('goals', goal.id)}
                  className={clsx(
                    'px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                    localFilters.goals.includes(goal.id)
                      ? 'bg-primary-500 text-white shadow-sm'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  {goal.label}
                </button>
              ))}
            </div>
          </section>

          {/* Topics */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Topics</h3>
            <div className="flex flex-wrap gap-2">
              {filterOptions.topics.map((topic) => (
                <button
                  key={topic.id}
                  onClick={() => toggleArrayValue('topics', topic.id)}
                  className={clsx(
                    'px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                    localFilters.topics.includes(topic.id)
                      ? 'bg-primary-500 text-white shadow-sm'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  {topic.label}
                </button>
              ))}
            </div>
          </section>

          {/* Budget */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Budget per Session</h3>
            <div className="space-y-2">
              {filterOptions.budget_ranges.map((range) => (
                <button
                  key={range.id}
                  onClick={() => setBudgetMax(range.max)}
                  className={clsx(
                    'w-full px-4 py-3 rounded-xl text-left transition-all flex items-center justify-between',
                    selectedBudgetId === range.id ||
                      (range.id === 'unknown' && localFilters.budget_max_rub === null)
                      ? 'bg-primary-50 border-2 border-primary-500'
                      : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                  )}
                >
                  <span className="font-medium text-gray-900">{range.label}</span>
                  {(selectedBudgetId === range.id ||
                    (range.id === 'unknown' && localFilters.budget_max_rub === null)) && (
                    <svg className="w-5 h-5 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </section>

          {/* Dietary Restrictions */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Dietary Preferences</h3>
            <div className="flex flex-wrap gap-2">
              {filterOptions.dietary.map((diet) => (
                <button
                  key={diet.id}
                  onClick={() => toggleArrayValue('dietary', diet.id)}
                  className={clsx(
                    'px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                    localFilters.dietary.includes(diet.id)
                      ? 'bg-primary-500 text-white shadow-sm'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  {diet.label}
                </button>
              ))}
            </div>
          </section>

          {/* Help Mode */}
          <section>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Type of Help</h3>
            <div className="space-y-2">
              {filterOptions.help_modes.map((mode) => (
                <button
                  key={mode.id}
                  onClick={() =>
                    setHelpMode(localFilters.help_mode === mode.id ? null : mode.id)
                  }
                  className={clsx(
                    'w-full px-4 py-3 rounded-xl text-left transition-all flex items-center justify-between',
                    localFilters.help_mode === mode.id
                      ? 'bg-primary-50 border-2 border-primary-500'
                      : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                  )}
                >
                  <span className="font-medium text-gray-900">{mode.label}</span>
                  {localFilters.help_mode === mode.id && (
                    <svg className="w-5 h-5 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </section>
        </div>

        {/* Footer with actions */}
        <div className="sticky bottom-0 bg-white border-t border-gray-100 px-4 py-4 safe-area-bottom">
          <div className="flex gap-2 mb-3">
            <button
              onClick={handleClearAll}
              className="flex-1 py-2.5 px-4 text-sm font-medium text-gray-600 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
            >
              Clear All
            </button>
            <button
              onClick={handleReset}
              className="flex-1 py-2.5 px-4 text-sm font-medium text-primary-600 bg-primary-50 rounded-xl hover:bg-primary-100 transition-colors"
            >
              Reset to Default
            </button>
          </div>
          <button
            onClick={handleApply}
            className="w-full btn-primary"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  )
}

