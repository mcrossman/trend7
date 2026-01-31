import { ContextBlock } from '@/app/types/blocks';

interface ContextBlockRendererProps {
  block: ContextBlock;
}

export function ContextBlockRenderer({ block }: ContextBlockRendererProps) {
  const renderElement = (element: any, idx: number) => {
    if (element.type === 'mrkdwn') {
      return (
        <span 
          key={idx}
          className="text-xs text-gray-500"
          dangerouslySetInnerHTML={{
            __html: element.text
              .replace(/\*(.+?)\*/g, '<strong class="text-gray-700">$1</strong>')
          }}
        />
      );
    }
    if (element.type === 'plain_text') {
      return (
        <span key={idx} className="text-xs text-gray-500">
          {element.text}
        </span>
      );
    }
    if (element.type === 'image') {
      return (
        <img 
          key={idx}
          src={element.image_url}
          alt={element.alt_text}
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
