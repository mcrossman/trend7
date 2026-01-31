import QueryInterface from './components/query/QueryInterface';
import ResultsPanel from './components/results/ResultsPanel';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Story Thread Surfacing
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
          {/* Left Panel - Query Interface */}
          <div className="lg:col-span-1">
            <QueryInterface />
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
