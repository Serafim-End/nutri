import { useMemo } from 'react'
import type { AvailabilitySlot } from '../types'
import { Stack, Text, NoSlotsState } from '../design-system'
import clsx from 'clsx'
import MoscowTimeNote from './MoscowTimeNote'
import {
  formatMoscowDateKeyLong,
  formatMoscowTime,
  getMoscowDateKey,
} from '../utils/moscowTime'

interface SlotPickerProps {
  slots: AvailabilitySlot[]
  selectedSlot: AvailabilitySlot | null
  onSelectSlot: (slot: AvailabilitySlot) => void
}

export default function SlotPicker({
  slots,
  selectedSlot,
  onSelectSlot,
}: SlotPickerProps) {
  // Group slots by date
  const groupedSlots = useMemo(() => {
    const groups: Record<string, AvailabilitySlot[]> = {}

    slots.forEach((slot) => {
      const date = getMoscowDateKey(slot.start_at)
      if (!date) return
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(slot)
    })

    // Sort slots within each group
    Object.keys(groups).forEach((date) => {
      groups[date].sort(
        (a, b) => Date.parse(a.start_at) - Date.parse(b.start_at)
      )
    })

    return groups
  }, [slots])

  const sortedDates = Object.keys(groupedSlots).sort()

  if (slots.length === 0) {
    return <NoSlotsState />
  }

  return (
    <Stack gap={6}>
      {sortedDates.map((date) => {
        const dateLabel = formatMoscowDateKeyLong(date)
        return (
          <div key={date}>
            <Text weight="medium" className="mb-3">
              {dateLabel}
            </Text>
            <div className="grid grid-cols-3 gap-2">
              {groupedSlots[date].map((slot) => {
                const isSelected = selectedSlot?.id === slot.id
                const startTime = formatMoscowTime(slot.start_at)

                return (
                  <button
                    key={slot.id}
                    onClick={() => onSelectSlot(slot)}
                    className={clsx(
                      'py-2.5 px-3 rounded-xl text-sm font-medium',
                      'transition-all duration-fast',
                      'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                      isSelected
                        ? 'bg-primary-500 text-white shadow-md shadow-primary-500/25'
                        : 'bg-neutral-100 text-text-secondary hover:bg-neutral-200'
                    )}
                  >
                    {startTime}
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
      <MoscowTimeNote className="mt-2" />
    </Stack>
  )
}
