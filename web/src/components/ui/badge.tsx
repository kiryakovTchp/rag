import React from 'react'
import { clsx } from 'clsx'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'error'
}

export function Badge({ 
  className, 
  variant = 'default', 
  ...props 
}: BadgeProps) {
  const base = 'inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium'
  
  const variants = {
    default: 'border-transparent bg-primary-500 text-white',
    secondary: 'border-transparent bg-secondary-100 text-secondary-800',
    outline: 'border-border bg-background text-foreground',
    success: 'border-transparent bg-success-500 text-white',
    warning: 'border-transparent bg-warning-500 text-white',
    error: 'border-transparent bg-error-500 text-white'
  }
  
  return (
    <span 
      className={clsx(base, variants[variant], className)} 
      {...props} 
    />
  )
}
