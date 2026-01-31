'use client';

import { useState } from 'react';
import { TrendUpIcon, SpinnerIcon, FlameIcon, ChartLineUpIcon } from '@phosphor-icons/react';
import { triggerTrendsDemo } from '@/app/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { TrendsDemoResponse, TrendInfo, TrendMatch } from '@/app/types/blocks';

export default function TrendsDemo() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TrendsDemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forceRefresh, setForceRefresh] = useState(true);

  const handleTriggerDemo = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await triggerTrendsDemo(forceRefresh);
      setResult(data);
      console.log('Trends demo result:', data);
    } catch (err) {
      console.error('Error triggering trends demo:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'rising':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'top':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'breakout':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendUpIcon className="size-5" />
          Google Trends Demo
        </CardTitle>
        <CardDescription>
          Discover trending topics and find relevant Atlantic articles
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Force Refresh Checkbox */}
        <div className="flex items-center space-x-2">
          <Checkbox
            id="force-refresh"
            checked={forceRefresh}
            onCheckedChange={(checked) => setForceRefresh(checked as boolean)}
          />
          <Label
            htmlFor="force-refresh"
            className="text-sm font-normal cursor-pointer"
          >
            Force refresh (bypass cache)
          </Label>
        </div>

        {/* Trigger Button */}
        <Button
          onClick={handleTriggerDemo}
          disabled={loading}
          className="w-full"
          size="lg"
        >
          {loading ? (
            <>
              <SpinnerIcon className="mr-2 size-4 animate-spin" />
              Fetching Trends & Searching Archive...
            </>
          ) : (
            <>
              <FlameIcon className="mr-2 size-4" />
              🔄 Refresh Trends & Find Matches
            </>
          )}
        </Button>

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            Error: {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium">{result.message}</p>
            </div>

            {/* Trends Found */}
            {result.trends && result.trends.length > 0 && (
              <div className="space-y-3">
                <h3 className="font-semibold text-sm text-gray-700 flex items-center gap-2">
                  <ChartLineUpIcon className="size-4" />
                  Current Trends ({result.trends_found} found)
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {result.trends.slice(0, 10).map((trend: TrendInfo, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-mono text-gray-400 w-6">
                          {index + 1}
                        </span>
                        <span className="font-medium">{trend.keyword}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={getCategoryColor(trend.category)}>
                          {trend.category}
                        </Badge>
                        <span className="text-sm text-gray-500 min-w-[3rem] text-right">
                          {trend.score}/100
                        </span>
                        {trend.velocity && trend.velocity > 0 && (
                          <span className="text-xs text-green-600 font-medium">
                            +{trend.velocity}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            {/* Matches */}
            {result.top_matches && result.top_matches.length > 0 && (
              <div className="space-y-3">
                <h3 className="font-semibold text-sm text-gray-700">
                  📰 Matched Articles ({result.queue_entries_added} entries)
                </h3>
                <div className="space-y-2">
                  {result.top_matches.map((match: TrendMatch, index: number) => (
                    <div
                      key={index}
                      className="p-3 bg-blue-50 rounded-lg border border-blue-100"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-blue-900">
                          {match.trend_keyword}
                        </span>
                        <Badge variant="outline" className="bg-white">
                          Score: {match.priority_score.toFixed(2)}
                        </Badge>
                      </div>
                      <p className="text-xs text-blue-700 font-mono truncate">
                        Thread: {match.thread_id}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.top_matches && result.top_matches.length === 0 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
                No matching articles found in the Atlantic archive for these trends.
                Try running the analysis again or check back later.
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
