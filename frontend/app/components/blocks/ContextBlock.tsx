import { ContextBlock, ImageElement, TextObject } from '@/app/types/blocks';

interface ContextBlockRendererProps {
  block: ContextBlock;
}

export function ContextBlockRenderer({ block }: ContextBlockRendererProps) {
  const renderElement = (element: TextObject | ImageElement, idx: number) => {
    if (element.type === 'mrkdwn') {
      return (
        <span
          key={idx}
          className="text-xs text-muted-foreground"
          dangerouslySetInnerHTML={{
            __html: (element as TextObject).text
              .replace(/\*(.+?)\*/g, '<strong class="text-foreground">$1</strong>')
          }}
        />
      );
    }
    if (element.type === 'plain_text') {
      return (
        <span key={idx} className="text-xs text-muted-foreground">
          {(element as TextObject).text}
        </span>
      );
    }
    if (element.type === 'image') {
      return (
        <img
          key={idx}
          src={(element as ImageElement).image_url}
          alt={(element as ImageElement).alt_text}
          className="w-4 h-4 rounded"
        />
      );
    }
    return null;
  };

  return (
    <div className="flex items-center gap-3 py-1">
      {block.elements.map((element, idx) => renderElement(element, idx))}
    </div>
  );
}
