import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { Nutritionist, NutritionistDocument } from '@/types'
import { format } from 'date-fns'
import clsx from 'clsx'

type ActionType = 'approve' | 'reject' | 'needs_update' | 'disable' | null

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

export function NutritionistDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [activeAction, setActiveAction] = useState<ActionType>(null)
  const [actionNote, setActionNote] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'nutritionist', id],
    queryFn: () => adminApi.getNutritionist(id!),
    enabled: !!id,
  })

  const nutritionist: Nutritionist | null = data?.nutritionist || null
  const documents: NutritionistDocument[] = data?.documents || []

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
                <div className="flex items-center gap-3 mb-2">
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
                </div>
                <p className="text-slate-400 text-sm">
                  {nutritionist.years_experience} years of experience • {nutritionist.currency} {nutritionist.hourly_rate}/hr
                </p>
              </div>
            </div>
          </div>

          {/* Bio */}
          <div className="p-6 border-b border-slate-800/50">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Bio</h3>
            <p className="text-slate-300 leading-relaxed">
              {nutritionist.bio || <span className="text-slate-500 italic">No bio provided</span>}
            </p>
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

              {!canModerate && !canDisable && (
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
                      activeAction === 'disable' && 'bg-warning-500 text-slate-900 hover:bg-warning-400'
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

