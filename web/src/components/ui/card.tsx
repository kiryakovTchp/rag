import React from 'react'
import { clsx } from 'clsx'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, ...props }: CardProps) {
  return (
    <div 
      className={clsx(
        'rounded-2xl border border-border bg-background shadow-sm',
        className
      )} 
      {...props} 
    />
  )
}

export function CardHeader({ className, ...props }: CardProps) {
  return (
    <div 
      className={clsx('p-6 pb-3', className)} 
      {...props} 
    />
  )
}

export function CardContent({ className, ...props }: CardProps) {
  return (
    <div 
      className={clsx('p-6', className)} 
      {...props} 
    />
  )
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 
      className={clsx('text-lg font-semibold text-foreground', className)} 
      {...props} 
    />
  )
}

export function CardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p 
      className={clsx('text-sm text-muted-600', className)} 
      {...props} 
    />
  )
}

export function CardFooter({ className, ...props }: CardProps) {
  return (
    <div 
      className={clsx('p-6 pt-3', className)} 
      {...props} 
    />
  )
}
