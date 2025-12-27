import { create } from 'zustand'
import type { IntakeAnswers } from '../types'

interface IntakeState {
  currentStep: number
  answers: IntakeAnswers
  intakeId: string | null
  setStep: (step: number) => void
  updateAnswers: (updates: Partial<IntakeAnswers>) => void
  setIntakeId: (id: string) => void
  reset: () => void
}

const initialAnswers: IntakeAnswers = {
  goals: [],
  dietary_restrictions: [],
  budget_min: null,
  budget_max: null,
  preferred_schedule: null,
  health_conditions: [],
  additional_notes: null,
}

export const useIntakeStore = create<IntakeState>((set) => ({
  currentStep: 0,
  answers: initialAnswers,
  intakeId: null,
  setStep: (step) => set({ currentStep: step }),
  updateAnswers: (updates) =>
    set((state) => ({
      answers: { ...state.answers, ...updates },
    })),
  setIntakeId: (id) => set({ intakeId: id }),
  reset: () =>
    set({
      currentStep: 0,
      answers: initialAnswers,
      intakeId: null,
    }),
}))


