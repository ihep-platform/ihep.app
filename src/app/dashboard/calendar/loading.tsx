export default function CalendarLoading() {
  return (
    <div className="space-y-8">
      {/* Header Skeleton */}
      <div className="flex justify-between items-center">
        <div>
          <div className="h-8 w-64 bg-gray-200 rounded-lg animate-pulse" />
          <div className="h-4 w-52 bg-gray-100 rounded mt-3 animate-pulse" />
        </div>
        <div className="h-10 w-40 bg-gray-200 rounded-lg animate-pulse" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar Widget Skeleton */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 lg:col-span-1 space-y-4">
          <div className="h-5 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="space-y-3">
            {/* Month nav */}
            <div className="flex items-center justify-between">
              <div className="h-6 w-6 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-6 bg-gray-200 rounded animate-pulse" />
            </div>
            {/* Day headers */}
            <div className="grid grid-cols-7 gap-1">
              {Array.from({ length: 7 }).map((_, i) => (
                <div
                  key={`header-${i}`}
                  className="h-8 bg-gray-100 rounded animate-pulse"
                />
              ))}
            </div>
            {/* Calendar grid -- 5 rows of 7 */}
            {Array.from({ length: 5 }).map((_, row) => (
              <div key={row} className="grid grid-cols-7 gap-1">
                {Array.from({ length: 7 }).map((_, col) => (
                  <div
                    key={col}
                    className="h-8 bg-gray-100 rounded-full animate-pulse"
                  />
                ))}
              </div>
            ))}
          </div>
          {/* Legend */}
          <div className="space-y-2 pt-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="h-3 w-3 bg-gray-200 rounded-full animate-pulse" />
                <div className="h-3 w-16 bg-gray-100 rounded animate-pulse" />
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Appointments Skeleton */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 lg:col-span-2 space-y-4">
          <div className="h-5 w-48 bg-gray-200 rounded animate-pulse" />
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="border border-gray-200 rounded-lg p-4 space-y-3"
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-2">
                    <div className="h-5 w-40 bg-gray-200 rounded animate-pulse" />
                    <div className="h-3 w-48 bg-gray-100 rounded animate-pulse" />
                  </div>
                  <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse" />
                </div>
                <div className="space-y-2">
                  <div className="h-3 w-44 bg-gray-100 rounded animate-pulse" />
                  <div className="h-3 w-24 bg-gray-100 rounded animate-pulse" />
                  <div className="h-3 w-36 bg-gray-100 rounded animate-pulse" />
                </div>
                <div className="flex gap-2 mt-2">
                  <div className="h-8 flex-1 bg-gray-100 rounded-lg animate-pulse" />
                  <div className="h-8 flex-1 bg-gray-100 rounded-lg animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Past Appointments Skeleton */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div className="h-5 w-36 bg-gray-200 rounded animate-pulse" />
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <div
              key={i}
              className="flex justify-between items-center py-3 border-b border-gray-100"
            >
              <div className="space-y-2">
                <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
                <div className="h-3 w-28 bg-gray-100 rounded animate-pulse" />
              </div>
              <div className="space-y-2 text-right">
                <div className="h-3 w-20 bg-gray-200 rounded animate-pulse ml-auto" />
                <div className="h-3 w-16 bg-gray-100 rounded animate-pulse ml-auto" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
