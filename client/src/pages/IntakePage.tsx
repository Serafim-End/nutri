import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useIntakeStore } from '../store/intake'
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

// Available options for the intake form
const GOALS = [
  { id: 'weight_loss', label: 'Weight Loss', emoji: '⚖️' },
  { id: 'muscle_gain', label: 'Muscle Gain', emoji: '💪' },
  { id: 'better_nutrition', label: 'Better Nutrition', emoji: '🥗' },
  { id: 'gut_health', label: 'Gut Health', emoji: '🌿' },
  { id: 'sports_nutrition', label: 'Sports Nutrition', emoji: '🏃' },
  { id: 'diabetes', label: 'Diabetes Management', emoji: '📊' },
  { id: 'mental_wellness', label: 'Mental Wellness', emoji: '🧠' },
  { id: 'pregnancy', label: 'Pregnancy Nutrition', emoji: '🤰' },
]

const DIETARY_RESTRICTIONS = [
  { id: 'vegetarian', label: 'Vegetarian', emoji: '🥬' },
  { id: 'vegan', label: 'Vegan', emoji: '🌱' },
  { id: 'gluten_free', label: 'Gluten Free', emoji: '🌾' },
  { id: 'lactose_free', label: 'Lactose Free', emoji: '🥛' },
  { id: 'halal', label: 'Halal', emoji: '☪️' },
  { id: 'kosher', label: 'Kosher', emoji: '✡️' },
  { id: 'none', label: 'No Restrictions', emoji: '✅' },
]

const BUDGET_RANGES = [
  { min: 0, max: 2000, label: 'Up to 2,000 ₽' },
  { min: 2000, max: 4000, label: '2,000 - 4,000 ₽' },
  { min: 4000, max: 6000, label: '4,000 - 6,000 ₽' },
  { min: 6000, max: null, label: '6,000+ ₽' },
]

const SCHEDULES = [
  { id: 'weekdays', label: 'Weekdays', emoji: '📅' },
  { id: 'weekends', label: 'Weekends', emoji: '🌴' },
  { id: 'evenings', label: 'Evenings', emoji: '🌙' },
  { id: 'flexible', label: 'Flexible', emoji: '🔄' },
]

const STEPS = [
  { title: 'Your Goals', subtitle: 'What would you like to achieve?' },
  { title: 'Dietary Needs', subtitle: 'Any dietary restrictions?' },
  { title: 'Budget', subtitle: "What's your budget per session?" },
  { title: 'Schedule', subtitle: 'When do you prefer consultations?' },
]

// Selection card component
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

// Progress indicator
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
  const [selectedBudget, setSelectedBudget] = useState<number | null>(
    answers.budget_max !== null
      ? BUDGET_RANGES.findIndex(
          (r) => r.min === answers.budget_min && r.max === answers.budget_max
        )
      : null
  )

  const submitMutation = useMutation({
    mutationFn: () => clientApi.createIntake(answers),
    onSuccess: (data) => {
      setIntakeId(data.intake_id)
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
    text: isLastStep ? 'Find Nutritionists' : 'Continue',
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
      {/* Header */}
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

      {/* Content */}
      <Section spacing="none" className="pb-32">
        {/* Step 1: Goals */}
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

        {/* Step 2: Dietary Restrictions */}
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

        {/* Step 3: Budget */}
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

        {/* Step 4: Schedule */}
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

        {/* Error message */}
        {submitMutation.isError && (
          <div className="mt-4">
            <Alert variant="error" title="Submission failed">
              {submitMutation.error instanceof Error
                ? submitMutation.error.message
                : 'Please try again.'}
            </Alert>
          </div>
        )}
      </Section>

      {/* Fallback button: Show when not in real Telegram */}
      {!window.Telegram?.WebApp?.initData && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-surface-primary border-t border-border-light safe-area-bottom">
          <Button
            onClick={handleNext}
            disabled={!canProceed || submitMutation.isPending}
            loading={submitMutation.isPending}
            fullWidth
          >
            {isLastStep ? 'Find Nutritionists' : 'Continue'}
          </Button>
        </div>
      )}
    </PageContainer>
  )
}
