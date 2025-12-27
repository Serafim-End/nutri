import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { publicApi, bookingApi } from '../lib/api'
import SlotPicker from '../components/SlotPicker'
import LoadingScreen from '../components/LoadingScreen'
import type { AvailabilitySlot } from '../types'

export default function BookingPage() {
  const { nutritionistId, serviceId } = useParams<{
    nutritionistId: string
    serviceId: string
  }>()
  const navigate = useNavigate()
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null)

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

  const { data: slotsData, isLoading: loadingSlots } = useQuery({
    queryKey: ['slots', nutritionistId, serviceId],
    queryFn: () => publicApi.getSlots(nutritionistId!, serviceId),
    enabled: !!nutritionistId,
  })

  const bookingMutation = useMutation({
    mutationFn: () => bookingApi.createBooking(serviceId!, selectedSlot!.id),
    onSuccess: (data) => {
      // In a real app, you'd redirect to payment or show payment modal
      // For now, simulate successful payment
      navigate('/payment-success', {
        state: { booking: data.booking, payment: data.payment },
      })
    },
  })

  if (loadingNutritionist || loadingServices || loadingSlots) {
    return <LoadingScreen />
  }

  const nutritionist = nutritionistData?.nutritionist
  const service = servicesData?.services?.find((s) => s.id === serviceId)
  const slots = slotsData?.slots || []

  if (!nutritionist || !service) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-gray-500">Service not found.</p>
        </div>
      </div>
    )
  }

  const handleBook = () => {
    if (selectedSlot) {
      // Haptic feedback
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')
      bookingMutation.mutate()
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="px-4 pt-6 pb-4 border-b border-gray-100">
        <h1 className="text-xl font-display font-bold text-gray-900">
          Book Appointment
        </h1>
        <p className="text-gray-500 mt-1">
          Select a convenient time slot
        </p>
      </div>

      {/* Service summary */}
      <div className="px-4 py-4 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center gap-3">
          {nutritionist.profile?.photo_url ? (
            <img
              src={nutritionist.profile.photo_url}
              alt={nutritionist.profile.full_name}
              className="w-12 h-12 rounded-xl object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-primary-500 flex items-center justify-center">
              <span className="text-white font-bold">
                {nutritionist.profile?.full_name?.charAt(0) || 'N'}
              </span>
            </div>
          )}
          <div className="flex-1">
            <p className="font-medium text-gray-900">{service.title}</p>
            <p className="text-sm text-gray-500">
              {nutritionist.profile?.full_name} • {service.duration_minutes} min
            </p>
          </div>
          <div className="text-right">
            <p className="font-bold text-primary-600">
              {service.price_rub.toLocaleString('ru-RU')} ₽
            </p>
          </div>
        </div>
      </div>

      {/* Slot picker */}
      <div className="px-4 py-6 pb-32">
        <SlotPicker
          slots={slots}
          selectedSlot={selectedSlot}
          onSelectSlot={setSelectedSlot}
        />
      </div>

      {/* Bottom section */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 safe-area-bottom">
        {selectedSlot && (
          <div className="px-4 py-3 bg-primary-50 border-b border-primary-100">
            <p className="text-sm text-primary-800">
              <span className="font-medium">Selected:</span>{' '}
              {format(parseISO(selectedSlot.start_at), 'EEEE, d MMMM', { locale: ru })} at{' '}
              {format(parseISO(selectedSlot.start_at), 'HH:mm')}
            </p>
          </div>
        )}
        <div className="p-4">
          <button
            onClick={handleBook}
            disabled={!selectedSlot || bookingMutation.isPending}
            className="btn-primary w-full"
          >
            {bookingMutation.isPending
              ? 'Booking...'
              : selectedSlot
              ? `Confirm Booking • ${service.price_rub.toLocaleString('ru-RU')} ₽`
              : 'Select a time slot'}
          </button>
        </div>

        {bookingMutation.isError && (
          <div className="px-4 pb-4">
            <p className="text-sm text-red-500 text-center">
              Failed to create booking. Please try again.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}


