'use client';

import { useState } from 'react';
import { MagnifyingGlassIcon } from '@phosphor-icons/react';
import { analyzeText, analyzeArticle } from '@/app/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

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

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MagnifyingGlassIcon className="size-4" />
          Input
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Tabs */}
        <div className="flex space-x-1 bg-muted p-1 rounded-lg">
          <Button
            onClick={() => setActiveTab('text')}
            variant={activeTab === 'text' ? 'default' : 'ghost'}
            className="flex-1"
          >
            Text
          </Button>
          <Button
            onClick={() => setActiveTab('article')}
            variant={activeTab === 'article' ? 'default' : 'ghost'}
            className="flex-1"
          >
            Article ID
          </Button>
        </div>

        {/* Text Input */}
        {activeTab === 'text' && (
          <div className="space-y-4">
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste article content or draft here..."
              className="min-h-48"
            />
            <Button
              onClick={handleTextSubmit}
              disabled={loading || !text.trim()}
              className="w-full"
            >
              {loading ? 'Analyzing...' : 'Find Connections'}
            </Button>
          </div>
        )}

        {/* Article ID Input */}
        {activeTab === 'article' && (
          <div className="space-y-4">
            <Input
              value={articleId}
              onChange={(e) => setArticleId(e.target.value)}
              placeholder="Enter article ID (e.g., atlantic_12345)"
            />
            <Button
              onClick={handleArticleSubmit}
              disabled={loading || !articleId.trim()}
              className="w-full"
            >
              {loading ? 'Analyzing...' : 'Analyze Article'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
