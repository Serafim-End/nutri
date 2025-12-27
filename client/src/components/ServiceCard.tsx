import type { Service } from '../types'
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
        'card w-full text-left transition-all duration-200',
        selected
          ? 'ring-2 ring-primary-500 bg-primary-50'
          : 'hover:bg-gray-50'
      )}
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">{service.title}</h4>
          {service.description && (
            <p className="mt-1 text-sm text-gray-500 line-clamp-2">
              {service.description}
            </p>
          )}
          <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {service.duration_minutes} min
            </span>
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <div className="text-lg font-bold text-primary-600">
            {service.price_rub.toLocaleString('ru-RU')} ₽
          </div>
        </div>
      </div>
    </button>
  )
}


