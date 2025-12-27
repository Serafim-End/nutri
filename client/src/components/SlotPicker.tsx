import { useMemo } from 'react'
import { format, parseISO, isSameDay } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { AvailabilitySlot } from '../types'
import clsx from 'clsx'

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
      const date = format(parseISO(slot.start_at), 'yyyy-MM-dd')
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(slot)
    })

    // Sort slots within each group
    Object.keys(groups).forEach((date) => {
      groups[date].sort(
        (a, b) => parseISO(a.start_at).getTime() - parseISO(b.start_at).getTime()
      )
    })

    return groups
  }, [slots])

  const sortedDates = Object.keys(groupedSlots).sort()

  if (slots.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No available slots at the moment.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {sortedDates.map((date) => {
        const dateObj = parseISO(date)
        return (
          <div key={date}>
            <h4 className="font-medium text-gray-900 mb-3">
              {format(dateObj, 'EEEE, d MMMM', { locale: ru })}
            </h4>
            <div className="grid grid-cols-3 gap-2">
              {groupedSlots[date].map((slot) => {
                const isSelected = selectedSlot?.id === slot.id
                const startTime = format(parseISO(slot.start_at), 'HH:mm')

                return (
                  <button
                    key={slot.id}
                    onClick={() => onSelectSlot(slot)}
                    className={clsx(
                      'py-2 px-3 rounded-xl text-sm font-medium transition-all duration-200',
                      isSelected
                        ? 'bg-primary-500 text-white shadow-md'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
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
    </div>
  )
}


