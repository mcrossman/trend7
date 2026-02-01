import { HeaderBlock } from '@/app/types/blocks';

interface HeaderBlockRendererProps {
  block: HeaderBlock;
}

export function HeaderBlockRenderer({ block }: HeaderBlockRendererProps) {
  return (
    <div className="py-2">
      <h3 className="text-xl font-bold text-foreground">
        {block.text.text}
      </h3>
    </div>
  );
}
