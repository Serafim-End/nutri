import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { publicApi } from '../lib/api'
import type { SearchFilters, FilterOptions } from '../types'
import {
  BottomSheet,
  Stack,
  Button,
  Text,
} from '../design-system'
import clsx from 'clsx'

interface FilterDrawerProps {
  isOpen: boolean
  onClose: () => void
  filters: SearchFilters
  defaults: SearchFilters
  onApply: (filters: SearchFilters) => void
  onReset: () => void
}

// Опции фильтров по умолчанию
const DEFAULT_OPTIONS: FilterOptions = {
  goals: [
    { id: 'weight_loss', label: 'Снижение веса' },
    { id: 'muscle_gain', label: 'Набор массы' },
    { id: 'better_nutrition', label: 'Здоровое питание' },
    { id: 'gut_health', label: 'Здоровье ЖКТ' },
    { id: 'sports_nutrition', label: 'Спортивное питание' },
    { id: 'diabetes', label: 'Контроль диабета' },
    { id: 'mental_wellness', label: 'Ментальное здоровье' },
    { id: 'pregnancy', label: 'Питание при беременности' },
  ],
  topics: [
    { id: 'nutrition_basics', label: 'Основы питания' },
    { id: 'meal_planning', label: 'Планирование рациона' },
    { id: 'supplements', label: 'Добавки и витамины' },
    { id: 'weight_management', label: 'Контроль веса' },
    { id: 'sports_performance', label: 'Спортивные результаты' },
    { id: 'chronic_conditions', label: 'Хронические заболевания' },
  ],
  dietary: [
    { id: 'vegetarian', label: 'Вегетарианство' },
    { id: 'vegan', label: 'Веганство' },
    { id: 'gluten_free', label: 'Без глютена' },
    { id: 'lactose_free', label: 'Без лактозы' },
    { id: 'halal', label: 'Халяль' },
    { id: 'kosher', label: 'Кошер' },
  ],
  help_modes: [
    { id: 'one_time', label: 'Разовая консультация' },
    { id: 'plan', label: 'План питания' },
    { id: 'long_term', label: 'Длительное сопровождение' },
  ],
  budget_ranges: [
    { id: 'up_to_2000', max: 2000, label: 'До 2 000 ₽' },
    { id: '2000_3000', max: 3000, label: '2 000 – 3 000 ₽' },
    { id: '3000_5000', max: 5000, label: '3 000 – 5 000 ₽' },
    { id: 'above_5000', max: null, label: 'От 5 000 ₽' },
    { id: 'unknown', max: null, label: 'Не знаю' },
  ],
}

// Кнопка выбора для одиночных опций
interface SelectionButtonProps {
  label: string
  selected: boolean
  onClick: () => void
}

function SelectionButton({ label, selected, onClick }: SelectionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'w-full px-4 py-3 rounded-xl text-left transition-all duration-fast',
        'flex items-center justify-between',
        selected
          ? 'bg-primary-50 border-2 border-primary-500'
          : 'bg-neutral-50 border-2 border-transparent hover:bg-neutral-100'
      )}
    >
      <span className="font-medium text-text-primary">{label}</span>
      {selected && (
        <svg className="w-5 h-5 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </button>
  )
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

  // Загрузка опций фильтров с бэкенда
  const { data: options } = useQuery({
    queryKey: ['filterOptions'],
    queryFn: publicApi.getFilterOptions,
    staleTime: Infinity,
  })

  const filterOptions = options || DEFAULT_OPTIONS

  // Синхронизация локальных фильтров при открытии
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

  // Поиск соответствующего ID бюджета
  const selectedBudgetId =
    localFilters.budget_max_rub === null
      ? null
      : filterOptions.budget_ranges.find(
          (r) => r.max === localFilters.budget_max_rub
        )?.id || null

  return (
    <BottomSheet isOpen={isOpen} onClose={onClose} title="Фильтры">
      {/* Контент */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
        {/* Цели */}
        <section>
          <Text size="sm" weight="semibold" color="secondary" className="mb-3">
            Цели
          </Text>
          <div className="flex flex-wrap gap-2">
            {filterOptions.goals.map((goal) => (
              <button
                key={goal.id}
                onClick={() => toggleArrayValue('goals', goal.id)}
                className={clsx(
                  'px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-fast',
                  localFilters.goals.includes(goal.id)
                    ? 'bg-primary-500 text-white shadow-sm'
                    : 'bg-neutral-100 text-text-secondary hover:bg-neutral-200'
                )}
              >
                {goal.label}
              </button>
            ))}
          </div>
        </section>

        {/* Темы */}
        <section>
          <Text size="sm" weight="semibold" color="secondary" className="mb-3">
            Темы
          </Text>
          <div className="flex flex-wrap gap-2">
            {filterOptions.topics.map((topic) => (
              <button
                key={topic.id}
                onClick={() => toggleArrayValue('topics', topic.id)}
                className={clsx(
                  'px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-fast',
                  localFilters.topics.includes(topic.id)
                    ? 'bg-primary-500 text-white shadow-sm'
                    : 'bg-neutral-100 text-text-secondary hover:bg-neutral-200'
                )}
              >
                {topic.label}
              </button>
            ))}
          </div>
        </section>

        {/* Бюджет */}
        <section>
          <Text size="sm" weight="semibold" color="secondary" className="mb-3">
            Бюджет за сессию
          </Text>
          <Stack gap={2}>
            {filterOptions.budget_ranges.map((range) => (
              <SelectionButton
                key={range.id}
                label={range.label}
                selected={
                  selectedBudgetId === range.id ||
                  (range.id === 'unknown' && localFilters.budget_max_rub === null)
                }
                onClick={() => setBudgetMax(range.max)}
              />
            ))}
          </Stack>
        </section>

        {/* Диетические ограничения */}
        <section>
          <Text size="sm" weight="semibold" color="secondary" className="mb-3">
            Особенности питания
          </Text>
          <div className="flex flex-wrap gap-2">
            {filterOptions.dietary.map((diet) => (
              <button
                key={diet.id}
                onClick={() => toggleArrayValue('dietary', diet.id)}
                className={clsx(
                  'px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-fast',
                  localFilters.dietary.includes(diet.id)
                    ? 'bg-primary-500 text-white shadow-sm'
                    : 'bg-neutral-100 text-text-secondary hover:bg-neutral-200'
                )}
              >
                {diet.label}
              </button>
            ))}
          </div>
        </section>

        {/* Тип помощи */}
        <section>
          <Text size="sm" weight="semibold" color="secondary" className="mb-3">
            Тип консультации
          </Text>
          <Stack gap={2}>
            {filterOptions.help_modes.map((mode) => (
              <SelectionButton
                key={mode.id}
                label={mode.label}
                selected={localFilters.help_mode === mode.id}
                onClick={() =>
                  setHelpMode(localFilters.help_mode === mode.id ? null : mode.id)
                }
              />
            ))}
          </Stack>
        </section>
      </div>

      {/* Футер с действиями */}
      <div className="sticky bottom-0 bg-surface-primary border-t border-border-light px-4 py-4 safe-area-bottom">
        <div className="flex gap-2 mb-3">
          <Button
            variant="secondary"
            size="md"
            onClick={handleClearAll}
            className="flex-1"
          >
            Очистить всё
          </Button>
          <Button
            variant="ghost"
            size="md"
            onClick={handleReset}
            className="flex-1 text-primary-600 bg-primary-50 hover:bg-primary-100"
          >
            По умолчанию
          </Button>
        </div>
        <Button onClick={handleApply} fullWidth>
          Применить фильтры
        </Button>
      </div>
    </BottomSheet>
  )
}
