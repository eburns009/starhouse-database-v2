import * as React from 'react'
import { cn } from '@/lib/utils'

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  initials: string
}

export function Avatar({ initials, className, ...props }: AvatarProps) {
  return (
    <div
      className={cn(
        'inline-flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/80 text-white text-sm font-semibold shadow-sm ring-2 ring-primary/10',
        className
      )}
      {...props}
    >
      {initials}
    </div>
  )
}
