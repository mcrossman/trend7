'use client';

import { useState, ReactNode } from 'react';
import { CaretDown, CaretRight } from '@phosphor-icons/react';

interface CollapsibleProps {
  children: ReactNode;
  title: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

export function Collapsible({ children, title, defaultOpen = false, className = '' }: CollapsibleProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={`border border-border rounded-lg overflow-hidden ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-muted/50 hover:bg-muted flex items-center justify-between transition-colors"
      >
        <span className="font-medium text-sm text-foreground">{title}</span>
        {isOpen ? (
          <CaretDown className="w-4 h-4 text-muted-foreground" />
        ) : (
          <CaretRight className="w-4 h-4 text-muted-foreground" />
        )}
      </button>
      {isOpen && (
        <div className="p-4 bg-card">
          {children}
        </div>
      )}
    </div>
  );
}
