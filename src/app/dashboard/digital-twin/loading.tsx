export default function DigitalTwinLoading() {
  return (
    <div className="space-y-8">
      {/* Header Skeleton */}
      <div>
        <div className="h-8 w-72 bg-gray-200 rounded-lg animate-pulse" />
        <div className="h-4 w-96 bg-gray-100 rounded mt-3 animate-pulse" />
      </div>

      {/* Overall Health Score Card Skeleton */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex-1 space-y-3">
            <div className="h-4 w-36 bg-gray-200 rounded animate-pulse" />
            <div className="h-12 w-24 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 w-64 bg-gray-100 rounded animate-pulse" />
          </div>
          <div className="w-48 h-48 rounded-full bg-gray-200 animate-pulse" />
        </div>
      </div>

      {/* 3D Viewer Area Skeleton */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-5 w-48 bg-gray-200 rounded animate-pulse" />
          <div className="h-9 w-24 bg-gray-200 rounded-lg animate-pulse" />
        </div>
        <div className="w-full aspect-video bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg animate-pulse" />
      </div>

      {/* Body Systems Status Grid Skeleton */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div className="h-5 w-44 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="border border-gray-200 rounded-lg p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-6 w-6 bg-gray-200 rounded animate-pulse" />
                  <div className="h-4 w-28 bg-gray-200 rounded animate-pulse" />
                </div>
                <div className="h-7 w-12 bg-gray-200 rounded animate-pulse" />
              </div>
              <div className="h-2 w-full bg-gray-200 rounded-full animate-pulse" />
              <div className="h-3 w-28 bg-gray-100 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>

      {/* Tabs Skeleton */}
      <div className="space-y-6">
        <div className="grid grid-cols-3 gap-2 bg-gray-100 rounded-lg p-1">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-9 bg-gray-200 rounded-md animate-pulse"
            />
          ))}
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div className="h-5 w-36 bg-gray-200 rounded animate-pulse" />
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-20 w-full bg-gray-100 rounded-lg animate-pulse"
            />
          ))}
        </div>
      </div>
    </div>
  )
}
