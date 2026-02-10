export default function WellnessLoading() {
  return (
    <div className="space-y-8">
      {/* Header Skeleton */}
      <div className="flex justify-between items-center">
        <div>
          <div className="h-8 w-48 bg-gray-200 rounded-lg animate-pulse" />
          <div className="h-4 w-40 bg-gray-100 rounded mt-3 animate-pulse" />
        </div>
        <div className="h-10 w-32 bg-gray-200 rounded-lg animate-pulse" />
      </div>

      {/* Overall Wellness Score Card Skeleton */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-5 w-40 bg-gray-200 rounded animate-pulse" />
          <div className="h-5 w-5 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-10 w-20 bg-gray-200 rounded animate-pulse" />
            <div className="h-3 w-36 bg-gray-100 rounded animate-pulse" />
          </div>
          <div className="text-right space-y-2">
            <div className="h-4 w-10 bg-gray-200 rounded animate-pulse ml-auto" />
            <div className="h-3 w-16 bg-gray-100 rounded animate-pulse ml-auto" />
          </div>
        </div>
        <div className="h-3 w-full bg-gray-200 rounded-full animate-pulse" />
      </div>

      {/* Tabs Skeleton */}
      <div className="space-y-6">
        <div className="grid grid-cols-4 gap-2 bg-gray-100 rounded-lg p-1">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-9 bg-gray-200 rounded-md animate-pulse"
            />
          ))}
        </div>

        {/* Vitals Grid Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-200 p-6 space-y-4"
            >
              <div className="h-5 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="space-y-3">
                <div className="flex items-baseline justify-between">
                  <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
                  <div className="h-3 w-12 bg-gray-100 rounded animate-pulse" />
                </div>
                <div className="h-3 w-24 bg-gray-100 rounded animate-pulse" />
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <div key={j} className="flex justify-between">
                      <div className="h-3 w-20 bg-gray-100 rounded animate-pulse" />
                      <div className="h-3 w-16 bg-gray-100 rounded animate-pulse" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
