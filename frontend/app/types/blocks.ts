// Block Kit type definitions for Slack-compatible UI rendering

export type BlockType = 
  | 'header' 
  | 'section' 
  | 'context' 
  | 'actions' 
  | 'divider'
  | 'image'
  | 'timeline';

export interface TextObject {
  type: 'plain_text' | 'mrkdwn';
  text: string;
  emoji?: boolean;
}

export interface ButtonElement {
  type: 'button';
  text: TextObject;
  action_id?: string;
  value?: string;
  style?: 'primary' | 'danger';
}

export interface ImageElement {
  type: 'image';
  image_url: string;
  alt_text: string;
}

export interface HeaderBlock {
  type: 'header';
  text: TextObject;
}

export interface SectionBlock {
  type: 'section';
  text?: TextObject;
  fields?: TextObject[];
  accessory?: ButtonElement | ImageElement;
}

export interface ContextBlock {
  type: 'context';
  elements: (TextObject | ImageElement)[];
}

export interface ActionsBlock {
  type: 'actions';
  elements: ButtonElement[];
}

export interface DividerBlock {
  type: 'divider';
}

export interface TimelineEvent {
  year: number;
  title: string;
  article_id: string;
}

export interface TimelineBlock {
  type: 'timeline';
  events: TimelineEvent[];
}

export type Block = 
  | HeaderBlock 
  | SectionBlock 
  | ContextBlock 
  | ActionsBlock 
  | DividerBlock
  | TimelineBlock;

// API response types
export interface AnalysisOptions {
  max_results?: number;
  include_trends?: boolean;
  threshold?: number;
  thread_types?: string[];
}

export interface ArticleReference {
  article_id: string;
  title: string;
  author?: string;
  published_date?: string;
  url?: string;
  excerpt?: string;
  relevance_score: number;
}

export interface Thread {
  thread_id: string;
  thread_type: 'evergreen' | 'event_driven' | 'novel_concept';
  central_topic: string;
  relevance_score: number;
  articles: ArticleReference[];
  blocks: Block[];
  explanation?: string;
}

export interface AnalysisResponse {
  success: boolean;
  data: {
    query_id: string;
    threads: Thread[];
    extracted_topics: string[];
    trend_data?: Record<string, unknown>;
  };
}

export interface ProactiveResponse {
  success: boolean;
  data: {
    generated_at: string;
    threads: Thread[];
  };
}

// Trends demo types
export interface TrendInfo {
  keyword: string;
  score: number;
  category: 'rising' | 'top' | 'breakout';
  velocity?: number;
}

export interface TrendMatch {
  trend_keyword: string;
  thread_id: string;
  priority_score: number;
  status: string;
}

export interface TrendsDemoResponse {
  success: boolean;
  message: string;
  trends_found: number;
  trends: TrendInfo[];
  queue_entries_added: number;
  top_matches: TrendMatch[];
}
