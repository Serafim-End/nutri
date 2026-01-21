import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { publicApi, bookingApi, paymentApi } from '../lib/api'
import { useCountdown } from '../hooks/useCountdown'
import SlotPicker from '../components/SlotPicker'
import type { AvailabilitySlot, Booking, PaymentIntent, Service } from '../types'
import {
  PageContainer,
  Section,
  Header,
  Footer,
  Stack,
  Inline,
  Card,
  Badge,
  Button,
  Alert,
  Heading,
  Text,
  Center,
  NotFoundState,
  Icons,
} from '../design-system'
import { PageLoader } from '../design-system/components/Loader'
import clsx from 'clsx'

type BookingState = 'select_slot' | 'pending_payment' | 'paid' | 'cancelled' | 'expired'

// Отображение таймера обратного отсчёта
function CountdownTimer({ expiresAt, onExpire }: { expiresAt: string; onExpire: () => void }) {
  const countdown = useCountdown(expiresAt)

  if (countdown.isExpired) {
    onExpire()
    return null
  }

  const isUrgent = countdown.totalSeconds <= 60

  return (
    <div className={clsx(
      'px-4 py-3 transition-colors',
      isUrgent ? 'bg-error-50' : 'bg-warning-50'
    )}>
      <Inline gap={3} align="center">
        <div className={clsx(
          'w-10 h-10 rounded-full flex items-center justify-center',
          isUrgent ? 'bg-error-100' : 'bg-warning-100'
        )}>
          <Icons.Clock size="md" className={isUrgent ? 'text-error-600' : 'text-warning-600'} />
        </div>
        <div>
          <Text weight="semibold" className={isUrgent ? 'text-error-700' : 'text-warning-700'}>
            Осталось времени: {countdown.formatted}
          </Text>
          <Text size="sm" className={isUrgent ? 'text-error-600' : 'text-warning-600'}>
            Завершите оплату до истечения времени
          </Text>
        </div>
      </Inline>
    </div>
  )
}

