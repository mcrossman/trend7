'use client';

import { useState, useEffect } from 'react';
import { TrendUpIcon, SpinnerIcon, FlameIcon, ChartLineUpIcon, ClockIcon } from '@phosphor-icons/react';
import { triggerTrendsDemo, getCurrentTrends } from '@/app/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { TrendsDemoResponse, TrendInfo, TrendMatch } from '@/app/types/blocks';

interface CachedTrend {
  keyword: string;
  score: number;
  category: string;
  velocity?: number;
}

export default function TrendsDemo() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TrendsDemoResponse | null>(null);
  const [cachedTrends, setCachedTrends] = useState<CachedTrend[] | null>(null);
  const [cachedTimestamp, setCachedTimestamp] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forceRefresh, setForceRefresh] = useState(false);

  // Load cached trends on mount
  useEffect(() => {
    loadCachedTrends();
  }, []);

  const loadCachedTrends = async () => {
    try {
      const data = await getCurrentTrends(20);
      if (data.success && data.trends && data.trends.length > 0) {
        setCachedTrends(data.trends);
        setCachedTimestamp(data.recorded_at);
      }
    } catch {
      console.log('No cached trends available');
    }
  };

  const handleTriggerDemo = async () => {
    setLoading(true);
    setError(null);
    try {
      // If not forcing refresh and we have cached trends, use them
      if (!forceRefresh && cachedTrends && cachedTrends.length > 0) {
        // Use cached data but still trigger the watch cycle to find matches
        console.log('Using cached trends, triggering match search...');
        
        // Call demo-trigger with force_refresh=false to use cache
        const data = await triggerTrendsDemo(false);
        setResult(data);
        
        // Refresh cached trends display
        await loadCachedTrends();
      } else {
        // Force refresh from Google
        console.log('Fetching fresh trends from Google...');
        const data = await triggerTrendsDemo(true);
        setResult(data);
        
        // Update cached trends
        await loadCachedTrends();
      }
      
      console.log('Trends demo result:', result);
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
        return 'bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/30';
      case 'top':
        return 'bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-500/30';
      case 'breakout':
        return 'bg-purple-500/20 text-purple-700 dark:text-purple-400 border-purple-500/30';
      default:
        return 'bg-gray-500/20 text-gray-700 dark:text-gray-400 border-gray-500/30';
    }
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    return date.toLocaleString();
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
        {/* Cache Status */}
        {cachedTrends && cachedTrends.length > 0 && (
          <div className="flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <ClockIcon className="size-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-700 dark:text-blue-300">
              {cachedTrends.length} trends cached from {formatTimestamp(cachedTimestamp)}
            </span>
          </div>
        )}

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
            Force refresh from Google (slower, may hit rate limits)
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
              {forceRefresh ? 'Fetching from Google...' : 'Searching Archive...'}
            </>
          ) : (
            <>
              <FlameIcon className="mr-2 size-4" />
              {forceRefresh ? '🔄 Fetch Fresh Trends' : '🔍 Find Matches from Cache'}
            </>
          )}
        </Button>

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
            Error: {error}
          </div>
        )}

        {/* Cached Trends Preview (if no result yet) */}
        {!result && cachedTrends && cachedTrends.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-semibold text-sm text-foreground flex items-center gap-2">
              <ChartLineUpIcon className="size-4" />
              Cached Trends ({cachedTrends.length} available)
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {cachedTrends.slice(0, 10).map((trend: CachedTrend, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border border-border"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-mono text-muted-foreground w-6">
                      {index + 1}
                    </span>
                    <span className="font-medium">{trend.keyword}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={getCategoryColor(trend.category)}>
                      {trend.category}
                    </Badge>
                    <span className="text-sm text-muted-foreground min-w-[3rem] text-right">
                      {trend.score}/100
                    </span>
                    {trend.velocity && trend.velocity > 0 && (
                      <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                        +{trend.velocity}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground text-center">
              Click &quot;Find Matches from Cache&quot; to search Atlantic archive for these trends
            </p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <p className="text-green-700 dark:text-green-300 font-medium">{result.message}</p>
            </div>

            {/* Trends Found */}
            {result.trends && result.trends.length > 0 && (
              <div className="space-y-3">
                <h3 className="font-semibold text-sm text-foreground flex items-center gap-2">
                  <ChartLineUpIcon className="size-4" />
                  {forceRefresh ? 'Fresh Trends' : 'Trends Used'} ({result.trends_found} found)
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {result.trends.slice(0, 10).map((trend: TrendInfo, index: number) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border border-border"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-mono text-muted-foreground w-6">
                          {index + 1}
                        </span>
                        <span className="font-medium">{trend.keyword}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={getCategoryColor(trend.category)}>
                          {trend.category}
                        </Badge>
                        <span className="text-sm text-muted-foreground min-w-[3rem] text-right">
                          {trend.score}/100
                        </span>
                        {trend.velocity && trend.velocity > 0 && (
                          <span className="text-xs text-green-600 dark:text-green-400 font-medium">
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
                <h3 className="font-semibold text-sm text-foreground">
                  📰 Matched Articles ({result.queue_entries_added} entries)
                </h3>
                <div className="space-y-2">
                  {result.top_matches.map((match: TrendMatch, index: number) => (
                    <div
                      key={index}
                      className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                          {match.trend_keyword}
                        </span>
                        <Badge variant="outline" className="bg-card">
                          Score: {match.priority_score.toFixed(2)}
                        </Badge>
                      </div>
                      <p className="text-xs text-blue-600 dark:text-blue-400 font-mono truncate">
                        Thread: {match.thread_id}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.top_matches && result.top_matches.length === 0 && (
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-yellow-700 dark:text-yellow-300 text-sm">
                No matching articles found in Atlantic archive for these trends.
                Try running analysis again or check back later.
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
