import React from 'react'
import { clsx } from 'clsx'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
  size?: 'sm' | 'base' | 'lg'
}

export function Input({ 
  className, 
  error = false, 
  size = 'base',
  ...props 
}: InputProps) {
  const base = 'w-full rounded-xl border bg-background px-3 text-sm outline-none transition-colors focus:ring-2 focus:ring-primary-500/20 disabled:cursor-not-allowed disabled:opacity-50'
  
  const sizes = {
    sm: 'h-8 text-xs',
    base: 'h-10 text-sm',
    lg: 'h-12 text-base'
  }
  
  const states = {
    default: 'border-border focus:border-primary-500',
    error: 'border-error-500 focus:border-error-500 focus:ring-error-500/20'
  }
  
  return (
    <input 
      className={clsx(base, sizes[size], states[error ? 'error' : 'default'], className)} 
      {...props} 
    />
  )
}
