'use client';

import { useState } from 'react';

export default function ResultsPanel() {
  const [results, setResults] = useState(null);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        📊 Results
      </h2>

      {!results && (
        <div className="text-center py-12 text-gray-500">
          <p>Submit a query to see results</p>
          <p className="text-sm mt-2">
            Enter text or an article ID to find related story threads
          </p>
        </div>
      )}

      {results && (
        <div className="space-y-6">
          {/* Results will be rendered here */}
          <pre className="bg-gray-50 p-4 rounded-md overflow-auto">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
