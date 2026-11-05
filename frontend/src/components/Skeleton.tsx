/**
 * Accessible skeleton loader component adhering to the warm parchment design system.
 */

interface SkeletonProps {
  className?: string
  lines?: number
}

export function Skeleton({ className = 'h-4 w-full', lines = 1 }: SkeletonProps) {
  if (lines > 1) {
    return (
      <div className="space-y-2.5 animate-pulse" aria-busy="true" aria-live="polite">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`bg-parchment-deep/40 rounded-sm ${className} ${
              i === lines - 1 ? 'w-4/5' : 'w-full'
            }`}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      className={`bg-parchment-deep/40 rounded-sm animate-pulse ${className}`}
      aria-busy="true"
      aria-live="polite"
    />
  )
}
