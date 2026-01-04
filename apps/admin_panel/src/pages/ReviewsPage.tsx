import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { Review } from '@/types'
import { format } from 'date-fns'
import clsx from 'clsx'

type RatingFilter = 'all' | 'low'

export function ReviewsPage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<RatingFilter>('all')

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'reviews', filter],
    queryFn: () => adminApi.getReviews(filter === 'low' ? { rating_lte: 3 } : undefined),
  })

  const reviews: Review[] = data?.reviews || []

  const hideMutation = useMutation({
    mutationFn: adminApi.hideReview,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'reviews'] })
    },
  })

  const showMutation = useMutation({
    mutationFn: adminApi.showReview,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'reviews'] })
    },
  })

  const problematicMutation = useMutation({
    mutationFn: ({ id, problematic }: { id: string; problematic: boolean }) =>
      adminApi.markReviewProblematic(id, problematic),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'reviews'] })
    },
  })

  const filterButtons: { value: RatingFilter; label: string }[] = [
    { value: 'all', label: 'All Reviews' },
    { value: 'low', label: 'Rating ≤ 3' },
  ]

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={clsx(
              'w-4 h-4',
              star <= rating ? 'text-amber-400' : 'text-slate-700'
            )}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
        <span className="ml-1.5 text-sm text-slate-400">{rating}</span>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-bold text-white mb-2">Reviews</h1>
          <p className="text-slate-400">Quality control for client reviews</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6 p-1 bg-slate-925/50 border border-slate-800/50 rounded-xl w-fit">
        {filterButtons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => setFilter(btn.value)}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
              filter === btn.value
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            )}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center p-12">
            <div className="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center p-12 text-error-400">
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Failed to load reviews
          </div>
        ) : reviews.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <svg className="w-12 h-12 mb-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            <p className="font-medium text-slate-400 mb-1">No reviews found</p>
            <p className="text-sm">
              {filter === 'low' ? 'No low-rated reviews at the moment.' : 'No reviews have been submitted yet.'}
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800/50">
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Rating
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Review
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Nutritionist
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Booking
                </th>
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Status
                </th>
                <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider px-6 py-4">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {reviews.map((review) => (
                <tr 
                  key={review.id} 
                  className={clsx(
                    'hover:bg-slate-900/30 transition-colors',
                    review.is_hidden && 'opacity-50'
                  )}
                >
                  <td className="px-6 py-4">
                    {renderStars(review.rating)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="max-w-md">
                      <p className="text-sm text-slate-300 line-clamp-2">
                        {review.text || <span className="text-slate-500 italic">No text provided</span>}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {format(new Date(review.created_at), 'MMM d, yyyy')}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-slate-300">{review.nutritionist_name}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-mono text-slate-500 bg-slate-800/50 px-2 py-1 rounded">
                      {review.booking_id.slice(0, 8)}...
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1.5">
                      {review.is_hidden && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-slate-700/50 text-slate-400 border border-slate-600/30">
                          Hidden
                        </span>
                      )}
                      {review.is_problematic && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-error-500/10 text-error-400 border border-error-500/20">
                          Problematic
                        </span>
                      )}
                      {!review.is_hidden && !review.is_problematic && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-success-500/10 text-success-400 border border-success-500/20">
                          Visible
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      {review.is_hidden ? (
                        <button
                          onClick={() => showMutation.mutate(review.id)}
                          disabled={showMutation.isPending}
                          className="px-3 py-1.5 text-sm font-medium text-success-400 hover:bg-success-500/10 rounded-lg transition-colors disabled:opacity-50"
                        >
                          Show
                        </button>
                      ) : (
                        <button
                          onClick={() => hideMutation.mutate(review.id)}
                          disabled={hideMutation.isPending}
                          className="px-3 py-1.5 text-sm font-medium text-slate-400 hover:bg-slate-700/50 rounded-lg transition-colors disabled:opacity-50"
                        >
                          Hide
                        </button>
                      )}
                      <button
                        onClick={() => problematicMutation.mutate({ 
                          id: review.id, 
                          problematic: !review.is_problematic 
                        })}
                        disabled={problematicMutation.isPending}
                        className={clsx(
                          'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors disabled:opacity-50',
                          review.is_problematic
                            ? 'text-slate-400 hover:bg-slate-700/50'
                            : 'text-error-400 hover:bg-error-500/10'
                        )}
                      >
                        {review.is_problematic ? 'Clear Flag' : 'Flag'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

