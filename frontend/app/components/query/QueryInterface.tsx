'use client';

import { useState } from 'react';
import { analyzeText, analyzeArticle, getProactiveSuggestions } from '@/app/lib/api';

export default function QueryInterface() {
  const [activeTab, setActiveTab] = useState<'text' | 'article'>('text');
  const [text, setText] = useState('');
  const [articleId, setArticleId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleTextSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const result = await analyzeText(text);
      console.log('Analysis result:', result);
      // TODO: Update results panel
    } catch (error) {
      console.error('Error analyzing text:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleArticleSubmit = async () => {
    if (!articleId.trim()) return;
    setLoading(true);
    try {
      const result = await analyzeArticle(articleId);
      console.log('Article analysis result:', result);
      // TODO: Update results panel
    } catch (error) {
      console.error('Error analyzing article:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProactiveTrigger = async () => {
    setLoading(true);
    try {
      const result = await getProactiveSuggestions();
      console.log('Proactive suggestions:', result);
      // TODO: Update results panel
    } catch (error) {
      console.error('Error getting proactive suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        🔍 Input
      </h2>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-4">
        <button
          onClick={() => setActiveTab('text')}
          className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'text'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Text
        </button>
        <button
          onClick={() => setActiveTab('article')}
          className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'article'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Article ID
        </button>
      </div>

      {/* Text Input */}
      {activeTab === 'text' && (
        <div className="space-y-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste article content or draft here..."
            className="w-full h-48 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
          <button
            onClick={handleTextSubmit}
            disabled={loading || !text.trim()}
            className="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analyzing...' : 'Find Connections'}
          </button>
        </div>
      )}

      {/* Article ID Input */}
      {activeTab === 'article' && (
        <div className="space-y-4">
          <input
            type="text"
            value={articleId}
            onChange={(e) => setArticleId(e.target.value)}
            placeholder="Enter article ID (e.g., atlantic_12345)"
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleArticleSubmit}
            disabled={loading || !articleId.trim()}
            className="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze Article'}
          </button>
        </div>
      )}

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-200" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">Or</span>
        </div>
      </div>

      {/* Proactive Button */}
      <button
        onClick={handleProactiveTrigger}
        disabled={loading}
        className="w-full py-2 px-4 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Scanning...' : 'Scan Proactive Suggestions'}
      </button>
    </div>
  );
}
