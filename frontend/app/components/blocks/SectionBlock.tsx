import { SectionBlock, ButtonElement } from '@/app/types/blocks';

interface SectionBlockRendererProps {
  block: SectionBlock;
  onAction?: (actionId: string, value: string) => void;
}

export function SectionBlockRenderer({ block, onAction }: SectionBlockRendererProps) {
  const renderText = (text: { type: string; text: string }) => {
    if (text.type === 'mrkdwn') {
      // Simple markdown-like rendering
      return (
        <div
          className="text-sm text-foreground whitespace-pre-wrap"
          dangerouslySetInnerHTML={{
            __html: text.text
              .replace(/\*(.+?)\*/g, '<strong>$1</strong>')
              .replace(/_(.+?)_/g, '<em>$1</em>')
              .replace(/`(.+?)`/g, '<code class="bg-muted px-1 rounded">$1</code>')
              .replace(/&gt; (.+)/g, '<blockquote class="border-l-4 border-border pl-3 my-2 text-muted-foreground">$1</blockquote>')
          }}
        />
      );
    }
    return <p className="text-sm text-foreground">{text.text}</p>;
  };

  const handleAccessoryClick = () => {
    if (block.accessory && block.accessory.type === 'button' && onAction) {
      const btn = block.accessory as ButtonElement;
      onAction(btn.action_id || 'button', btn.value || '');
    }
  };

  return (
    <div className="py-2">
      <div className="flex items-start gap-4">
        <div className="flex-1">
          {block.text && renderText(block.text)}

          {block.fields && (
            <div className="grid grid-cols-2 gap-4 mt-2">
              {block.fields.map((field, idx) => (
                <div key={idx}>{renderText(field)}</div>
              ))}
            </div>
          )}
        </div>

        {block.accessory && block.accessory.type === 'button' && (
          <button
            onClick={handleAccessoryClick}
            className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
              block.accessory.style === 'primary'
                ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                : block.accessory.style === 'danger'
                ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            {block.accessory.text.text}
          </button>
        )}
      </div>
    </div>
  );
}
