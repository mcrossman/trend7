import { TimelineBlock } from '@/app/types/blocks';

interface TimelineBlockRendererProps {
  block: TimelineBlock;
}

export function TimelineBlockRenderer({ block }: TimelineBlockRendererProps) {
  const sortedEvents = [...block.events].sort((a, b) => a.year - b.year);

  return (
    <div className="py-3">
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {sortedEvents.map((event, index) => (
          <div key={index} className="flex items-center flex-shrink-0">
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">{event.year}</div>
              <div className="w-3 h-3 bg-blue-600 rounded-full mx-auto" />
              <div 
                className="text-xs text-gray-700 mt-1 max-w-[100px] truncate"
                title={event.title}
              >
                {event.title}
              </div>
            </div>
            {index < sortedEvents.length - 1 && (
              <div className="w-8 h-0.5 bg-gray-300 mx-2" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
