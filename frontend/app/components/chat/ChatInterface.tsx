'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { PaperPlaneRightIcon, TextTIcon, FileTextIcon, TrashIcon, TrendUpIcon, ArrowsClockwiseIcon } from '@phosphor-icons/react';
import { analyzeText, analyzeArticle, getProactiveSuggestions, purgeQueue, triggerTrendsWatch, triggerWatchCached } from '@/app/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Message } from 'slack-blocks-to-jsx';
import type { Block } from 'slack-blocks-to-jsx';
import 'slack-blocks-to-jsx/dist/style.css';
import { Thread, ProactiveThread } from '@/app/types/blocks';

type MessageType = 'user-text' | 'user-article' | 'system' | 'trend';

interface ChatMessage {
  id: string;
  type: MessageType;
  content: string;
  timestamp: Date;
  threads?: Thread[];
  proactiveThread?: ProactiveThread;
  blocks?: Block[];
  isLoading?: boolean;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [articleId, setArticleId] = useState('');
  const [inputMode, setInputMode] = useState<'text' | 'article'>('text');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingTrends, setIsLoadingTrends] = useState(false);
  const [isPurgingQueue, setIsPurgingQueue] = useState(false);
  const [isTriggeringWatch, setIsTriggeringWatch] = useState(false);
  const [lastTrendUpdate, setLastTrendUpdate] = useState<string | null>(null);
  const [purgeMessage, setPurgeMessage] = useState<string | null>(null);
  const [watchMessage, setWatchMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch proactive suggestions on mount
  const fetchTrendMessages = useCallback(async () => {
    setIsLoadingTrends(true);
    try {
      const response = await getProactiveSuggestions(10, true);
      if (response.success && response.threads.length > 0) {
        setLastTrendUpdate(response.generated_at);
        
        // Convert proactive threads to chat messages
        const trendMessages: ChatMessage[] = response.threads.map((thread) => ({
          id: `trend-${thread.thread_id}`,
          type: 'trend',
          content: thread.central_topic,
          timestamp: new Date(response.generated_at),
          proactiveThread: thread,
        }));
        
        setMessages((prev) => {
          // Remove existing trend messages
          const withoutTrends = prev.filter((m) => m.type !== 'trend');
          return [...trendMessages, ...withoutTrends];
        });
      }
    } catch (error) {
      console.error('Error fetching trend messages:', error);
    } finally {
      setIsLoadingTrends(false);
    }
  }, []);

  useEffect(() => {
    fetchTrendMessages();
  }, [fetchTrendMessages]);

  const handlePurgeQueue = async () => {
    setIsPurgingQueue(true);
    setPurgeMessage(null);
    try {
      const response = await purgeQueue();
      setPurgeMessage(response.message);
      // Refresh trends after purge
      await fetchTrendMessages();
    } catch (error) {
      console.error('Error purging queue:', error);
      setPurgeMessage(error instanceof Error ? error.message : 'Failed to purge queue');
    } finally {
      setIsPurgingQueue(false);
      // Clear message after 5 seconds
      setTimeout(() => setPurgeMessage(null), 5000);
    }
  };

  const handleTriggerWatch = async () => {
    setIsTriggeringWatch(true);
    setWatchMessage(null);
    try {
      const response = await triggerTrendsWatch(false);
      setWatchMessage(`✅ Found ${response.new_matches} matches from ${response.trends_checked} trends`);
      // Refresh trends after watch cycle
      await fetchTrendMessages();
    } catch (error) {
      console.error('Error triggering watch:', error);
      const errorMsg = error instanceof Error ? error.message : 'Failed to trigger watch';
      // Check if it's a rate limit error
      if (errorMsg.includes('429') || errorMsg.includes('rate limit')) {
        setWatchMessage('⚠️ Google Trends rate limited. Use "Watch Cached" button instead.');
      } else {
        setWatchMessage(errorMsg);
      }
    } finally {
      setIsTriggeringWatch(false);
      // Clear message after 5 seconds
      setTimeout(() => setWatchMessage(null), 5000);
    }
  };

  const handleTriggerWatchCached = async () => {
    setIsTriggeringWatch(true);
    setWatchMessage(null);
    try {
      const response = await triggerWatchCached(10);
      setWatchMessage(`✅ Found ${response.new_matches} matches from ${response.trends_checked} cached trends (no Google API call)`);
      // Refresh trends after watch cycle
      await fetchTrendMessages();
    } catch (error) {
      console.error('Error triggering cached watch:', error);
      setWatchMessage(error instanceof Error ? error.message : 'Failed to trigger cached watch');
    } finally {
      setIsTriggeringWatch(false);
      // Clear message after 5 seconds
      setTimeout(() => setWatchMessage(null), 5000);
    }
  };

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const handleSendMessage = async () => {
    const content = inputMode === 'text' ? inputText.trim() : articleId.trim();
    if (!content || isLoading) return;

    // Create user message
    const userMessage: ChatMessage = {
      id: generateId(),
      type: inputMode === 'text' ? 'user-text' : 'user-article',
      content,
      timestamp: new Date(),
    };

    // Create loading system message
    const loadingMessage: ChatMessage = {
      id: generateId(),
      type: 'system',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setIsLoading(true);

    // Clear input
    if (inputMode === 'text') {
      setInputText('');
    } else {
      setArticleId('');
    }

    try {
      let result;
      const options = { include_trends: false }; // Direct Infactory search, no trend correlation
      if (inputMode === 'text') {
        result = await analyzeText(content, options);
      } else {
        result = await analyzeArticle(content, options);
      }

      if (result.success && result.data.threads.length > 0) {
        // Replace loading message with results
        setMessages((prev) => {
          const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id);
          
          // Add a summary message first
          const summaryMessage: ChatMessage = {
            id: generateId(),
            type: 'system',
            content: `Found ${result.data.threads.length} relevant story thread${result.data.threads.length > 1 ? 's' : ''}`,
            timestamp: new Date(),
            threads: result.data.threads,
          };
          
          return [...withoutLoading, summaryMessage];
        });
      } else {
        // No results found
        setMessages((prev) => {
          const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id);
          const noResultsMessage: ChatMessage = {
            id: generateId(),
            type: 'system',
            content: 'No relevant story threads found for this query.',
            timestamp: new Date(),
          };
          return [...withoutLoading, noResultsMessage];
        });
      }
    } catch (error) {
      // Error message
      setMessages((prev) => {
        const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id);
        const errorMessage: ChatMessage = {
          id: generateId(),
          type: 'system',
          content: error instanceof Error ? error.message : 'An error occurred while analyzing.',
          timestamp: new Date(),
        };
        return [...withoutLoading, errorMessage];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages((prev) => prev.filter((m) => m.type === 'trend'));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

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

  const hasUserMessages = messages.some((m) => m.type.startsWith('user'));

  return (
    <Card className="w-full flex flex-col h-[calc(100vh-200px)] min-h-[500px]">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">Story Search</span>
          <Badge variant="outline" className="text-xs">
            {messages.filter((m) => m.type !== 'trend').length} messages
          </Badge>
          {lastTrendUpdate && (
            <span className="text-xs text-muted-foreground">
              Trends updated: {new Date(lastTrendUpdate).toLocaleTimeString()}
            </span>
          )}
          {purgeMessage && (
            <span className="text-xs text-green-600 font-medium">
              {purgeMessage}
            </span>
          )}
          {watchMessage && (
            <span className="text-xs text-blue-600 font-medium">
              {watchMessage}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchTrendMessages}
            disabled={isLoadingTrends}
            className="text-muted-foreground hover:text-foreground"
          >
            {isLoadingTrends ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
            ) : (
              <ArrowsClockwiseIcon className="size-4" />
            )}
            <span className="ml-1">Refresh Trends</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePurgeQueue}
            disabled={isPurgingQueue}
            className="text-muted-foreground hover:text-foreground"
            title="Clear cached trend blocks and regenerate"
          >
            {isPurgingQueue ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
            ) : (
              <TrashIcon className="size-4" />
            )}
            <span className="ml-1">Purge Queue</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleTriggerWatch}
            disabled={isTriggeringWatch}
            className="text-muted-foreground hover:text-foreground"
            title="Run trends watch cycle with Google Trends"
          >
            {isTriggeringWatch ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
            ) : (
              <TrendUpIcon className="size-4" />
            )}
            <span className="ml-1">Run Watch</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleTriggerWatchCached}
            disabled={isTriggeringWatch}
            className="text-muted-foreground hover:text-foreground"
            title="Use cached trends only (no Google API call) - for 429 errors"
          >
            {isTriggeringWatch ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
            ) : (
              <ArrowsClockwiseIcon className="size-4" />
            )}
            <span className="ml-1">Watch Cached</span>
          </Button>
          {hasUserMessages && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearChat}
              className="text-muted-foreground hover:text-foreground"
            >
              <TrashIcon className="size-4 mr-1" />
              Clear Chat
            </Button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-4">
            <div className="text-center space-y-2">
              <p className="text-lg font-medium">Start a conversation</p>
              <p className="text-sm">Paste article text or enter an article ID to find related stories</p>
            </div>
            <div className="flex gap-2 text-xs">
              <Badge variant="secondary">Text Analysis</Badge>
              <Badge variant="secondary">Article Lookup</Badge>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.type.startsWith('user') ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[85%] space-y-1 ${
                  message.type.startsWith('user') ? 'items-end' : 'items-start'
                }`}
              >
                {/* Message Bubble */}
                <div
                  className={`rounded-lg px-4 py-2 ${
                    message.type === 'user-text'
                      ? 'bg-primary text-primary-foreground'
                      : message.type === 'user-article'
                      ? 'bg-secondary text-secondary-foreground'
                      : message.type === 'trend'
                      ? 'bg-muted border border-border'
                      : 'bg-muted'
                  }`}
                >
                  {message.isLoading ? (
                    <div className="flex items-center gap-2 py-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
                      <span className="text-sm">Analyzing...</span>
                    </div>
                  ) : message.type.startsWith('user') ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-xs opacity-70">
                        {message.type === 'user-text' ? (
                          <TextTIcon className="size-3" />
                        ) : (
                          <FileTextIcon className="size-3" />
                        )}
                        <span>{message.type === 'user-text' ? 'Text Query' : 'Article ID'}</span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>
                  ) : message.type === 'trend' ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <TrendUpIcon className="size-4 text-primary" />
                        <span className="text-sm font-semibold text-foreground">Trend Alert</span>
                        {message.proactiveThread && (
                          <Badge variant="outline" className={`text-xs ${getThreadTypeColor(message.proactiveThread.thread_type)}`}>
                            {message.proactiveThread.thread_type.replace('_', ' ')}
                          </Badge>
                        )}
                      </div>
                      {message.proactiveThread && (
                        <Message
                          blocks={message.proactiveThread.blocks as Block[]}
                          name="Trend Bot"
                          logo="/bot-logo.png"
                          time={message.timestamp}
                        />
                      )}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {message.content && (
                        <p className="text-sm font-medium">{message.content}</p>
                      )}
                      {message.threads && message.threads.map((thread) => (
                        <div key={thread.thread_id} className="border-t border-border/50 pt-2 first:border-t-0 first:pt-0">
                          <Message
                            blocks={thread.blocks as Block[]}
                            name="Archive Bot"
                            logo="/bot-logo.png"
                            time={message.timestamp}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Timestamp */}
                <span className="text-xs text-muted-foreground px-1">
                  {formatTime(message.timestamp)}
                </span>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </CardContent>

      {/* Input Area */}
      <div className="border-t border-border p-4 space-y-3 bg-card">
        {/* Input Mode Toggle */}
        <div className="flex gap-2">
          <Button
            variant={inputMode === 'text' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setInputMode('text')}
            className="flex-1"
          >
            <TextTIcon className="size-4 mr-2" />
            Text
          </Button>
          <Button
            variant={inputMode === 'article' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setInputMode('article')}
            className="flex-1"
          >
            <FileTextIcon className="size-4 mr-2" />
            Article ID
          </Button>
        </div>

        {/* Input Field */}
        <div className="flex gap-2">
          <div className="flex-1">
            {inputMode === 'text' ? (
              <Textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Paste article content or draft here..."
                className="min-h-[80px] resize-none"
                disabled={isLoading}
              />
            ) : (
              <Input
                value={articleId}
                onChange={(e) => setArticleId(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter article ID (e.g., atlantic_12345)"
                disabled={isLoading}
              />
            )}
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={
              isLoading ||
              (inputMode === 'text' ? !inputText.trim() : !articleId.trim())
            }
            className="h-auto px-4"
          >
            <PaperPlaneRightIcon className="size-5" />
          </Button>
        </div>

        <p className="text-xs text-muted-foreground text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </Card>
  );
}
