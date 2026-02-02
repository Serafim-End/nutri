import clsx from 'clsx'
import { Text } from '../design-system'
import { MOSCOW_TIME_NOTE } from '../utils/moscowTime'

type MoscowTimeNoteProps = {
  className?: string
  align?: 'left' | 'center' | 'right'
}

export default function MoscowTimeNote({ className, align = 'left' }: MoscowTimeNoteProps) {
  const alignClass = align === 'center'
    ? 'text-center'
    : align === 'right'
      ? 'text-right'
      : 'text-left'

  return (
    <Text size="xs" className={clsx('text-text-tertiary', alignClass, className)}>
      {MOSCOW_TIME_NOTE}
    </Text>
  )
}
