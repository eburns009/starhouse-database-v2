import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium transition-all duration-200',
  {
    variants: {
      variant: {
        default:
          'border-primary/20 bg-primary/10 text-primary hover:bg-primary/20',
        secondary:
          'border-secondary/20 bg-secondary text-secondary-foreground',
        outline: 'border-border bg-background text-foreground hover:bg-accent',
        destructive:
          'border-destructive/20 bg-destructive/10 text-destructive hover:bg-destructive/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
