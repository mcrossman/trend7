'use client';

import { useState } from 'react';
import { Collapsible } from '@/components/ui/collapsible';
import { Message } from 'slack-blocks-to-jsx';
import type { Block } from 'slack-blocks-to-jsx';
import 'slack-blocks-to-jsx/dist/style.css';

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
  const [results] = useState(null);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        📊 Results
      </h2>

      <Collapsible title="Sample Slack Block (Test)" defaultOpen={true}>
        <Message
          blocks={testSlackBlocks}
          name="Story Thread Bot"
          logo="/bot-logo.png"
          time={new Date()}
        />
      </Collapsible>

      {!results && (
        <div className="text-center py-12 text-gray-500 mt-6">
          <p>Submit a query to see results</p>
          <p className="text-sm mt-2">
            Enter text or an article ID to find related story threads
          </p>
        </div>
      )}

      {results && (
        <div className="space-y-6 mt-6">
          <pre className="bg-gray-50 p-4 rounded-md overflow-auto">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
