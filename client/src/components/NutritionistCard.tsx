import { Link } from 'react-router-dom'
import type { NutritionistProfile } from '../types'
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
        'card block hover:shadow-md transition-all duration-200',
        'animate-slide-up opacity-0'
      )}
      style={{ animationDelay: `${animationDelay}ms`, animationFillMode: 'forwards' }}
    >
      <div className="flex gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {profile?.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.full_name}
              className="w-16 h-16 rounded-2xl object-cover bg-gray-100"
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
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-gray-900 truncate">
              {profile?.full_name || 'Nutritionist'}
            </h3>
            {/* Rating */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <svg className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span className="text-sm font-medium text-gray-700">
                {nutritionist.rating.toFixed(1)}
              </span>
              <span className="text-xs text-gray-400">
                ({nutritionist.reviews_count})
              </span>
            </div>
          </div>

          {/* Bio */}
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">
            {nutritionist.bio || 'Professional nutritionist ready to help you.'}
          </p>

          {/* Tags */}
          {nutritionist.specializations?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {nutritionist.specializations.slice(0, 3).map((spec) => (
                <span
                  key={spec}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700"
                >
                  {spec.replace(/_/g, ' ')}
                </span>
              ))}
              {nutritionist.specializations.length > 3 && (
                <span className="text-xs text-gray-400">
                  +{nutritionist.specializations.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}


