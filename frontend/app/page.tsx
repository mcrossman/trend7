'use client';

import { useState } from 'react';
import { MagnifyingGlassIcon, TrendUpIcon } from '@phosphor-icons/react';
import QueryInterface from './components/query/QueryInterface';
import TrendsDemo from './components/trends/TrendsDemo';
import ResultsPanel from './components/results/ResultsPanel';
import { Button } from '@/components/ui/button';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'search' | 'trends'>('search');

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                DejaNews
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Identify and resurface historical Atlantic stories
              </p>
            </div>
            <div className="text-sm text-gray-500">
              POC v0.1.0
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel */}
          <div className="lg:col-span-1 space-y-6">
            {/* Tab Switcher */}
            <div className="flex space-x-1 bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
              <Button
                onClick={() => setActiveTab('search')}
                variant={activeTab === 'search' ? 'default' : 'ghost'}
                className="flex-1"
              >
                <MagnifyingGlassIcon className="mr-2 size-4" />
                Search
              </Button>
              <Button
                onClick={() => setActiveTab('trends')}
                variant={activeTab === 'trends' ? 'default' : 'ghost'}
                className="flex-1"
              >
                <TrendUpIcon className="mr-2 size-4" />
                Trends
              </Button>
            </div>

            {/* Panel Content */}
            {activeTab === 'search' ? (
              <QueryInterface />
            ) : (
              <TrendsDemo />
            )}
          </div>

          {/* Right Panel - Results */}
          <div className="lg:col-span-2">
            <ResultsPanel />
          </div>
        </div>
      </div>
    </main>
  );
}
