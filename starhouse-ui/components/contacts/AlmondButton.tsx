/**
 * Almond-shaped expandable button component
 * FAANG Standard: Reusable, type-safe component with feminine design aesthetics
 */

import { ChevronDown, ChevronUp, LucideIcon } from 'lucide-react'

interface AlmondButtonProps {
  icon: LucideIcon
  label: string
  count?: number
  isExpanded: boolean
  onClick: () => void
  gradientFrom?: string
  gradientTo?: string
  hasEyelashes?: boolean
}

export function AlmondButton({
  icon: Icon,
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
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`
              rounded-full p-3 transition-all duration-300
              ${isExpanded
                ? 'bg-white/90 text-rose-600 shadow-md'
                : 'bg-white/70 text-purple-600 group-hover:bg-white/90'
              }
            `}>
              <Icon className="h-6 w-6" />
            </div>
            <div className="text-left">
              <span className={`
                font-semibold text-lg transition-colors
                ${isExpanded ? 'text-rose-900' : 'text-purple-900'}
              `}>
                {label}
              </span>
              {count !== undefined && (
                <span className="ml-2 text-base font-normal text-purple-700/70">
                  ({count})
                </span>
              )}
            </div>
          </div>

          <div className={`
            rounded-full p-2 transition-all duration-300
            ${isExpanded
              ? 'bg-white/70 text-rose-700'
              : 'bg-white/50 text-purple-700 group-hover:bg-white/70'
            }
          `}>
            {isExpanded ? (
              <ChevronUp className="h-5 w-5" />
            ) : (
              <ChevronDown className="h-5 w-5" />
            )}
          </div>
        </div>
      </button>
    </div>
  )
}
