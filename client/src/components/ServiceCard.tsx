import { useState, useRef, useEffect } from 'react'
import type { Service } from '../types'
import { Inline, Text, Icons } from '../design-system'
import clsx from 'clsx'

interface ServiceCardProps {
  service: Service
  selected?: boolean
  onSelect: (service: Service) => void
}

function useIsClamped(ref: React.RefObject<HTMLElement | null>, expanded: boolean, description: string | null) {
  const [isClamped, setIsClamped] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el || expanded) {
      setIsClamped(false)
      return
    }

    const checkClamped = () => {
      setIsClamped(el.scrollHeight > el.clientHeight)
    }

    checkClamped()

    const observer = new ResizeObserver(checkClamped)
    observer.observe(el)
    return () => observer.disconnect()
  }, [ref, expanded, description])

  return isClamped
}

export default function ServiceCard({ service, selected, onSelect }: ServiceCardProps) {
  const [expanded, setExpanded] = useState(false)
  const descRef = useRef<HTMLParagraphElement>(null)
  const isClamped = useIsClamped(descRef, expanded, service.description)
  const showToggle = isClamped || expanded

  return (
    <button
      onClick={() => onSelect(service)}
      className={clsx(
        'w-full text-left rounded-2xl p-4',
        'bg-surface-primary border-2 transition-all duration-fast',
        selected
          ? 'border-primary-500 bg-primary-50 shadow-sm'
          : 'border-border-light hover:border-border-default hover:shadow-xs'
      )}
    >
      <Inline justify="between" align="start" gap={4}>
        <div className="flex-1 min-w-0">
          <Text weight="semibold" className={clsx(selected && 'text-primary-700')}>
            {service.title}
          </Text>
          {service.description && (
            <div className="mt-1">
              <Text
                ref={descRef}
                as="p"
                size="sm"
                color="secondary"
                lineClamp={expanded ? undefined : 2}
                className="mt-0"
              >
                {service.description}
              </Text>
              {showToggle && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setExpanded((prev) => !prev)
                  }}
                  className="mt-0.5 text-sm text-primary-600 hover:text-primary-700 hover:underline"
                >
                  {expanded ? 'скрыть' : 'показать полностью'}
                </button>
              )}
            </div>
          )}
          <Inline gap={1} className="mt-2 text-text-tertiary">
            <Icons.Clock size="sm" />
            <Text size="sm" color="tertiary">
              {service.duration_minutes} мин
            </Text>
          </Inline>
        </div>
        <div className="flex-shrink-0 text-right">
          <Text size="lg" weight="bold" className="text-primary-600">
            {service.price_rub.toLocaleString('ru-RU')} ₽
          </Text>
        </div>
      </Inline>
    </button>
  )
}
