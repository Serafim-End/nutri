import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useIntakeStore } from '../store/intake'
import { useAuthStore } from '../store/auth'
import { clientApi } from '../lib/api'
import { useTelegramMainButton } from '../hooks/useTelegramMainButton'
import {
  PageContainer,
  Section,
  Stack,
  Grid,
  Button,
  Alert,
  Heading,
  Text,
} from '../design-system'
import clsx from 'clsx'

// Доступные опции для анкеты
const GOALS = [
  { id: 'weight_loss', label: 'Снижение веса', emoji: '⚖️' },
  { id: 'muscle_gain', label: 'Набор массы', emoji: '💪' },
  { id: 'better_nutrition', label: 'Здоровое питание', emoji: '🥗' },
  { id: 'gut_health', label: 'Здоровье ЖКТ', emoji: '🌿' },
  { id: 'sports_nutrition', label: 'Спортивное питание', emoji: '🏃' },
  { id: 'diabetes', label: 'Контроль диабета', emoji: '📊' },
  { id: 'mental_wellness', label: 'Ментальное здоровье', emoji: '🧠' },
  { id: 'pregnancy', label: 'Питание при беременности', emoji: '🤰' },
]

const DIETARY_RESTRICTIONS = [
  { id: 'vegetarian', label: 'Вегетарианство', emoji: '🥬' },
  { id: 'vegan', label: 'Веганство', emoji: '🌱' },
  { id: 'gluten_free', label: 'Без глютена', emoji: '🌾' },
  { id: 'lactose_free', label: 'Без лактозы', emoji: '🥛' },
  { id: 'halal', label: 'Халяль', emoji: '☪️' },
  { id: 'kosher', label: 'Кошер', emoji: '✡️' },
  { id: 'none', label: 'Без ограничений', emoji: '✅' },
]

const BUDGET_RANGES = [
  { min: 0, max: 2000, label: 'До 2 000 ₽' },
  { min: 2000, max: 4000, label: '2 000 – 4 000 ₽' },
  { min: 4000, max: 6000, label: '4 000 – 6 000 ₽' },
  { min: 6000, max: null, label: 'От 6 000 ₽' },
]

const SCHEDULES = [
  { id: 'weekdays', label: 'Будни', emoji: '📅' },
  { id: 'weekends', label: 'Выходные', emoji: '🌴' },
  { id: 'evenings', label: 'Вечером', emoji: '🌙' },
  { id: 'flexible', label: 'Гибкий график', emoji: '🔄' },
]

const STEPS = [
  { title: 'Ваши цели', subtitle: 'Чего вы хотите достичь?' },
  { title: 'Особенности питания', subtitle: 'Есть ли ограничения в рационе?' },
  { title: 'Бюджет', subtitle: 'Какой бюджет на консультацию?' },
  { title: 'Расписание', subtitle: 'Когда вам удобно заниматься?' },
]

// Компонент карточки выбора
interface SelectionCardProps {
  emoji?: string
  label: string
  selected: boolean
  onClick: () => void
  checkmark?: boolean
}

function SelectionCard({ emoji, label, selected, onClick, checkmark = false }: SelectionCardProps) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full p-4 rounded-2xl border-2 text-left',
        'transition-all duration-fast',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
        selected
          ? 'border-primary-500 bg-primary-50'
          : 'border-border-light bg-surface-primary hover:border-border-default'
      )}
    >
      <div className="flex items-center gap-3">
        {emoji && <span className="text-2xl flex-shrink-0">{emoji}</span>}
        <span className="flex-1 font-medium text-text-primary">{label}</span>
        {checkmark && selected && (
          <svg
            className="w-5 h-5 text-primary-500 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>
    </button>
  )
}

// Индикатор прогресса
function ProgressBar({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div
          key={index}
          className={clsx(
            'h-1 flex-1 rounded-full transition-colors duration-slow',
            index <= currentStep ? 'bg-primary-500' : 'bg-neutral-200'
          )}
        />
      ))}
    </div>
  )
}

