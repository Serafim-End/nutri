import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { publicApi } from '../lib/api'
import ServiceCard from '../components/ServiceCard'
import LoadingScreen from '../components/LoadingScreen'
import type { Service } from '../types'
import { useState } from 'react'

export default function NutritionistPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [selectedService, setSelectedService] = useState<Service | null>(null)

  const { data: nutritionistData, isLoading: loadingNutritionist } = useQuery({
    queryKey: ['nutritionist', id],
    queryFn: () => publicApi.getNutritionist(id!),
    enabled: !!id,
  })

  const { data: servicesData, isLoading: loadingServices } = useQuery({
    queryKey: ['services', id],
    queryFn: () => publicApi.getServices(id!),
    enabled: !!id,
  })

  if (loadingNutritionist || loadingServices) {
    return <LoadingScreen />
  }

  if (!nutritionistData?.nutritionist) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-gray-500">Nutritionist not found.</p>
        </div>
      </div>
    )
  }

  const nutritionist = nutritionistData.nutritionist
  const profile = nutritionist.profile
  const services = servicesData?.services || []

  const handleSelectService = (service: Service) => {
    setSelectedService(service)
  }

  const handleBookService = () => {
    if (selectedService) {
      navigate(`/book/${id}/${selectedService.id}`)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Hero section */}
      <div className="bg-gradient-to-b from-primary-500 to-primary-600 px-4 pt-8 pb-16 text-white">
        <div className="flex items-center gap-4">
          {profile?.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.full_name}
              className="w-20 h-20 rounded-2xl object-cover border-2 border-white/30"
            />
          ) : (
            <div className="w-20 h-20 rounded-2xl bg-white/20 flex items-center justify-center">
              <span className="text-3xl font-bold">
                {profile?.full_name?.charAt(0) || 'N'}
              </span>
            </div>
          )}
          <div>
            <h1 className="text-xl font-display font-bold">
              {profile?.full_name || 'Nutritionist'}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex items-center gap-1">
                <svg className="w-4 h-4 text-amber-300" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span className="font-medium">{nutritionist.rating.toFixed(1)}</span>
              </div>
              <span className="text-white/60">•</span>
              <span className="text-white/80 text-sm">
                {nutritionist.reviews_count} reviews
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 -mt-8">
        {/* Bio card */}
        <div className="card mb-6 animate-slide-up">
          <h2 className="font-semibold text-gray-900 mb-2">About</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            {nutritionist.bio || 'Professional nutritionist ready to help you achieve your health goals.'}
          </p>

          {/* Specializations */}
          {nutritionist.specializations?.length > 0 && (
            <div className="mt-4">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Specializations
              </h3>
              <div className="flex flex-wrap gap-2">
                {nutritionist.specializations.map((spec) => (
                  <span
                    key={spec}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-50 text-primary-700"
                  >
                    {spec.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {nutritionist.tags?.length > 0 && (
            <div className="mt-4">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Supports
              </h3>
              <div className="flex flex-wrap gap-2">
                {nutritionist.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
                  >
                    {tag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Services */}
        <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
          <h2 className="font-semibold text-gray-900 mb-3">Services</h2>
          {services.length === 0 ? (
            <p className="text-gray-500 text-sm">No services available.</p>
          ) : (
            <div className="space-y-3 pb-32">
              {services.map((service) => (
                <ServiceCard
                  key={service.id}
                  service={service}
                  selected={selectedService?.id === service.id}
                  onSelect={handleSelectService}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom button */}
      {services.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-100 safe-area-bottom">
          <button
            onClick={handleBookService}
            disabled={!selectedService}
            className="btn-primary w-full"
          >
            {selectedService
              ? `Book for ${selectedService.price_rub.toLocaleString('ru-RU')} ₽`
              : 'Select a service'}
          </button>
        </div>
      )}
    </div>
  )
}


