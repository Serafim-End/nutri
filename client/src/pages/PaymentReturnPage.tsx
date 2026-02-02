import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { bookingApi, paymentApi } from '../lib/api'
import type { Booking, Payment } from '../types'
import MoscowTimeNote from '../components/MoscowTimeNote'
import { formatMoscowDateLong, formatMoscowDateTime, formatMoscowTime } from '../utils/moscowTime'
import {
  Stack,
  Card,
  Button,
  Heading,
  Text,
  Icons,
  Alert,
} from '../design-system'

type Mode = 'success' | 'fail'
type Status = 'checking' | 'success' | 'failed' | 'pending' | 'error'

const formatDate = (value?: string | null) => formatMoscowDateTime(value)

export default function PaymentReturnPage({ mode }: { mode: Mode }) {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<Status>(mode === 'success' ? 'checking' : 'failed')
  const [booking, setBooking] = useState<Booking | null>(null)
  const [payment, setPayment] = useState<Payment | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const bookingId = useMemo(() => {
    return searchParams.get('order_id') || searchParams.get('booking_id')
  }, [searchParams])

  useEffect(() => {
    if (!bookingId) {
      setStatus('error')
      setError('Не удалось определить бронирование')
      return
    }

    bookingApi.getBooking(bookingId)
      .then((data) => setBooking(data.booking))
      .catch(() => setBooking(null))
  }, [bookingId])

  useEffect(() => {
    if (mode !== 'success' || !bookingId) return

    let attempts = 0
    const maxAttempts = 20
    const interval = setInterval(async () => {
      attempts += 1
      try {
        const data = await paymentApi.getPaymentStatus(bookingId)
        const currentPayment = data.payment
        setPayment(currentPayment)
        if (currentPayment.status === 'succeeded') {
          setStatus('success')
          window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
          clearInterval(interval)
          return
        }
        if (['failed', 'refunded'].includes(currentPayment.status)) {
          setStatus('failed')
          clearInterval(interval)
          return
        }
        setStatus('pending')
      } catch {
        setStatus('pending')
      }

      if (attempts >= maxAttempts) {
        setStatus('pending')
        clearInterval(interval)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [bookingId, mode])

  const handleRetry = async () => {
    if (!bookingId) return
    try {
      const intent = await paymentApi.createPaymentIntent(bookingId)
      if (window.Telegram?.WebApp?.openLink) {
        window.Telegram.WebApp.openLink(intent.payment_url)
      } else {
        window.location.href = intent.payment_url
      }
    } catch {
      setError('Не удалось получить ссылку на оплату')
    }
  }

  const handleRefresh = async () => {
    if (!bookingId) return
    setIsRefreshing(true)
    setError(null)
    try {
      const [bookingData, paymentData] = await Promise.all([
        bookingApi.getBooking(bookingId),
        paymentApi.getPaymentStatus(bookingId).catch(() => null),
      ])

      if (bookingData?.booking) {
        setBooking(bookingData.booking)
      }

      if (paymentData?.payment) {
        const currentPayment = paymentData.payment
        setPayment(currentPayment)
        if (currentPayment.status === 'succeeded') {
          setStatus('success')
        } else if (['failed', 'refunded'].includes(currentPayment.status)) {
          setStatus('failed')
        } else {
          setStatus('pending')
        }
      } else {
        setStatus('pending')
      }
    } catch {
      setError('Не удалось обновить статус')
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleViewBookings = () => {
    navigate('/my-bookings')
  }

  const title = status === 'success'
    ? 'Оплата подтверждена!'
    : mode === 'fail'
      ? 'Оплата не прошла'
      : 'Проверяем оплату'

  const subtitle = status === 'success'
    ? 'Ваше бронирование подтверждено.'
    : status === 'pending'
      ? 'Мы ещё проверяем платёж. Это может занять до минуты.'
      : 'Если оплата не прошла, попробуйте снова.'

  const canRetry = status === 'failed' || mode === 'fail'
  const canRefresh = status !== 'success'

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-500 to-primary-600 flex flex-col items-center justify-center px-4 text-white">
      <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mb-8 animate-scale-in shadow-xl">
        {status === 'success' ? (
          <Icons.CheckCircle size="xl" className="w-14 h-14 text-primary-500" />
        ) : status === 'checking' ? (
          <Icons.Clock size="xl" className="w-14 h-14 text-primary-500" />
        ) : (
          <Icons.Close size="xl" className="w-14 h-14 text-primary-500" />
        )}
      </div>

      <Heading level="h1" size="2xl" className="text-white text-center animate-fade-in">
        {title}
      </Heading>

      <Text className="text-white/80 text-center mt-2 animate-fade-in">
        {subtitle}
      </Text>

      {error && (
        <Alert variant="error" className="mt-6">
          {error}
        </Alert>
      )}

      {booking && (
        <Card
          variant="elevated"
          padding="lg"
          className="w-full max-w-sm mt-8 bg-white/10 border-none animate-slide-up"
        >
          {booking.slot && (
            <div className="text-center text-white">
              <Text size="sm" className="text-white/60">Дата консультации</Text>
              <Text weight="semibold" size="lg" className="text-white">
                {formatMoscowDateLong(booking.slot.start_at)}
              </Text>
              <Text size="xl" weight="bold" className="text-white">
                {formatMoscowTime(booking.slot.start_at)}
              </Text>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-white/10 text-center">
            <Text size="sm" className="text-white/60">Сумма</Text>
            <Text size="xl" weight="bold" className="text-white">
              {booking.price_rub.toLocaleString('ru-RU')} ₽
            </Text>
          </div>
          {payment && (
            <div className="mt-3 text-xs text-white/70 text-center">
              Статус: {payment.status} · {formatDate(payment.created_at)}
            </div>
          )}
          <MoscowTimeNote className="mt-3 text-white/70" align="center" />
        </Card>
      )}

      <Stack gap={3} className="w-full max-w-sm mt-8 animate-slide-up">
        {canRefresh && (
          <Button
            onClick={handleRefresh}
            loading={isRefreshing}
            variant="secondary"
            fullWidth
            className="bg-white text-primary-600 hover:bg-white/90"
          >
            Обновить статус
          </Button>
        )}

        {canRetry && (
          <Button
            onClick={handleRetry}
            variant="secondary"
            fullWidth
            className="bg-white text-primary-600 hover:bg-white/90"
          >
            Оплатить снова
          </Button>
        )}

        <Button
          onClick={handleViewBookings}
          variant="ghost"
          fullWidth
          className="text-white bg-white/10 hover:bg-white/20"
        >
          Мои бронирования
        </Button>
      </Stack>

      <Text size="sm" className="mt-8 text-white/60 text-center max-w-xs animate-fade-in">
        Если оплата уже прошла, статус обновится автоматически.
      </Text>
    </div>
  )
}
