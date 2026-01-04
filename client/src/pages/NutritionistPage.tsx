import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { publicApi } from '../lib/api'
import ServiceCard from '../components/ServiceCard'
import type { Service } from '../types'
import { useState } from 'react'
import {
  PageContainer,
  Stack,
  Inline,
  Card,
  Badge,
  Button,
  Heading,
  Text,
  Footer,
  Icons,
  NotFoundState,
} from '../design-system'
import { PageLoader } from '../design-system/components/Loader'

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
    return <PageLoader text="Loading profile..." />
  }

  if (!nutritionistData?.nutritionist) {
    return (
      <PageContainer>
        <div className="min-h-screen flex items-center justify-center px-4">
          <NotFoundState onBack={() => navigate(-1)} />
        </div>
      </PageContainer>
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
    <PageContainer background="primary">
      {/* Hero section with gradient */}
      <div className="bg-gradient-to-b from-primary-500 to-primary-600 px-4 pt-8 pb-16 text-white">
        <Inline gap={4} align="center">
          {profile?.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.full_name}
              className="w-20 h-20 rounded-2xl object-cover border-2 border-white/30 shadow-lg"
            />
          ) : (
            <div className="w-20 h-20 rounded-2xl bg-white/20 flex items-center justify-center shadow-lg">
              <span className="text-3xl font-bold">
                {profile?.full_name?.charAt(0) || 'N'}
              </span>
            </div>
          )}
          <div>
            <Heading level="h1" size="lg" className="text-white">
              {profile?.full_name || 'Nutritionist'}
            </Heading>
            <Inline gap={2} className="mt-1">
              <Inline gap={1}>
                <Icons.Star size="sm" className="text-amber-300" />
                <span className="font-medium">{nutritionist.rating.toFixed(1)}</span>
              </Inline>
              <span className="text-white/60">•</span>
              <span className="text-white/80 text-sm">
                {nutritionist.reviews_count} reviews
              </span>
            </Inline>
          </div>
        </Inline>
      </div>

      {/* Content overlapping hero */}
      <div className="px-4 -mt-8">
        {/* Bio card */}
        <Card variant="elevated" padding="lg" className="mb-6 animate-slide-up">
          <Heading level="h2" size="md" className="mb-3">About</Heading>
          <Text color="secondary" className="leading-relaxed">
            {nutritionist.bio || 'Professional nutritionist ready to help you achieve your health goals.'}
          </Text>

          {/* Specializations */}
          {nutritionist.specializations?.length > 0 && (
            <div className="mt-5">
              <Text size="xs" weight="medium" color="tertiary" className="uppercase tracking-wider mb-2">
                Specializations
              </Text>
              <div className="flex flex-wrap gap-2">
                {nutritionist.specializations.map((spec) => (
                  <Badge key={spec} variant="primary" size="md">
                    {spec.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {nutritionist.tags?.length > 0 && (
            <div className="mt-4">
              <Text size="xs" weight="medium" color="tertiary" className="uppercase tracking-wider mb-2">
                Supports
              </Text>
              <div className="flex flex-wrap gap-2">
                {nutritionist.tags.map((tag) => (
                  <Badge key={tag} variant="default" size="md">
                    {tag.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Services */}
        <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
          <Heading level="h2" size="md" className="mb-4">Services</Heading>
          {services.length === 0 ? (
            <Text color="secondary">No services available.</Text>
          ) : (
            <Stack gap={3} className="pb-32">
              {services.map((service) => (
                <ServiceCard
                  key={service.id}
                  service={service}
                  selected={selectedService?.id === service.id}
                  onSelect={handleSelectService}
                />
              ))}
            </Stack>
          )}
        </div>
      </div>

      {/* Bottom button */}
      {services.length > 0 && (
        <Footer bordered>
          <Button
            onClick={handleBookService}
            disabled={!selectedService}
            fullWidth
            size="lg"
          >
            {selectedService
              ? `Book for ${selectedService.price_rub.toLocaleString('ru-RU')} ₽`
              : 'Select a service'}
          </Button>
        </Footer>
      )}
    </PageContainer>
  )
}
