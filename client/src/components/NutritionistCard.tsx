import { Link } from 'react-router-dom'
import type { NutritionistProfile } from '../types'
import { Inline, Badge, Text, Icons } from '../design-system'
import clsx from 'clsx'

interface NutritionistCardProps {
  nutritionist: NutritionistProfile
  animationDelay?: number
}

export default function NutritionistCard({
  nutritionist,
  animationDelay = 0,
}: NutritionistCardProps) {
  const profile = nutritionist.profile

  return (
    <Link
      to={`/nutritionist/${nutritionist.nutritionist_id}`}
      className={clsx(
        'block rounded-2xl bg-surface-primary border border-border-light p-4',
        'shadow-xs hover:shadow-md transition-all duration-fast',
        'animate-slide-up opacity-0'
      )}
      style={{ animationDelay: `${animationDelay}ms`, animationFillMode: 'forwards' }}
    >
      <Inline gap={4} align="start">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {profile?.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.full_name}
              className="w-16 h-16 rounded-2xl object-cover bg-neutral-100"
            />
          ) : (
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
              <span className="text-white text-xl font-bold">
                {profile?.full_name?.charAt(0) || 'N'}
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <Inline justify="between" gap={2}>
            <Text weight="semibold" truncate>
              {profile?.full_name || 'Nutritionist'}
            </Text>
            {/* Rating */}
            <Inline gap={1} className="flex-shrink-0">
              <Icons.Star size="sm" className="text-accent-amber" />
              <Text size="sm" weight="medium">
                {nutritionist.rating.toFixed(1)}
              </Text>
              <Text size="xs" color="tertiary">
                ({nutritionist.reviews_count})
              </Text>
            </Inline>
          </Inline>

          {/* Bio */}
          <Text size="sm" color="secondary" lineClamp={2} className="mt-1">
            {nutritionist.bio || 'Professional nutritionist ready to help you.'}
          </Text>

          {/* Tags */}
          {nutritionist.specializations?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {nutritionist.specializations.slice(0, 3).map((spec) => (
                <Badge key={spec} variant="primary" size="sm">
                  {spec.replace(/_/g, ' ')}
                </Badge>
              ))}
              {nutritionist.specializations.length > 3 && (
                <Text size="xs" color="tertiary">
                  +{nutritionist.specializations.length - 3}
                </Text>
              )}
            </div>
          )}
        </div>
      </Inline>
    </Link>
  )
}
