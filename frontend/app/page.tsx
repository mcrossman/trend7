'use client';

import ChatInterface from './components/chat/ChatInterface';

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                TrendCloset
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Find the story that fits the moment.
              </p>
            </div>
            <div className="text-sm text-muted-foreground">
              POC v0.1.0
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Single Column */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ChatInterface />
      </div>
    </main>
  );
}
