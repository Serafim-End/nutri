import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { Nutritionist, NutritionistDocument, AdminService, WorkingHoursTemplate } from '@/types'
import { format } from 'date-fns'
import clsx from 'clsx'

type ActionType = 'approve' | 'reject' | 'needs_update' | 'disable' | 'activate' | null

const statusColors: Record<string, string> = {
  pending: 'bg-warning-500/10 text-warning-400 border-warning-500/20',
  approved: 'bg-success-500/10 text-success-400 border-success-500/20',
  rejected: 'bg-error-500/10 text-error-400 border-error-500/20',
  needs_update: 'bg-accent-500/10 text-accent-400 border-accent-500/20',
}

const docStatusColors: Record<string, string> = {
  uploaded: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  accepted: 'bg-success-500/10 text-success-400 border-success-500/20',
  rejected: 'bg-error-500/10 text-error-400 border-error-500/20',
}

const DAYS: Array<{ id: string; label: string }> = [
  { id: '0', label: 'Пн' },
  { id: '1', label: 'Вт' },
  { id: '2', label: 'Ср' },
  { id: '3', label: 'Чт' },
  { id: '4', label: 'Пт' },
  { id: '5', label: 'Сб' },
  { id: '6', label: 'Вс' },
]

const formatRanges = (ranges: Array<{ start: string; end: string }>) => {
  if (!ranges || ranges.length === 0) return ''
  return ranges.map((r) => `${r.start}-${r.end}`).join(', ')
}

const parseRanges = (value: string) => {
  if (!value.trim()) return []
  return value
    .split(',')
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .map((chunk) => {
      const normalized = chunk.replace('–', '-')
      const [start, end] = normalized.split('-').map((part) => part.trim())
      if (!start || !end) {
        throw new Error(`Invalid range: ${chunk}`)
      }
      return { start, end }
    })
}

