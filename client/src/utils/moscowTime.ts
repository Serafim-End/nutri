const MOSCOW_TIMEZONE = 'Europe/Moscow'
const RU_LOCALE = 'ru-RU'

type MoscowParts = {
  year: string
  month: string
  day: string
  hour: string
  minute: string
}

const moscowPartsFormatter = new Intl.DateTimeFormat(RU_LOCALE, {
  timeZone: MOSCOW_TIMEZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

const moscowDateFormatter = new Intl.DateTimeFormat(RU_LOCALE, {
  timeZone: MOSCOW_TIMEZONE,
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

const moscowTimeFormatter = new Intl.DateTimeFormat(RU_LOCALE, {
  timeZone: MOSCOW_TIMEZONE,
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

export const MOSCOW_TIME_NOTE = 'Время указано по Москве (МСК).'

const getMoscowParts = (value: string | Date): MoscowParts | null => {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return null

  const parts = moscowPartsFormatter.formatToParts(date)
  const result: MoscowParts = {
    year: '',
    month: '',
    day: '',
    hour: '',
    minute: '',
  }

  for (const part of parts) {
    if (part.type in result) {
      result[part.type as keyof MoscowParts] = part.value
    }
  }

  if (!result.year || !result.month || !result.day) return null
  return result
}

export const getMoscowDateKey = (value: string): string | null => {
  const parts = getMoscowParts(value)
  if (!parts) return null
  return `${parts.year}-${parts.month}-${parts.day}`
}

export const formatMoscowDateLong = (value: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return moscowDateFormatter.format(date)
}

export const formatMoscowTime = (value: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return moscowTimeFormatter.format(date)
}

export const formatMoscowDateTime = (value?: string | null): string => {
  if (!value) return '—'
  const parts = getMoscowParts(value)
  if (!parts) return '—'
  return `${parts.day}.${parts.month}.${parts.year} ${parts.hour}:${parts.minute}`
}

export const formatMoscowDateKeyLong = (dateKey: string): string => {
  const [year, month, day] = dateKey.split('-')
  if (!year || !month || !day) return '—'
  const date = new Date(Date.UTC(Number(year), Number(month) - 1, Number(day), 0, 0, 0))
  if (Number.isNaN(date.getTime())) return '—'
  return moscowDateFormatter.format(date)
}
