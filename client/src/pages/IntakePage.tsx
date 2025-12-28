import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useIntakeStore } from '../store/intake'
import { clientApi } from '../lib/api'
import { useTelegramMainButton } from '../hooks/useTelegramMainButton'
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
  { title: 'Budget', subtitle: 'What\'s your budget per session?' },
  { title: 'Schedule', subtitle: 'When do you prefer consultations?' },
]

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
    <div className="min-h-screen bg-gradient-to-b from-primary-50/50 to-white">
      {/* Header */}
      <div className="px-4 pt-6 pb-4">
        <div className="flex items-center gap-2 mb-4">
          {STEPS.map((_, index) => (
            <div
              key={index}
              className={clsx(
                'h-1 flex-1 rounded-full transition-colors duration-300',
                index <= currentStep ? 'bg-primary-500' : 'bg-gray-200'
              )}
            />
          ))}
        </div>
        <h1 className="text-2xl font-display font-bold text-gray-900">
          {STEPS[currentStep].title}
        </h1>
        <p className="text-gray-500 mt-1">{STEPS[currentStep].subtitle}</p>
      </div>

      {/* Content */}
      <div className="px-4 pb-32">
        {/* Step 1: Goals */}
        {currentStep === 0 && (
          <div className="grid grid-cols-2 gap-3 animate-fade-in">
            {GOALS.map((goal) => {
              const isSelected = answers.goals.includes(goal.id)
              return (
                <button
                  key={goal.id}
                  onClick={() => toggleGoal(goal.id)}
                  className={clsx(
                    'p-4 rounded-2xl border-2 text-left transition-all duration-200',
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-100 bg-white hover:border-gray-200'
                  )}
                >
                  <span className="text-2xl">{goal.emoji}</span>
                  <p className="mt-2 font-medium text-gray-900 text-sm">{goal.label}</p>
                </button>
              )
            })}
          </div>
        )}

        {/* Step 2: Dietary Restrictions */}
        {currentStep === 1 && (
          <div className="space-y-3 animate-fade-in">
            {DIETARY_RESTRICTIONS.map((restriction) => {
              const isSelected = answers.dietary_restrictions.includes(restriction.id)
              return (
                <button
                  key={restriction.id}
                  onClick={() => toggleRestriction(restriction.id)}
                  className={clsx(
                    'w-full p-4 rounded-2xl border-2 text-left transition-all duration-200 flex items-center gap-3',
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-100 bg-white hover:border-gray-200'
                  )}
                >
                  <span className="text-2xl">{restriction.emoji}</span>
                  <span className="font-medium text-gray-900">{restriction.label}</span>
                  {isSelected && (
                    <svg
                      className="w-5 h-5 text-primary-500 ml-auto"
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
                </button>
              )
            })}
          </div>
        )}

        {/* Step 3: Budget */}
        {currentStep === 2 && (
          <div className="space-y-3 animate-fade-in">
            {BUDGET_RANGES.map((range, index) => {
              const isSelected = selectedBudget === index
              return (
                <button
                  key={index}
                  onClick={() => selectBudget(index)}
                  className={clsx(
                    'w-full p-4 rounded-2xl border-2 text-left transition-all duration-200',
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-100 bg-white hover:border-gray-200'
                  )}
                >
                  <span className="font-medium text-gray-900">{range.label}</span>
                </button>
              )
            })}
          </div>
        )}

        {/* Step 4: Schedule */}
        {currentStep === 3 && (
          <div className="grid grid-cols-2 gap-3 animate-fade-in">
            {SCHEDULES.map((schedule) => {
              const isSelected = answers.preferred_schedule === schedule.id
              return (
                <button
                  key={schedule.id}
                  onClick={() => selectSchedule(schedule.id)}
                  className={clsx(
                    'p-4 rounded-2xl border-2 text-left transition-all duration-200',
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-100 bg-white hover:border-gray-200'
                  )}
                >
                  <span className="text-2xl">{schedule.emoji}</span>
                  <p className="mt-2 font-medium text-gray-900">{schedule.label}</p>
                </button>
              )
            })}
          </div>
        )}

        {/* Error message */}
        {submitMutation.isError && (
          <div className="mt-4 p-4 rounded-xl bg-red-50 text-red-600 text-sm">
            <p className="font-medium">Failed to submit. Please try again.</p>
            <p className="mt-1 text-xs opacity-75">
              {submitMutation.error instanceof Error 
                ? submitMutation.error.message 
                : 'Unknown error'}
            </p>
          </div>
        )}
      </div>

      {/* Fallback button: Show when not in real Telegram (no initData) */}
      {(!window.Telegram?.WebApp?.initData) && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-100">
          <button
            onClick={handleNext}
            disabled={!canProceed || submitMutation.isPending}
            className="btn-primary w-full"
          >
            {submitMutation.isPending
              ? 'Loading...'
              : isLastStep
              ? 'Find Nutritionists'
              : 'Continue'}
          </button>
        </div>
      )}
    </div>
  )
}


