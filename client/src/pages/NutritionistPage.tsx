import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { publicApi } from '../lib/api'
import ServiceCard from '../components/ServiceCard'
import type { Service, Review } from '../types'
import { useState } from 'react'
import { formatFilterLabel } from '../lib/labels'
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
  const [showReviews, setShowReviews] = useState(false)

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

  const { data: reviewsData, isLoading: loadingReviews } = useQuery({
    queryKey: ['reviews', id],
    queryFn: () => publicApi.getReviews(id!, { limit: 3 }),
    enabled: !!id && showReviews,
  })

  if (loadingNutritionist || loadingServices) {
    return <PageLoader text="Загрузка профиля..." />
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
  const reviews: Review[] = reviewsData?.reviews || []
  const reviewsSummary =
    nutritionist.reviews_count > 0
      ? `${nutritionist.reviews_count} отзывов`
      : 'Пока нет отзывов'

  const formatReviewDate = (value: string) =>
    new Date(value).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })

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
      {/* Верхняя секция с градиентом */}
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
                {profile?.full_name?.charAt(0) || 'Н'}
              </span>
            </div>
          )}
          <div>
            <Heading level="h1" size="lg" className="text-white">
              {profile?.full_name || 'Нутрициолог'}
            </Heading>
            <Inline gap={2} className="mt-1">
              <Inline gap={1}>
                <Icons.Star size="sm" className="text-amber-300" />
                <span className="font-medium">{nutritionist.rating.toFixed(1)}</span>
              </Inline>
              <span className="text-white/60">•</span>
              <span className="text-white/80 text-sm">
                {nutritionist.reviews_count} отзывов
              </span>
            </Inline>
          </div>
        </Inline>
      </div>

      {/* Контент, перекрывающий верхнюю секцию */}
      <div className="px-4 -mt-8">
        {/* Карточка с описанием */}
        <Card variant="elevated" padding="lg" className="mb-6 animate-slide-up">
          <Heading level="h2" size="md" className="mb-3">О специалисте</Heading>
          <Text color="secondary" className="leading-relaxed">
            {nutritionist.bio || 'Профессиональный нутрициолог, готовый помочь вам достичь ваших целей в области здоровья.'}
          </Text>

          {/* Специализации */}
          {nutritionist.specializations?.length > 0 && (
            <div className="mt-5">
              <Text size="xs" weight="medium" color="tertiary" className="uppercase tracking-wider mb-2">
                Специализации
              </Text>
              <div className="flex flex-wrap gap-2">
                {nutritionist.specializations.map((spec: string) => (
                  <Badge key={spec} variant="primary" size="md">
                    {formatFilterLabel(spec)}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Теги */}
          {nutritionist.tags?.length > 0 && (
            <div className="mt-4">
              <Text size="xs" weight="medium" color="tertiary" className="uppercase tracking-wider mb-2">
                Работает с
              </Text>
              <div className="flex flex-wrap gap-2">
                {nutritionist.tags.map((tag: string) => (
                  <Badge key={tag} variant="default" size="md">
                    {formatFilterLabel(tag)}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Отзывы */}
        <Card variant="elevated" padding="lg" className="mb-6 animate-slide-up" style={{ animationDelay: '60ms' }}>
          <Inline align="center" justify="between">
            <div>
              <Heading level="h2" size="md" className="mb-1">Отзывы</Heading>
              <Text size="sm" color="secondary">
                {reviewsSummary}
              </Text>
            </div>
            {nutritionist.reviews_count > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowReviews((prev) => !prev)}
              >
                {showReviews ? 'Скрыть' : 'Показать'}
              </Button>
            )}
          </Inline>

          {showReviews && (
            <div className="mt-4 space-y-4">
              {loadingReviews ? (
                <Text color="secondary">Загрузка отзывов...</Text>
              ) : reviews.length === 0 ? (
                <Text color="secondary">Отзывов пока нет.</Text>
              ) : (
                reviews.map((review) => (
                  <div key={review.id} className="rounded-xl bg-slate-950/30 border border-white/10 p-3">
                    <Inline gap={2} align="center">
                      <Inline gap={1} align="center">
                        <Icons.Star size="sm" className="text-amber-400" />
                        <Text size="sm" weight="medium">{review.rating}</Text>
                      </Inline>
                      <Text size="xs" color="tertiary">•</Text>
                      <Text size="xs" color="tertiary">
                        {review.client_name || 'Клиент'}
                      </Text>
                      <Text size="xs" color="tertiary">•</Text>
                      <Text size="xs" color="tertiary">
                        {formatReviewDate(review.created_at)}
                      </Text>
                    </Inline>
                    {review.comment && (
                      <Text size="sm" color="secondary" className="mt-2 leading-relaxed">
                        {review.comment}
                      </Text>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </Card>

        {/* Услуги */}
        <div className="animate-slide-up" style={{ animationDelay: '100ms' }}>
          <Heading level="h2" size="md" className="mb-4">Услуги</Heading>
          {services.length === 0 ? (
            <Text color="secondary">Услуги пока не добавлены.</Text>
          ) : (
            <Stack gap={3} className="pb-32">
              {services.map((service: Service) => (
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

      {/* Нижняя кнопка */}
      {services.length > 0 && (
        <Footer bordered>
          <Button
            onClick={handleBookService}
            disabled={!selectedService}
            fullWidth
            size="lg"
          >
            {selectedService
              ? `Забронировать за ${selectedService.price_rub.toLocaleString('ru-RU')} ₽`
              : 'Выберите услугу'}
          </Button>
        </Footer>
      )}
    </PageContainer>
  )
}
