/**
 * Almond-shaped expandable button component
 * FAANG Standard: Reusable, type-safe component with feminine design aesthetics
 */

interface AlmondButtonProps {
  label: string
  count?: number
  isExpanded: boolean
  onClick: () => void
  gradientFrom?: string
  gradientTo?: string
  hasEyelashes?: boolean
}

export function AlmondButton({
  label,
  count,
  isExpanded,
  onClick,
  gradientFrom = 'from-rose-100',
  gradientTo = 'to-purple-100',
  hasEyelashes = false,
}: AlmondButtonProps) {
  return (
    <div className="relative w-full">
      {/* Eyelashes - only for Additional Names */}
      {hasEyelashes && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex gap-3 z-10">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="w-0.5 h-4 bg-gradient-to-t from-rose-400/60 to-transparent rounded-full"
              style={{
                transform: `rotate(${(i - 2) * 15}deg)`,
                transformOrigin: 'bottom center',
              }}
            />
          ))}
        </div>
      )}

      <button
        onClick={onClick}
        className={`
          group relative w-full overflow-hidden
          transition-all duration-300 ease-out
          ${isExpanded
            ? 'bg-gradient-to-r from-rose-200/60 to-purple-200/60 shadow-xl scale-[1.03]'
            : `bg-gradient-to-r ${gradientFrom} ${gradientTo} hover:shadow-lg hover:scale-[1.02]`
          }
        `}
        style={{
          borderRadius: '120px / 40px', // More elongated eye shape (3:1 ratio)
          padding: '24px 48px',
          minHeight: '80px',
        }}
      >
        {/* Subtle shimmer effect on hover */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        {/* Content */}
        <div className="relative flex items-center justify-center">
          <div className="text-center">
            <span className={`
              font-medium text-sm transition-colors
              ${isExpanded ? 'text-rose-900' : 'text-purple-900'}
            `}>
              {label}
            </span>
            {count !== undefined && (
              <span className="ml-1.5 text-xs font-normal text-purple-700/70">
                ({count})
              </span>
            )}
          </div>
        </div>
      </button>
    </div>
  )
}
