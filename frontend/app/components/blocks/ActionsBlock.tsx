import { ActionsBlock } from '@/app/types/blocks';

interface ActionsBlockRendererProps {
  block: ActionsBlock;
  onAction?: (actionId: string, value: string) => void;
}

export function ActionsBlockRenderer({ block, onAction }: ActionsBlockRendererProps) {
  const handleClick = (element: { action_id?: string; value?: string; style?: 'primary' | 'danger' }) => {
    if (onAction) {
      onAction(element.action_id || 'button', element.value || '');
    }
  };

  return (
    <div className="flex flex-wrap gap-2 py-2">
      {block.elements.map((element, idx) => (
        <button
          key={idx}
          onClick={() => handleClick(element)}
          className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
            element.style === 'primary'
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : element.style === 'danger'
              ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
          }`}
        >
          {element.text.text}
        </button>
      ))}
    </div>
  );
}