// Состояние успешного бронирования
function BookingSuccess({ 
  booking, 
  onViewBookings, 
  onBrowseMore 
}: { 
  booking: Booking
  onViewBookings: () => void
  onBrowseMore: () => void
}) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-500 to-primary-600 flex flex-col items-center justify-center px-4 text-white">
      <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mb-8 animate-scale-in shadow-xl">
        <Icons.CheckCircle size="xl" className="w-14 h-14 text-primary-500" />
      </div>

      <Heading level="h1" size="2xl" className="text-white text-center animate-fade-in">
        Бронирование подтверждено!
      </Heading>

      <Text className="text-white/80 text-center mt-2 animate-fade-in">
        Ваша консультация успешно забронирована.
      </Text>

      {booking.slot && (
        <Card variant="elevated" className="w-full max-w-sm mt-8 bg-white/10 border-none animate-slide-up">
          <div className="text-center text-white">
            <Text size="sm" className="text-white/60">Дата консультации</Text>
            <Text weight="semibold" size="lg" className="text-white">
              {format(parseISO(booking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
            </Text>
            <Text size="xl" weight="bold" className="text-white">
              {format(parseISO(booking.slot.start_at), 'HH:mm')}
            </Text>
          </div>

          <div className="mt-4 pt-4 border-t border-white/10 text-center">
            <Text size="sm" className="text-white/60">Сумма</Text>
            <Text size="xl" weight="bold" className="text-white">
              {booking.price_rub.toLocaleString('ru-RU')} ₽
            </Text>
          </div>
        </Card>
      )}

      <Stack gap={3} className="w-full max-w-sm mt-8 animate-slide-up">
        <Button
          onClick={onViewBookings}
          variant="secondary"
          fullWidth
          className="bg-white text-primary-600 hover:bg-white/90"
        >
          Мои бронирования
        </Button>
        <Button
          onClick={onBrowseMore}
          variant="ghost"
          fullWidth
          className="text-white bg-white/10 hover:bg-white/20"
        >
          Найти другого специалиста
        </Button>
      </Stack>
    </div>
  )
}

// Состояние истёкшего бронирования
function BookingExpired({ onRetry }: { onRetry: () => void }) {
  return (
    <Center fullHeight className="bg-bg-secondary px-4">
      <div className="text-center">
        <div className="w-20 h-20 bg-warning-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Icons.Clock size="xl" className="text-warning-600" />
        </div>
        <Heading size="lg">Время истекло</Heading>
        <Text color="secondary" className="mt-2 max-w-xs mx-auto">
          Время бронирования истекло. Слот мог быть занят другим клиентом.
        </Text>
        <Button onClick={onRetry} className="mt-6">
          Выбрать другое время
        </Button>
      </div>
    </Center>
  )
}

// Состояние отменённого бронирования
function BookingCancelled({ onRetry }: { onRetry: () => void }) {
  return (
    <Center fullHeight className="bg-bg-secondary px-4">
      <div className="text-center">
        <div className="w-20 h-20 bg-neutral-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Icons.Close size="xl" className="text-neutral-400" />
        </div>
        <Heading size="lg">Бронирование отменено</Heading>
        <Text color="secondary" className="mt-2">
          Ваше бронирование было отменено.
        </Text>
        <Button onClick={onRetry} className="mt-6">
          Забронировать снова
        </Button>
      </div>
    </Center>
  )
}

export default function BookingPage() {
  const { nutritionistId, serviceId } = useParams<{
    nutritionistId: string
    serviceId: string
  }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null)
  const [bookingState, setBookingState] = useState<BookingState>('select_slot')
  const [currentBooking, setCurrentBooking] = useState<Booking | null>(null)
  const [paymentInfo, setPaymentInfo] = useState<PaymentIntent | null>(null)
  const [error, setError] = useState<string | null>(null)

  const holdExpiresAt = currentBooking?.slot?.hold_expires_at

  const { data: nutritionistData, isLoading: loadingNutritionist } = useQuery({
    queryKey: ['nutritionist', nutritionistId],
    queryFn: () => publicApi.getNutritionist(nutritionistId!),
    enabled: !!nutritionistId,
  })

  const { data: servicesData, isLoading: loadingServices } = useQuery({
    queryKey: ['services', nutritionistId],
    queryFn: () => publicApi.getServices(nutritionistId!),
    enabled: !!nutritionistId,
  })

  const { data: slotsData, isLoading: loadingSlots, refetch: refetchSlots } = useQuery({
    queryKey: ['slots', nutritionistId, serviceId],
    queryFn: () => publicApi.getSlots(nutritionistId!, serviceId),
    enabled: !!nutritionistId,
  })

  // Мутация создания бронирования
  const bookingMutation = useMutation({
    mutationFn: () => bookingApi.createBooking(serviceId!, selectedSlot!.id),
    onSuccess: (data: { booking: Booking; payment: PaymentIntent }) => {
      setCurrentBooking(data.booking)
      setPaymentInfo(data.payment)
      setBookingState('pending_payment')
      setError(null)
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')
    },
    onError: (err: Error & { response?: { status?: number; data?: { error?: string } } }) => {
      const errorMessage = err.response?.data?.error || 'Не удалось создать бронирование'
      if (err.response?.status === 409) {
        setError('Этот слот уже заняли. Пожалуйста, выберите другой.')
        refetchSlots()
      } else {
        setError(errorMessage)
      }
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error')
    },
  })

  // Мутация оплаты
  const simulatePaymentMutation = useMutation({
    mutationFn: async (): Promise<{ booking: Booking }> => {
      const result = await paymentApi.simulatePayment(currentBooking!.id)
      if (!result.booking) {
        throw new Error('Оплата прошла, но данные бронирования не получены')
      }
      return { booking: result.booking }
    },
    onSuccess: (data) => {
      setCurrentBooking(data.booking)
      setBookingState('paid')
      queryClient.invalidateQueries({ queryKey: ['my-bookings'] })
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
    },
    onError: (err: Error & { response?: { data?: { error?: string } } }) => {
      const errorMessage = err.response?.data?.error || 'Ошибка оплаты'
      if (errorMessage.toLowerCase().includes('expired')) {
        setBookingState('expired')
      }
      setError(errorMessage)
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error')
    },
  })

  const createPaymentLinkMutation = useMutation({
    mutationFn: async () => {
      if (paymentInfo) {
        return paymentInfo
      }
      return paymentApi.createPaymentIntent(currentBooking!.id)
    },
    onSuccess: (intent) => {
      setPaymentInfo(intent)
      if (window.Telegram?.WebApp?.openLink) {
        window.Telegram.WebApp.openLink(intent.payment_url)
      } else {
        window.location.href = intent.payment_url
      }
    },
    onError: (err: Error & { response?: { data?: { error?: string } } }) => {
      setError(err.response?.data?.error || 'Не удалось получить ссылку на оплату')
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error')
    },
  })

  // Мутация отмены бронирования
  const cancelMutation = useMutation({
    mutationFn: () => bookingApi.cancelBooking(currentBooking!.id, 'Отменено пользователем'),
    onSuccess: (data: { booking: Booking; message: string }) => {
      setCurrentBooking(data.booking)
      setBookingState('cancelled')
      refetchSlots()
      queryClient.invalidateQueries({ queryKey: ['my-bookings'] })
    },
    onError: (err: Error & { response?: { data?: { error?: string } } }) => {
      setError(err.response?.data?.error || 'Не удалось отменить бронирование')
    },
  })

  if (loadingNutritionist || loadingServices || loadingSlots) {
    return <PageLoader text="Загрузка доступных слотов..." />
  }

  const nutritionist = nutritionistData?.nutritionist
  const service = servicesData?.services?.find((s: Service) => s.id === serviceId)
  const slots = slotsData?.slots || []

  if (!nutritionist || !service) {
    return (
      <PageContainer>
        <Center fullHeight>
          <NotFoundState onBack={() => navigate(-1)} />
        </Center>
      </PageContainer>
    )
  }

  const handleBook = () => {
    if (selectedSlot) {
      setError(null)
      bookingMutation.mutate()
    }
  }

  const handlePayment = () => {
    if (paymentInfo?.provider === 'mock') {
      simulatePaymentMutation.mutate()
      return
    }
    createPaymentLinkMutation.mutate()
  }

  const handleCancel = () => {
    cancelMutation.mutate()
  }

  const handleBookAnother = () => {
    setSelectedSlot(null)
    setCurrentBooking(null)
    setPaymentInfo(null)
    setBookingState('select_slot')
    setError(null)
    refetchSlots()
  }

  // Рендер различных состояний
  if (bookingState === 'paid' && currentBooking) {
    return (
      <BookingSuccess
        booking={currentBooking}
        onViewBookings={() => navigate('/my-bookings')}
        onBrowseMore={() => navigate('/results')}
      />
    )
  }

  if (bookingState === 'expired') {
    return <BookingExpired onRetry={handleBookAnother} />
  }

  if (bookingState === 'cancelled') {
    return <BookingCancelled onRetry={handleBookAnother} />
  }

  if (bookingState === 'pending_payment' && currentBooking) {
    return (
      <PageContainer background="primary">
        <Header sticky bordered>
          <Heading level="h1" size="lg">Оплата</Heading>
          <Text size="sm" color="secondary" className="mt-0.5">
            Завершите бронирование
          </Text>
        </Header>

        {/* Таймер обратного отсчёта */}
        {holdExpiresAt && (
          <CountdownTimer
            expiresAt={holdExpiresAt}
            onExpire={() => setBookingState('expired')}
          />
        )}

        {/* Детали бронирования */}
        <Section>
          <Card padding="lg">
            <Heading level="h2" size="md" className="mb-4">Детали бронирования</Heading>
            
            <Stack gap={3}>
              <Inline justify="between">
                <Text color="secondary">Услуга</Text>
                <Text weight="medium">{currentBooking.service?.title}</Text>
              </Inline>
              <Inline justify="between">
                <Text color="secondary">Нутрициолог</Text>
                <Text weight="medium">{nutritionist.profile?.full_name}</Text>
              </Inline>
              {currentBooking.slot && (
                <>
                  <Inline justify="between">
                    <Text color="secondary">Дата</Text>
                    <Text weight="medium">
                      {format(parseISO(currentBooking.slot.start_at), 'EEEE, d MMMM', { locale: ru })}
                    </Text>
                  </Inline>
                  <Inline justify="between">
                    <Text color="secondary">Время</Text>
                    <Text weight="medium">
                      {format(parseISO(currentBooking.slot.start_at), 'HH:mm')}
                    </Text>
                  </Inline>
                </>
              )}
              <div className="pt-3 border-t border-border-light">
                <Inline justify="between">
                  <Text weight="medium">Итого</Text>
                  <Text weight="bold" className="text-primary-600 text-lg">
                    {currentBooking.price_rub.toLocaleString('ru-RU')} ₽
                  </Text>
                </Inline>
              </div>
            </Stack>
          </Card>
        </Section>

        {/* Статус */}
        <Section spacing="sm">
          <Badge variant="warning" dot animated size="md">
            Ожидает оплаты
          </Badge>
        </Section>

        {/* Отображение ошибки */}
        {error && (
          <Section spacing="sm">
            <Alert variant="error">{error}</Alert>
          </Section>
        )}

        {/* Действия */}
        <Footer bordered>
          <Stack gap={3}>
            <Button
              onClick={handlePayment}
              loading={simulatePaymentMutation.isPending || createPaymentLinkMutation.isPending}
              fullWidth
              size="lg"
            >
              {paymentInfo?.provider === 'mock'
                ? 'Симулировать оплату'
                : `Оплатить ${currentBooking.price_rub.toLocaleString('ru-RU')} ₽`}
            </Button>
            <Button
              variant="ghost"
              onClick={handleCancel}
              loading={cancelMutation.isPending}
              fullWidth
              className="text-text-secondary"
            >
              Отменить
            </Button>
          </Stack>
        </Footer>
      </PageContainer>
    )
  }

  // Состояние по умолчанию: выбор слота
  return (
    <PageContainer background="primary">
      <Header sticky bordered>
        <Heading level="h1" size="lg">Бронирование</Heading>
        <Text size="sm" color="secondary" className="mt-0.5">
          Выберите удобное время
        </Text>
      </Header>

      {/* Информация об услуге */}
      <div className="px-4 py-4 bg-bg-secondary border-b border-border-light">
        <Inline gap={3} align="center">
          {nutritionist.profile?.photo_url ? (
            <img
              src={nutritionist.profile.photo_url}
              alt={nutritionist.profile.full_name}
              className="w-12 h-12 rounded-xl object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-primary-500 flex items-center justify-center">
              <span className="text-white font-bold">
                {nutritionist.profile?.full_name?.charAt(0) || 'Н'}
              </span>
            </div>
          )}
          <div className="flex-1">
            <Text weight="medium">{service.title}</Text>
            <Text size="sm" color="secondary">
              {nutritionist.profile?.full_name} • {service.duration_minutes} мин
            </Text>
          </div>
          <Text weight="bold" className="text-primary-600">
            {service.price_rub.toLocaleString('ru-RU')} ₽
          </Text>
        </Inline>
      </div>

      {/* Отображение ошибки */}
      {error && (
        <Section spacing="sm">
          <Alert variant="error">{error}</Alert>
        </Section>
      )}

      {/* Выбор слота */}
      <Section className="pb-40">
        <SlotPicker
          slots={slots}
          selectedSlot={selectedSlot}
          onSelectSlot={setSelectedSlot}
        />
      </Section>

      {/* Нижняя секция */}
      <Footer bordered>
        {selectedSlot && (
          <div className="mb-3 px-3 py-2 bg-primary-50 rounded-lg border border-primary-100">
            <Text size="sm" className="text-primary-800">
              <span className="font-medium">Выбрано:</span>{' '}
              {format(parseISO(selectedSlot.start_at), 'EEEE, d MMMM', { locale: ru })} в{' '}
              {format(parseISO(selectedSlot.start_at), 'HH:mm')}
            </Text>
          </div>
        )}
        <Button
          onClick={handleBook}
          disabled={!selectedSlot}
          loading={bookingMutation.isPending}
          fullWidth
          size="lg"
        >
          {selectedSlot
            ? `Подтвердить бронирование • ${service.price_rub.toLocaleString('ru-RU')} ₽`
            : 'Выберите время'}
        </Button>
      </Footer>
    </PageContainer>
  )
}
