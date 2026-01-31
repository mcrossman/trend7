import { ActionsBlock } from '@/app/types/blocks';

interface ActionsBlockRendererProps {
  block: ActionsBlock;
  onAction?: (actionId: string, value: string) => void;
}

export function ActionsBlockRenderer({ block, onAction }: ActionsBlockRendererProps) {
  const handleClick = (element: any) => {
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
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : element.style === 'danger'
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
        >
          {element.text.text}
        </button>
      ))}
    </div>
  );
}
