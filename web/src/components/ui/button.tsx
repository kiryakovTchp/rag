import React from 'react'
import { clsx } from 'clsx'

type ButtonVariant = 'default' | 'secondary' | 'ghost' | 'outline' | 'destructive'
type ButtonSize = 'sm' | 'base' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  disabled?: boolean
  loading?: boolean
}

export function Button({ 
  className, 
  variant = 'default', 
  size = 'base', 
  disabled = false,
  loading = false,
  children,
  ...props 
}: ButtonProps) {
  const base = 'inline-flex items-center justify-center rounded-xl font-medium transition-all duration-200 active:translate-y-[0.5px] disabled:opacity-50 disabled:cursor-not-allowed'
  
  const sizes = {
    sm: 'h-8 px-3 text-xs',
    base: 'h-9 px-3 text-sm', 
    lg: 'h-11 px-5 text-base'
  }
  
  const variants = {
    default: 'bg-primary-500 text-white hover:bg-primary-600 shadow-sm',
    secondary: 'bg-secondary-100 text-foreground hover:bg-secondary-200',
    ghost: 'bg-transparent hover:bg-secondary-100 text-foreground',
    outline: 'border border-border bg-background hover:bg-secondary-50 text-foreground',
    destructive: 'bg-error-500 text-white hover:bg-error-600'
  }
  
  return (
    <button 
      className={clsx(base, sizes[size], variants[variant], className)} 
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  )
}
