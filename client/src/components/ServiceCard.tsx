import type { Service } from '../types'
import { Inline, Text, Icons } from '../design-system'
import clsx from 'clsx'

interface ServiceCardProps {
  service: Service
  selected?: boolean
  onSelect: (service: Service) => void
}

export default function ServiceCard({ service, selected, onSelect }: ServiceCardProps) {
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
            <Text size="sm" color="secondary" lineClamp={2} className="mt-1">
              {service.description}
            </Text>
          )}
          <Inline gap={1} className="mt-2 text-text-tertiary">
            <Icons.Clock size="sm" />
            <Text size="sm" color="tertiary">
              {service.duration_minutes} min
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
