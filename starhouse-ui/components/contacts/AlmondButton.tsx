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
    <div className="relative w-full max-w-[200px] mx-auto">
      {/* Girly Eyelashes - only for Additional Names (Real Eye) */}
      {hasEyelashes && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 flex gap-2 z-10">
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="origin-bottom"
              style={{
                transform: `rotate(${(i - 3) * 18}deg)`,
              }}
            >
              <div
                className="w-1 bg-gradient-to-t from-rose-500/80 via-rose-400/60 to-transparent rounded-full"
                style={{
                  height: i === 3 ? '22px' : i === 2 || i === 4 ? '18px' : '14px',
                  width: i === 3 ? '2px' : '1.5px',
                }}
              />
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onClick}
        className={`
          group relative w-full overflow-visible
          transition-all duration-300 ease-out
          ${isExpanded
            ? 'bg-gradient-to-r from-rose-200/60 to-purple-200/60 shadow-xl scale-[1.05]'
            : `bg-gradient-to-r ${gradientFrom} ${gradientTo} hover:shadow-lg hover:scale-[1.02]`
          }
          ${hasEyelashes ? 'bg-white border-2 border-rose-300/40' : ''}
        `}
        style={{
          borderRadius: '100px / 45px', // Eye shape
          padding: '16px 24px',
          minHeight: '60px',
        }}
      >
        {/* Shimmer effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"
          style={{ borderRadius: '100px / 45px' }}
        />

        {/* Pupil - only for real eye (Additional Names) */}
        {hasEyelashes && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            {/* Iris */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-rose-400 to-rose-600 flex items-center justify-center shadow-lg">
              {/* Pupil */}
              <div className="w-4 h-4 rounded-full bg-gray-900 relative overflow-hidden">
                {/* Light reflection */}
                <div className="absolute top-0.5 left-0.5 w-1.5 h-1.5 rounded-full bg-white/70" />
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="relative flex items-center justify-center">
          <div className="text-center">
            <span className={`
              font-medium text-xs transition-colors
              ${isExpanded ? 'text-rose-900' : 'text-purple-900'}
              ${hasEyelashes ? 'opacity-0' : 'opacity-100'}
            `}>
              {label}
            </span>
            {count !== undefined && !hasEyelashes && (
              <span className="ml-1 text-[10px] font-normal text-purple-700/70">
                ({count})
              </span>
            )}
          </div>
        </div>
      </button>
    </div>
  )
}