export function NutritionistDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [activeAction, setActiveAction] = useState<ActionType>(null)
  const [actionNote, setActionNote] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [nameDraft, setNameDraft] = useState('')
  const [showPhotoUploader, setShowPhotoUploader] = useState(false)
  const [bioDraft, setBioDraft] = useState('')
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false)
  const [isDragActive, setIsDragActive] = useState(false)
  const [editingServiceId, setEditingServiceId] = useState<string | null>(null)
  const [serviceDraft, setServiceDraft] = useState<Partial<AdminService>>({})
  const [newService, setNewService] = useState({
    title: '',
    description: '',
    duration_minutes: 60,
    price_rub: 0,
    is_active: true,
  })
  const [scheduleInputs, setScheduleInputs] = useState<Record<string, string>>({})
  const [scheduleError, setScheduleError] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'nutritionist', id],
    queryFn: () => adminApi.getNutritionist(id!),
    enabled: !!id,
  })

  const nutritionist: Nutritionist | null = data?.nutritionist || null
  const documents: NutritionistDocument[] = data?.documents || []

  const { data: servicesData } = useQuery({
    queryKey: ['admin', 'nutritionist', id, 'services'],
    queryFn: () => adminApi.getNutritionistServices(id!),
    enabled: !!id,
  })

  const services: AdminService[] = servicesData?.services || []

  const { data: workingHoursData } = useQuery({
    queryKey: ['admin', 'nutritionist', id, 'working-hours'],
    queryFn: () => adminApi.getWorkingHoursTemplate(id!),
    enabled: !!id,
  })

  const workingHours: WorkingHoursTemplate | null = workingHoursData?.template || null

  useEffect(() => {
    if (nutritionist) {
      setNameDraft(nutritionist.full_name || '')
      setBioDraft(nutritionist.bio || '')
    }
  }, [nutritionist])

  useEffect(() => {
    if (workingHours?.weekly_schedule) {
      const inputs: Record<string, string> = {}
      DAYS.forEach((day) => {
        const ranges = workingHours.weekly_schedule[day.id] || []
        inputs[day.id] = formatRanges(ranges)
      })
      setScheduleInputs(inputs)
    }
  }, [workingHours])

  const updateBioMutation = useMutation({
    mutationFn: (bio: string | null) => adminApi.updateNutritionistBio(id!, bio),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
    },
  })

  const updateProfileMutation = useMutation({
    mutationFn: (payload: { full_name: string }) =>
      adminApi.updateNutritionistProfile(id!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionists'] })
    },
  })

  const activateMutation = useMutation({
    mutationFn: () => adminApi.activateNutritionist(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionists'] })
      setActiveAction(null)
    },
  })

  const uploadPhotoMutation = useMutation({
    mutationFn: (file: File) => adminApi.uploadNutritionistPhoto(id!, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionists'] })
    },
    onError: () => {
      setUploadError('Failed to upload photo')
    },
    onSettled: () => {
      setIsUploadingPhoto(false)
      setIsDragActive(false)
    },
  })

  const handlePhotoFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setUploadError('Only image files are supported')
      return
    }
    setUploadError(null)
    setIsUploadingPhoto(true)
    uploadPhotoMutation.mutate(file)
  }

  const createServiceMutation = useMutation({
    mutationFn: () =>
      adminApi.createNutritionistService(id!, {
        title: newService.title,
        description: newService.description || null,
        duration_minutes: newService.duration_minutes,
        price_rub: newService.price_rub,
        is_active: newService.is_active,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id, 'services'] })
      setNewService({
        title: '',
        description: '',
        duration_minutes: 60,
        price_rub: 0,
        is_active: true,
      })
    },
  })

  const updateServiceMutation = useMutation({
    mutationFn: () =>
      adminApi.updateNutritionistService(id!, editingServiceId!, {
        title: serviceDraft.title,
        description: serviceDraft.description || null,
        duration_minutes: serviceDraft.duration_minutes,
        price_rub: serviceDraft.price_rub,
        is_active: serviceDraft.is_active,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id, 'services'] })
      setEditingServiceId(null)
      setServiceDraft({})
    },
  })

  const deleteServiceMutation = useMutation({
    mutationFn: (serviceId: string) => adminApi.deleteNutritionistService(id!, serviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id, 'services'] })
    },
  })

  const updateScheduleMutation = useMutation({
    mutationFn: (weeklySchedule: Record<string, Array<{ start: string; end: string }>>) =>
      adminApi.updateWorkingHoursTemplate(id!, weeklySchedule),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id, 'working-hours'] })
    },
  })

  const approveMutation = useMutation({
    mutationFn: (note?: string) => adminApi.approveNutritionist(id!, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionists'] })
      setActiveAction(null)
      setActionNote('')
    },
  })

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => adminApi.rejectNutritionist(id!, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionists'] })
      setActiveAction(null)
      setActionNote('')
    },
  })

  const requestUpdateMutation = useMutation({
    mutationFn: (notes: string) => adminApi.requestUpdate(id!, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionists'] })
      setActiveAction(null)
      setActionNote('')
    },
  })

  const disableMutation = useMutation({
    mutationFn: () => adminApi.disableNutritionist(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionist', id] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'nutritionists'] })
      setActiveAction(null)
      setActionNote('')
    },
  })

  const handleAction = async () => {
    if (!activeAction) return
    setIsSubmitting(true)

    try {
      switch (activeAction) {
        case 'approve':
          await approveMutation.mutateAsync(actionNote || undefined)
          break
        case 'reject':
          if (!actionNote.trim()) return
          await rejectMutation.mutateAsync(actionNote)
          break
        case 'needs_update':
          if (!actionNote.trim()) return
          await requestUpdateMutation.mutateAsync(actionNote)
          break
        case 'disable':
          await disableMutation.mutateAsync()
          break
        case 'activate':
          await activateMutation.mutateAsync()
          break
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDownloadDocument = async (doc: NutritionistDocument) => {
    try {
      const { url } = await adminApi.getDocumentUrl(doc.id)
      window.open(url, '_blank')
    } catch {
      // Fallback: try direct file_path
      window.open(doc.file_path, '_blank')
    }
  }

  const canModerate = nutritionist?.verification_status === 'pending' || nutritionist?.verification_status === 'needs_update'
  const canDisable = nutritionist?.verification_status === 'approved' && nutritionist?.is_active
  const canActivate = nutritionist?.verification_status === 'approved' && !nutritionist?.is_active
  const trimmedName = nameDraft.trim()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !nutritionist) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-400">
        <svg className="w-16 h-16 mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-lg font-medium mb-2">Nutritionist not found</p>
        <button
          onClick={() => navigate('/nutritionists')}
          className="text-accent-400 hover:text-accent-300 transition-colors"
        >
          ← Back to list
        </button>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Back button */}
      <button
        onClick={() => navigate('/nutritionists')}
        className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Nutritionists
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-2 rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
          <div className="p-6 border-b border-slate-800/50">
            <div className="flex items-start gap-4">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center flex-shrink-0">
                {nutritionist.profile?.photo_url ? (
                  <img
                    src={nutritionist.profile.photo_url}
                    alt=""
                    className="w-20 h-20 rounded-2xl object-cover"
                  />
                ) : (
                  <span className="text-2xl font-bold text-slate-300">
                    {nutritionist.full_name?.charAt(0).toUpperCase() || '?'}
                  </span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="font-display text-2xl font-bold text-white truncate">
                    {nutritionist.full_name}
                  </h1>
                  <span
                    className={clsx(
                      'px-2.5 py-1 text-xs font-medium rounded-lg border flex-shrink-0',
                      statusColors[nutritionist.verification_status] || statusColors.pending
                    )}
                  >
                    {nutritionist.verification_status.replace('_', ' ')}
                  </span>
                  <button
                    onClick={() => navigate(`/reviews?nutritionist_id=${nutritionist.nutritionist_id}`)}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800/50 text-slate-200 hover:bg-slate-800"
                  >
                    Reviews
                  </button>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-400">
                  <span>
                    {nutritionist.years_experience ? `${nutritionist.years_experience} years of experience` : ''}
                    {nutritionist.years_experience && nutritionist.currency && nutritionist.hourly_rate ? ' • ' : ''}
                    {nutritionist.currency && nutritionist.hourly_rate ? `${nutritionist.currency} ${nutritionist.hourly_rate}/hr` : ''}
                  </span>
                  {nutritionist.profile?.telegram_username && (
                    <a
                      href={`https://t.me/${nutritionist.profile.telegram_username}`}
                      className="inline-flex items-center gap-1 text-xs text-accent-400 hover:text-accent-300"
                      target="_blank"
                      rel="noreferrer"
                    >
                      @{nutritionist.profile.telegram_username}
                    </a>
                  )}
                </div>
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => {
                      setShowPhotoUploader((prev) => !prev)
                      setUploadError(null)
                    }}
                    className="inline-flex items-center gap-2 rounded-lg bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-800"
                  >
                    Change photo for clients
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Profile */}
          <div className="p-6 border-b border-slate-800/50">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Profile</h3>
                <button
                  onClick={() =>
                    updateProfileMutation.mutate({
                      full_name: trimmedName,
                    })
                  }
                  disabled={!trimmedName || updateProfileMutation.isPending}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800/50 text-slate-200 hover:bg-slate-800 disabled:opacity-50"
                >
                  Save
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="block text-sm text-slate-300">
                  Name
                  <input
                    value={nameDraft}
                    onChange={(e) => setNameDraft(e.target.value)}
                    placeholder="Nutritionist name"
                    className="mt-1 w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50"
                  />
                </label>
            </div>
            {showPhotoUploader && (
              <div className="mt-4">
                <div
                  className={clsx(
                    'flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed p-4 text-sm transition-colors',
                    isDragActive
                      ? 'border-accent-400 bg-accent-500/10 text-accent-200'
                      : 'border-slate-700/50 bg-slate-900/30 text-slate-400'
                  )}
                  onDragOver={(event) => {
                    event.preventDefault()
                    setIsDragActive(true)
                  }}
                  onDragLeave={() => setIsDragActive(false)}
                  onDrop={(event) => {
                    event.preventDefault()
                    const file = event.dataTransfer.files?.[0]
                    if (file) handlePhotoFile(file)
                  }}
                >
                  <span className="text-xs uppercase tracking-wide text-slate-500">
                    Drag & Drop Photo
                  </span>
                  <span>or</span>
                  <label className="cursor-pointer rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700">
                    Upload image
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(event) => {
                        const file = event.target.files?.[0]
                        if (file) handlePhotoFile(file)
                      }}
                    />
                  </label>
                  {isUploadingPhoto && (
                    <span className="text-xs text-slate-500">Uploading...</span>
                  )}
                  {uploadError && (
                    <span className="text-xs text-error-400">{uploadError}</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Bio */}
          <div className="p-6 border-b border-slate-800/50">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Bio</h3>
              <button
                onClick={() => updateBioMutation.mutate(bioDraft || null)}
                disabled={updateBioMutation.isPending}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800/50 text-slate-200 hover:bg-slate-800 disabled:opacity-50"
              >
                Save
              </button>
            </div>
            <textarea
              value={bioDraft}
              onChange={(e) => setBioDraft(e.target.value)}
              placeholder="Add nutritionist bio..."
              className="w-full min-h-[120px] px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 resize-none"
            />
          </div>

          {/* Specializations */}
          <div className="p-6 border-b border-slate-800/50">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Specializations</h3>
            <div className="flex flex-wrap gap-2">
              {nutritionist.specializations?.length ? (
                nutritionist.specializations.map((spec) => (
                  <span
                    key={spec}
                    className="px-3 py-1.5 text-sm rounded-lg bg-slate-800 text-slate-200 border border-slate-700/50"
                  >
                    {spec}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic">No specializations listed</span>
              )}
            </div>
          </div>

          {/* Languages */}
          <div className="p-6 border-b border-slate-800/50">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Languages</h3>
            <div className="flex flex-wrap gap-2">
              {nutritionist.languages?.length ? (
                nutritionist.languages.map((lang) => (
                  <span
                    key={lang}
                    className="px-3 py-1.5 text-sm rounded-lg bg-slate-800/50 text-slate-300 border border-slate-700/30"
                  >
                    {lang}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic">No languages listed</span>
              )}
            </div>
          </div>

          {/* Services */}
          <div className="p-6 border-b border-slate-800/50">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Services</h3>
            <div className="space-y-4">
              {services.length === 0 && (
                <p className="text-slate-500 text-sm">No services yet.</p>
              )}
              {services.map((service) => {
                const isEditing = editingServiceId === service.id
                return (
                  <div key={service.id} className="border border-slate-800/50 rounded-xl p-4 bg-slate-900/20">
                    {isEditing ? (
                      <div className="space-y-3">
                        <input
                          value={serviceDraft.title || ''}
                          onChange={(e) => setServiceDraft({ ...serviceDraft, title: e.target.value })}
                          placeholder="Service title"
                          className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                        />
                        <textarea
                          value={serviceDraft.description || ''}
                          onChange={(e) => setServiceDraft({ ...serviceDraft, description: e.target.value })}
                          placeholder="Service description"
                          className="w-full min-h-[80px] px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 resize-none"
                        />
                        <div className="grid grid-cols-3 gap-3">
                          <input
                            type="number"
                            value={serviceDraft.duration_minutes ?? 60}
                            onChange={(e) =>
                              setServiceDraft({ ...serviceDraft, duration_minutes: Number(e.target.value) })
                            }
                            placeholder="Duration"
                            className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                          />
                          <input
                            type="number"
                            value={serviceDraft.price_rub ?? 0}
                            onChange={(e) =>
                              setServiceDraft({ ...serviceDraft, price_rub: Number(e.target.value) })
                            }
                            placeholder="Price"
                            className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                          />
                          <select
                            value={serviceDraft.is_active ? 'true' : 'false'}
                            onChange={(e) =>
                              setServiceDraft({ ...serviceDraft, is_active: e.target.value === 'true' })
                            }
                            className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                          >
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                          </select>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => updateServiceMutation.mutate()}
                            className="px-4 py-2 rounded-lg text-sm font-medium bg-accent-500 text-white"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => {
                              setEditingServiceId(null)
                              setServiceDraft({})
                            }}
                            className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-800/60 text-slate-200"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-sm font-semibold text-white">{service.title}</p>
                            <p className="text-xs text-slate-400">
                              {service.duration_minutes} мин · {service.price_rub} ₽ · {service.is_active ? 'Active' : 'Inactive'}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                setEditingServiceId(service.id)
                                setServiceDraft(service)
                              }}
                              className="px-3 py-1.5 text-xs rounded-lg bg-slate-800/60 text-slate-200"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => deleteServiceMutation.mutate(service.id)}
                              className="px-3 py-1.5 text-xs rounded-lg bg-error-500/20 text-error-400"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                        {service.description && (
                          <p className="text-sm text-slate-300 mt-2">{service.description}</p>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}

              <div className="border border-dashed border-slate-700/70 rounded-xl p-4">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Add service</p>
                <div className="space-y-3">
                  <input
                    value={newService.title}
                    onChange={(e) => setNewService({ ...newService, title: e.target.value })}
                    placeholder="Service title"
                    className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                  />
                  <textarea
                    value={newService.description}
                    onChange={(e) => setNewService({ ...newService, description: e.target.value })}
                    placeholder="Service description"
                    className="w-full min-h-[80px] px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200 resize-none"
                  />
                  <div className="grid grid-cols-3 gap-3">
                    <input
                      type="number"
                      value={newService.duration_minutes}
                      onChange={(e) =>
                        setNewService({ ...newService, duration_minutes: Number(e.target.value) })
                      }
                      placeholder="Duration"
                      className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                    />
                    <input
                      type="number"
                      value={newService.price_rub}
                      onChange={(e) =>
                        setNewService({ ...newService, price_rub: Number(e.target.value) })
                      }
                      placeholder="Price"
                      className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                    />
                    <select
                      value={newService.is_active ? 'true' : 'false'}
                      onChange={(e) =>
                        setNewService({ ...newService, is_active: e.target.value === 'true' })
                      }
                      className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                    >
                      <option value="true">Active</option>
                      <option value="false">Inactive</option>
                    </select>
                  </div>
                  <button
                    onClick={() => createServiceMutation.mutate()}
                    className="px-4 py-2 rounded-lg text-sm font-medium bg-primary-500 text-white"
                    disabled={!newService.title.trim()}
                  >
                    Add service
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Working Hours */}
          <div className="p-6 border-b border-slate-800/50">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Schedule</h3>
              <button
                onClick={() => {
                  try {
                    const payload: Record<string, Array<{ start: string; end: string }>> = {}
                    DAYS.forEach((day) => {
                      payload[day.id] = parseRanges(scheduleInputs[day.id] || '')
                    })
                    setScheduleError(null)
                    updateScheduleMutation.mutate(payload)
                  } catch (err) {
                    setScheduleError(err instanceof Error ? err.message : 'Invalid schedule format')
                  }
                }}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800/50 text-slate-200 hover:bg-slate-800"
              >
                Save
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-3">
              Format: 09:00-12:00, 14:00-18:00
            </p>
            {scheduleError && (
              <div className="mb-3 text-xs text-error-400">{scheduleError}</div>
            )}
            <div className="space-y-2">
              {DAYS.map((day) => (
                <div key={day.id} className="flex items-center gap-3">
                  <span className="w-10 text-sm text-slate-400">{day.label}</span>
                  <input
                    value={scheduleInputs[day.id] || ''}
                    onChange={(e) => setScheduleInputs({ ...scheduleInputs, [day.id]: e.target.value })}
                    className="flex-1 px-3 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-slate-200"
                    placeholder="09:00-12:00, 14:00-18:00"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Dates */}
          <div className="p-6 grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Created</h3>
              <p className="text-slate-300">{format(new Date(nutritionist.created_at), 'MMM d, yyyy HH:mm')}</p>
            </div>
            <div>
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Submitted</h3>
              <p className="text-slate-300">
                {nutritionist.submitted_at
                  ? format(new Date(nutritionist.submitted_at), 'MMM d, yyyy HH:mm')
                  : '—'}
              </p>
            </div>
            {nutritionist.verified_at && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Verified</h3>
                <p className="text-slate-300">{format(new Date(nutritionist.verified_at), 'MMM d, yyyy HH:mm')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar: Actions & Documents */}
        <div className="space-y-6">
          {/* Actions Card */}
          <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
            <div className="p-4 border-b border-slate-800/50">
              <h3 className="font-medium text-white">Moderation Actions</h3>
            </div>
            <div className="p-4 space-y-3">
              {canModerate && (
                <>
                  <button
                    onClick={() => setActiveAction('approve')}
                    className={clsx(
                      'w-full px-4 py-3 rounded-xl text-sm font-medium transition-all',
                      activeAction === 'approve'
                        ? 'bg-success-500 text-white'
                        : 'bg-success-500/10 text-success-400 hover:bg-success-500/20 border border-success-500/20'
                    )}
                  >
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Approve
                    </span>
                  </button>

                  <button
                    onClick={() => setActiveAction('reject')}
                    className={clsx(
                      'w-full px-4 py-3 rounded-xl text-sm font-medium transition-all',
                      activeAction === 'reject'
                        ? 'bg-error-500 text-white'
                        : 'bg-error-500/10 text-error-400 hover:bg-error-500/20 border border-error-500/20'
                    )}
                  >
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Reject
                    </span>
                  </button>

                  <button
                    onClick={() => setActiveAction('needs_update')}
                    className={clsx(
                      'w-full px-4 py-3 rounded-xl text-sm font-medium transition-all',
                      activeAction === 'needs_update'
                        ? 'bg-accent-500 text-white'
                        : 'bg-accent-500/10 text-accent-400 hover:bg-accent-500/20 border border-accent-500/20'
                    )}
                  >
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Needs Update
                    </span>
                  </button>
                </>
              )}

              {canDisable && (
                <button
                  onClick={() => setActiveAction('disable')}
                  className={clsx(
                    'w-full px-4 py-3 rounded-xl text-sm font-medium transition-all',
                    activeAction === 'disable'
                      ? 'bg-warning-500 text-slate-900'
                      : 'bg-warning-500/10 text-warning-400 hover:bg-warning-500/20 border border-warning-500/20'
                  )}
                >
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                    Disable
                  </span>
                </button>
              )}

              {canActivate && (
                <button
                  onClick={() => setActiveAction('activate')}
                  className={clsx(
                    'w-full px-4 py-3 rounded-xl text-sm font-medium transition-all',
                    activeAction === 'activate'
                      ? 'bg-success-500 text-white'
                      : 'bg-success-500/10 text-success-400 hover:bg-success-500/20 border border-success-500/20'
                  )}
                >
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Activate
                  </span>
                </button>
              )}

              {!canModerate && !canDisable && !canActivate && (
                <p className="text-center text-slate-500 py-4 text-sm">
                  No actions available for this status
                </p>
              )}
            </div>

            {/* Action Form */}
            {activeAction && (
              <div className="p-4 border-t border-slate-800/50 bg-slate-900/30">
                {(activeAction === 'reject' || activeAction === 'needs_update') && (
                  <div className="mb-4">
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      {activeAction === 'reject' ? 'Rejection Reason *' : 'Update Notes *'}
                    </label>
                    <textarea
                      value={actionNote}
                      onChange={(e) => setActionNote(e.target.value)}
                      placeholder={
                        activeAction === 'reject'
                          ? 'Provide a reason for rejection...'
                          : 'What needs to be updated...'
                      }
                      className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500/50 resize-none"
                      rows={3}
                    />
                  </div>
                )}

                {activeAction === 'approve' && (
                  <div className="mb-4">
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Approval Note (optional)
                    </label>
                    <textarea
                      value={actionNote}
                      onChange={(e) => setActionNote(e.target.value)}
                      placeholder="Optional note for the approval..."
                      className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-accent-500/50 resize-none"
                      rows={3}
                    />
                  </div>
                )}

                {activeAction === 'disable' && (
                  <p className="text-sm text-warning-400 mb-4">
                    This will deactivate the nutritionist's profile. They will no longer appear in search results.
                  </p>
                )}
                {activeAction === 'activate' && (
                  <p className="text-sm text-success-400 mb-4">
                    This will activate the nutritionist's profile and make them visible to clients.
                  </p>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setActiveAction(null)
                      setActionNote('')
                    }}
                    className="flex-1 px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-800 transition-all"
                    disabled={isSubmitting}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAction}
                    disabled={
                      isSubmitting ||
                      ((activeAction === 'reject' || activeAction === 'needs_update') && !actionNote.trim())
                    }
                    className={clsx(
                      'flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed',
                      activeAction === 'approve' && 'bg-success-500 text-white hover:bg-success-600',
                      activeAction === 'reject' && 'bg-error-500 text-white hover:bg-error-600',
                      activeAction === 'needs_update' && 'bg-accent-500 text-white hover:bg-accent-600',
                      activeAction === 'disable' && 'bg-warning-500 text-slate-900 hover:bg-warning-400',
                      activeAction === 'activate' && 'bg-success-500 text-white hover:bg-success-600'
                    )}
                  >
                    {isSubmitting ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                        Processing...
                      </span>
                    ) : (
                      'Confirm'
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Documents Card */}
          <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
            <div className="p-4 border-b border-slate-800/50">
              <h3 className="font-medium text-white">Documents</h3>
            </div>
            <div className="divide-y divide-slate-800/50">
              {documents.length === 0 ? (
                <div className="p-6 text-center">
                  <svg
                    className="w-10 h-10 mx-auto mb-3 text-slate-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p className="text-slate-500 text-sm">No documents uploaded</p>
                </div>
              ) : (
                documents.map((doc) => (
                  <div key={doc.id} className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white capitalize">
                        {doc.type.replace('_', ' ')}
                      </span>
                      <span
                        className={clsx(
                          'px-2 py-0.5 text-xs font-medium rounded border',
                          docStatusColors[doc.status] || docStatusColors.uploaded
                        )}
                      >
                        {doc.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mb-3">
                      Uploaded {format(new Date(doc.uploaded_at), 'MMM d, yyyy')}
                    </p>
                    <button
                      onClick={() => handleDownloadDocument(doc)}
                      className="flex items-center gap-2 text-sm text-accent-400 hover:text-accent-300 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      Download
                    </button>
                    {doc.review_note && (
                      <p className="mt-2 text-xs text-slate-400 bg-slate-800/30 rounded-lg p-2">
                        Note: {doc.review_note}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
