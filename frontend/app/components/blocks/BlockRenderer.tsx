import { Block } from '@/app/types/blocks';
import { HeaderBlockRenderer } from './HeaderBlock';
import { SectionBlockRenderer } from './SectionBlock';
import { ContextBlockRenderer } from './ContextBlock';
import { ActionsBlockRenderer } from './ActionsBlock';
import { DividerBlockRenderer } from './DividerBlock';
import { TimelineBlockRenderer } from './TimelineBlock';

interface BlockRendererProps {
  blocks: Block[];
  onAction?: (actionId: string, value: string) => void;
}

export default function BlockRenderer({ blocks, onAction }: BlockRendererProps) {
  return (
    <div className="space-y-3">
      {blocks.map((block, index) => (
        <BlockComponent
          key={index}
          block={block}
          onAction={onAction}
        />
      ))}
    </div>
  );
}

interface BlockComponentProps {
  block: Block;
  onAction?: (actionId: string, value: string) => void;
}

function BlockComponent({ block, onAction }: BlockComponentProps) {
  switch (block.type) {
    case 'header':
      return <HeaderBlockRenderer block={block} />;
    case 'section':
      return <SectionBlockRenderer block={block} onAction={onAction} />;
    case 'context':
      return <ContextBlockRenderer block={block} />;
    case 'actions':
      return <ActionsBlockRenderer block={block} onAction={onAction} />;
    case 'divider':
      return <DividerBlockRenderer />;
    case 'timeline':
      return <TimelineBlockRenderer block={block} />;
    default:
      return (
        <div className="text-sm text-destructive p-2 bg-destructive/10 rounded">
          Unknown block type
        </div>
      );
  }
}