export default function IntakePage() {
  const navigate = useNavigate()
  const { currentStep, answers, setStep, updateAnswers, setIntakeId } = useIntakeStore()
  const { setOnboardingCompleted, isAuthenticated, token } = useAuthStore()
  const [selectedBudget, setSelectedBudget] = useState<number | null>(
    answers.budget_max !== null
      ? BUDGET_RANGES.findIndex(
          (r) => r.min === answers.budget_min && r.max === answers.budget_max
        )
      : null
  )

  const submitMutation = useMutation({
    mutationFn: () => {
      if (!isAuthenticated || !token) {
        throw new Error('Необходима авторизация. Пожалуйста, обновите страницу.')
      }
      return clientApi.createIntake(answers)
    },
    onSuccess: (data: { intake_id: string }) => {
      setIntakeId(data.intake_id)
      setOnboardingCompleted()
      navigate('/results')
    },
  })

  const isLastStep = currentStep === STEPS.length - 1
  const canProceed =
    (currentStep === 0 && answers.goals.length > 0) ||
    (currentStep === 1 && answers.dietary_restrictions.length > 0) ||
    (currentStep === 2 && selectedBudget !== null) ||
    (currentStep === 3 && answers.preferred_schedule !== null)

  const handleNext = useCallback(() => {
    if (isLastStep) {
      submitMutation.mutate()
    } else {
      setStep(currentStep + 1)
    }
  }, [currentStep, isLastStep, setStep, submitMutation])

  useTelegramMainButton({
    text: isLastStep ? 'Найти нутрициолога' : 'Продолжить',
    onClick: handleNext,
    isVisible: true,
    isActive: canProceed && !submitMutation.isPending,
    showProgress: submitMutation.isPending,
  })

  const toggleGoal = (goalId: string) => {
    const current = answers.goals
    const updated = current.includes(goalId)
      ? current.filter((g) => g !== goalId)
      : [...current, goalId]
    updateAnswers({ goals: updated })
  }

  const toggleRestriction = (restrictionId: string) => {
    let updated: string[]
    if (restrictionId === 'none') {
      updated = answers.dietary_restrictions.includes('none') ? [] : ['none']
    } else {
      const withoutNone = answers.dietary_restrictions.filter((r) => r !== 'none')
      updated = withoutNone.includes(restrictionId)
        ? withoutNone.filter((r) => r !== restrictionId)
        : [...withoutNone, restrictionId]
    }
    updateAnswers({ dietary_restrictions: updated })
  }

  const selectBudget = (index: number) => {
    const range = BUDGET_RANGES[index]
    setSelectedBudget(index)
    updateAnswers({
      budget_min: range.min,
      budget_max: range.max,
    })
  }

  const selectSchedule = (scheduleId: string) => {
    updateAnswers({ preferred_schedule: scheduleId })
  }

  return (
    <PageContainer background="gradient" withBottomNav>
      {/* Заголовок */}
      <Section spacing="sm">
        <Stack gap={4}>
          <ProgressBar currentStep={currentStep} totalSteps={STEPS.length} />
          <div>
            <Heading level="h1" size="xl">
              {STEPS[currentStep].title}
            </Heading>
            <Text color="secondary" className="mt-1">
              {STEPS[currentStep].subtitle}
            </Text>
          </div>
        </Stack>
      </Section>

      {/* Контент */}
      <Section spacing="none" className="pb-32">
        {/* Шаг 1: Цели */}
        {currentStep === 0 && (
          <Grid cols={2} gap={3} className="animate-fade-in">
            {GOALS.map((goal) => (
              <button
                key={goal.id}
                onClick={() => toggleGoal(goal.id)}
                className={clsx(
                  'p-4 rounded-2xl border-2 text-left',
                  'transition-all duration-fast',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                  answers.goals.includes(goal.id)
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-border-light bg-surface-primary hover:border-border-default'
                )}
              >
                <span className="text-2xl">{goal.emoji}</span>
                <p className="mt-2 font-medium text-text-primary text-sm">{goal.label}</p>
              </button>
            ))}
          </Grid>
        )}

        {/* Шаг 2: Особенности питания */}
        {currentStep === 1 && (
          <Stack gap={3} className="animate-fade-in">
            {DIETARY_RESTRICTIONS.map((restriction) => (
              <SelectionCard
                key={restriction.id}
                emoji={restriction.emoji}
                label={restriction.label}
                selected={answers.dietary_restrictions.includes(restriction.id)}
                onClick={() => toggleRestriction(restriction.id)}
                checkmark
              />
            ))}
          </Stack>
        )}

        {/* Шаг 3: Бюджет */}
        {currentStep === 2 && (
          <Stack gap={3} className="animate-fade-in">
            {BUDGET_RANGES.map((range, index) => (
              <SelectionCard
                key={index}
                label={range.label}
                selected={selectedBudget === index}
                onClick={() => selectBudget(index)}
              />
            ))}
          </Stack>
        )}

        {/* Шаг 4: Расписание */}
        {currentStep === 3 && (
          <Grid cols={2} gap={3} className="animate-fade-in">
            {SCHEDULES.map((schedule) => (
              <button
                key={schedule.id}
                onClick={() => selectSchedule(schedule.id)}
                className={clsx(
                  'p-4 rounded-2xl border-2 text-left',
                  'transition-all duration-fast',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                  answers.preferred_schedule === schedule.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-border-light bg-surface-primary hover:border-border-default'
                )}
              >
                <span className="text-2xl">{schedule.emoji}</span>
                <p className="mt-2 font-medium text-text-primary">{schedule.label}</p>
              </button>
            ))}
          </Grid>
        )}

        {/* Сообщение об ошибке */}
        {submitMutation.isError && (
          <div className="mt-4">
            <Alert variant="error" title="Не удалось отправить">
              {submitMutation.error instanceof Error
                ? submitMutation.error.message
                : 'Пожалуйста, попробуйте ещё раз.'}
            </Alert>
          </div>
        )}
      </Section>

      {/* Резервная кнопка: показывать вне Telegram */}
      {!window.Telegram?.WebApp?.initData && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-surface-primary border-t border-border-light safe-area-bottom">
          <Button
            onClick={handleNext}
            disabled={!canProceed || submitMutation.isPending}
            loading={submitMutation.isPending}
            fullWidth
          >
            {isLastStep ? 'Найти нутрициолога' : 'Продолжить'}
          </Button>
        </div>
      )}
    </PageContainer>
  )
}
