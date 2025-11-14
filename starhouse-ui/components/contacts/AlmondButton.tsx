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
}

export function AlmondButton({
  icon: Icon,
  label,
  count,
  isExpanded,
  onClick,
  gradientFrom = 'from-rose-100',
  gradientTo = 'to-purple-100',
}: AlmondButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`
        group relative w-full overflow-hidden
        transition-all duration-300 ease-out
        ${isExpanded
          ? 'bg-gradient-to-r from-rose-200/60 to-purple-200/60 shadow-lg scale-[1.02]'
          : `bg-gradient-to-r ${gradientFrom} ${gradientTo} hover:shadow-md hover:scale-[1.01]`
        }
      `}
      style={{
        borderRadius: '100px / 50px',
        padding: '20px 40px',
        minHeight: '70px',
      }}
    >
      {/* Subtle shimmer effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Content */}
      <div className="relative flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`
            rounded-full p-2.5 transition-all duration-300
            ${isExpanded
              ? 'bg-white/80 text-rose-600 shadow-sm'
              : 'bg-white/60 text-purple-600 group-hover:bg-white/80'
            }
          `}>
            <Icon className="h-5 w-5" />
          </div>
          <div className="text-left">
            <span className={`
              font-medium text-base transition-colors
              ${isExpanded ? 'text-rose-900' : 'text-purple-900'}
            `}>
              {label}
            </span>
            {count !== undefined && (
              <span className="ml-2 text-sm font-normal text-purple-700/70">
                ({count})
              </span>
            )}
          </div>
        </div>

        <div className={`
          rounded-full p-1.5 transition-all duration-300
          ${isExpanded
            ? 'bg-white/60 text-rose-700'
            : 'bg-white/40 text-purple-700 group-hover:bg-white/60'
          }
        `}>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </div>
      </div>
    </button>
  )
}
