'use client';

import { useState, useEffect, useCallback } from 'react';
import { Collapsible } from '@/components/ui/collapsible';
import { Message } from 'slack-blocks-to-jsx';
import type { Block } from 'slack-blocks-to-jsx';
import 'slack-blocks-to-jsx/dist/style.css';
import { getProactiveSuggestions } from '@/app/lib/api';
import { ProactiveThread } from '@/app/types/blocks';
import { Button } from '@/components/ui/button';
import { SpinnerIcon, ArrowsClockwiseIcon, ChatCircleTextIcon } from '@phosphor-icons/react';
import { Badge } from '@/components/ui/badge';

const testSlackBlocks: Block[] = [
  {
    type: 'header',
    text: { type: 'plain_text', text: '🔍 Story Thread Found', emoji: true }
  },
  {
    type: 'section',
    text: { type: 'mrkdwn', text: '*Climate Change Coverage*\nThis thread shows the evolution of climate reporting over the past decade.' }
  },
  {
    type: 'context',
    elements: [
      { type: 'mrkdwn', text: '12 articles | High relevance' }
    ]
  },
  {
    type: 'divider'
  },
  {
    type: 'section',
    text: { type: 'mrkdwn', text: '*Key Milestones:*\n• 2015: Paris Agreement coverage\n• 2018: IPCC special report\n• 2021: COP26 summit' },
    fields: [
      { type: 'mrkdwn', text: '*Thread Type:*\nEvergreen' },
      { type: 'mrkdwn', text: '*Articles:*\n12' }
    ]
  },
  {
    type: 'actions',
    elements: [
      {
        type: 'button',
        text: { type: 'plain_text', text: 'View Details', emoji: true },
        action_id: 'view_details',
        style: 'primary'
      },
      {
        type: 'button',
        text: { type: 'plain_text', text: 'Dismiss', emoji: true },
        action_id: 'dismiss'
      }
    ]
  }
];

export default function ResultsPanel() {
  const [threads, setThreads] = useState<ProactiveThread[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchMessages = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getProactiveSuggestions(10, true);
      if (response.success) {
        setThreads(response.threads);
        setLastUpdated(response.generated_at);
      } else {
        setError('Failed to fetch messages');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while fetching messages');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch messages on mount
  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  const getThreadTypeColor = (type: string) => {
    switch (type) {
      case 'evergreen':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'event_driven':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'novel_concept':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="bg-card rounded-lg shadow-sm border border-border p-6">
      {/* Header with refresh */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <ChatCircleTextIcon className="size-5" />
            Trending Story Messages
          </h2>
          {lastUpdated && (
            <p className="text-xs text-muted-foreground mt-1">
              Last updated: {formatTimestamp(lastUpdated)}
            </p>
          )}
        </div>
        <Button
          onClick={fetchMessages}
          disabled={loading}
          variant="outline"
          size="sm"
        >
          {loading ? (
            <SpinnerIcon className="size-4 animate-spin" />
          ) : (
            <ArrowsClockwiseIcon className="size-4" />
          )}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {/* Loading State */}
      {loading && threads.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <SpinnerIcon className="size-8 animate-spin mx-auto mb-4" />
          <p>Fetching Slack messages...</p>
          <p className="text-sm mt-2">Loading trend analysis results</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm mb-4">
          <p className="font-medium">Error loading messages</p>
          <p>{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && threads.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg mb-2">No trending messages yet</p>
          <p className="text-sm">
            Run the Trends analysis to generate Slack messages with emerging trends and related stories
          </p>
        </div>
      )}

      {/* Messages List */}
      {threads.length > 0 && (
        <div className="space-y-6">
          {threads.map((thread, index) => (
            <Collapsible
              key={thread.thread_id}
              title={
                <div className="flex items-center gap-3">
                  <span className="font-medium">{thread.central_topic}</span>
                  <Badge variant="outline" className={getThreadTypeColor(thread.thread_type)}>
                    {thread.thread_type.replace('_', ' ')}
                  </Badge>
                  <span className="text-xs text-gray-500">
                    {thread.article_count} articles
                  </span>
                </div>
              }
              defaultOpen={index === 0}
            >
              <Message
                blocks={thread.blocks as Block[]}
                name="Story Thread Bot"
                logo="/bot-logo.png"
                time={new Date()}
              />
            </Collapsible>
          ))}
        </div>
      )}

      {/* Test Block (for development) */}
      <Collapsible title="Sample Slack Block (Test)" defaultOpen={false} className="mt-8 pt-6 border-t border-border">
        <Message
          blocks={testSlackBlocks}
          name="Story Thread Bot"
          logo="/bot-logo.png"
          time={new Date()}
        />
      </Collapsible>
    </div>
  );
}
