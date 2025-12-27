export default function LoadingScreen() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-primary-50 to-white">
      <div className="animate-pulse">
        <div className="w-20 h-20 bg-primary-500 rounded-3xl flex items-center justify-center shadow-lg">
          <svg
            className="w-12 h-12 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
      </div>
      <h1 className="mt-6 text-2xl font-display font-bold text-gray-800">
        NutriMatch
      </h1>
      <p className="mt-2 text-gray-500">Finding your perfect nutritionist...</p>
    </div>
  )
}


