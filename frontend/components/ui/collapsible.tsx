'use client';

import { useState, ReactNode } from 'react';
import { CaretDown, CaretRight } from '@phosphor-icons/react';

interface CollapsibleProps {
  children: ReactNode;
  title: string;
  defaultOpen?: boolean;
}

export function Collapsible({ children, title, defaultOpen = false }: CollapsibleProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
      >
        <span className="font-medium text-sm text-gray-900">{title}</span>
        {isOpen ? (
          <CaretDown className="w-4 h-4 text-gray-500" />
        ) : (
          <CaretRight className="w-4 h-4 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="p-4 bg-white">
          {children}
        </div>
      )}
    </div>
  );
}
