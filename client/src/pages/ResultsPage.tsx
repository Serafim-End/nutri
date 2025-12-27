import { useQuery } from '@tanstack/react-query'
import { useIntakeStore } from '../store/intake'
import { clientApi, publicApi } from '../lib/api'
import NutritionistCard from '../components/NutritionistCard'
import LoadingScreen from '../components/LoadingScreen'

export default function ResultsPage() {
  const { intakeId } = useIntakeStore()

  // Try to get matches if we have an intake ID, otherwise fetch all
  const { data, isLoading, error } = useQuery({
    queryKey: ['matches', intakeId],
    queryFn: async () => {
      if (intakeId) {
        return clientApi.getMatches(intakeId)
      }
      // Fallback to listing all nutritionists
      const result = await publicApi.getNutritionists()
      return { matches: result.nutritionists, total: result.total }
    },
  })

  if (isLoading) {
    return <LoadingScreen />
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-500">Failed to load nutritionists.</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  const nutritionists = data?.matches || []

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50/50 to-white">
      {/* Header */}
      <div className="px-4 pt-6 pb-4">
        <h1 className="text-2xl font-display font-bold text-gray-900">
          Your Matches
        </h1>
        <p className="text-gray-500 mt-1">
          {nutritionists.length} nutritionist{nutritionists.length !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* Results list */}
      <div className="px-4 pb-8 space-y-3">
        {nutritionists.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🔍</div>
            <p className="text-gray-500">
              No nutritionists found matching your criteria.
            </p>
            <p className="text-gray-400 text-sm mt-2">
              Try adjusting your preferences.
            </p>
          </div>
        ) : (
          nutritionists.map((nutritionist, index) => (
            <NutritionistCard
              key={nutritionist.nutritionist_id}
              nutritionist={nutritionist}
              animationDelay={index * 50}
            />
          ))
        )}
      </div>
    </div>
  )
}


