import React from 'react'
import { clsx } from 'clsx'

interface IconChipProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'base' | 'lg'
  variant?: 'default' | 'primary' | 'secondary'
}

export function IconChip({ 
  className, 
  size = 'base', 
  variant = 'default',
  children,
  ...props 
}: IconChipProps) {
  const sizes = {
    sm: 'size-7',
    base: 'size-9',
    lg: 'size-11'
  }
  
  const variants = {
    default: 'bg-primary-900 text-white',
    primary: 'bg-primary-500 text-white',
    secondary: 'bg-secondary-200 text-secondary-800'
  }
  
  return (
    <div 
      className={clsx(
        'grid place-items-center rounded-lg shadow-sm',
        sizes[size],
        variants[variant],
        className
      )}
      aria-hidden
      {...props}
    >
      {children}
    </div>
  )
}
