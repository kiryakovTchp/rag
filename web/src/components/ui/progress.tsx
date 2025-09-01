import React from 'react'
import { clsx } from 'clsx'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number
  max?: number
  size?: 'sm' | 'base' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'error'
}

export function Progress({ 
  className, 
  value = 0, 
  max = 100, 
  size = 'base',
  variant = 'default',
  ...props 
}: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))
  
  const sizes = {
    sm: 'h-1.5',
    base: 'h-2',
    lg: 'h-3'
  }
  
  const variants = {
    default: 'bg-primary-500',
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    error: 'bg-error-500'
  }
  
  return (
    <div 
      className={clsx(
        'w-full overflow-hidden rounded-full bg-secondary-100',
        sizes[size],
        className
      )}
      {...props}
    >
      <div 
        className={clsx(
          'h-full transition-all duration-300 ease-out',
          variants[variant]
        )}
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}
