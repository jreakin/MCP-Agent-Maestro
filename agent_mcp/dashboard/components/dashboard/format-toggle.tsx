"use client"

import React from 'react'
import { Button } from '@/components/ui/button'
import { Code, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

type FormatType = 'json' | 'toon'

interface FormatToggleProps {
  format: FormatType
  onFormatChange: (format: FormatType) => void
  className?: string
}

export function FormatToggle({ format, onFormatChange, className }: FormatToggleProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="text-xs text-muted-foreground">Format:</span>
      <div className="flex border rounded-md overflow-hidden">
        <Button
          variant={format === 'json' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => onFormatChange('json')}
          className={cn(
            "rounded-none border-0 h-7 px-3 text-xs",
            format === 'json' && "bg-primary text-primary-foreground"
          )}
        >
          <Code className="h-3 w-3 mr-1.5" />
          JSON
        </Button>
        <Button
          variant={format === 'toon' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => onFormatChange('toon')}
          className={cn(
            "rounded-none border-0 h-7 px-3 text-xs",
            format === 'toon' && "bg-primary text-primary-foreground"
          )}
          title="Token-Oriented Object Notation - More token-efficient"
        >
          <Zap className="h-3 w-3 mr-1.5" />
          TOON
        </Button>
      </div>
    </div>
  )
}

