import React from 'react'
import { clsx } from 'clsx'

interface SeparatorProps extends React.HTMLAttributes<HTMLHRElement> {
  orientation?: 'horizontal' | 'vertical'
}

export function Separator({ 
  className, 
  orientation = 'horizontal', 
  ...props 
}: SeparatorProps) {
  return (
    <hr
      className={clsx(
        'border-0',
        orientation === 'horizontal' 
          ? 'h-px w-full bg-border' 
          : 'h-full w-px bg-border',
        className
      )}
      {...props}
    />
  )
}
