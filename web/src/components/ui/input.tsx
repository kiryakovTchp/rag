import React from 'react'
import { clsx } from 'clsx'

type NativeInputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">;
interface InputProps extends NativeInputProps {
  error?: boolean
  uiSize?: 'sm' | 'base' | 'lg'
}

export function Input({ 
  className, 
  error = false, 
  uiSize = 'base',
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
      className={clsx(base, sizes[uiSize], states[error ? 'error' : 'default'], className)} 
      {...props} 
    />
  )
}
