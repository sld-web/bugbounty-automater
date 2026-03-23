import { useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  BackgroundVariant,
  NodeTypes,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { cn } from '../../lib/utils';

export interface FlowCardData {
  id: string;
  name: string;
  card_type: 'ASSET' | 'FLOW' | 'ATTACK' | 'FINDING';
  status: 'NOT_STARTED' | 'RUNNING' | 'REVIEW' | 'DONE' | 'FLAGGED' | 'BLOCKED' | 'FAILED';
  description?: string;
  results?: Record<string, unknown>;
  logs?: string[];
  error?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  [key: string]: unknown;
}

interface FlowChartProps {
  cards: FlowCardData[];
  className?: string;
  onCardClick?: (card: FlowCardData) => void;
  selectedCardId?: string;
}

const statusColors: Record<string, { bg: string; border: string; text: string }> = {
  NOT_STARTED: { bg: 'bg-surface-100', border: 'border-white/20', text: 'text-white/50' },
  RUNNING: { bg: 'bg-secondary/20', border: 'border-secondary', text: 'text-secondary' },
  REVIEW: { bg: 'bg-warning/20', border: 'border-warning', text: 'text-warning' },
  DONE: { bg: 'bg-tertiary/20', border: 'border-tertiary', text: 'text-tertiary' },
  FLAGGED: { bg: 'bg-warning/20', border: 'border-warning', text: 'text-warning' },
  BLOCKED: { bg: 'bg-error/20', border: 'border-error', text: 'text-error' },
  FAILED: { bg: 'bg-error/20', border: 'border-error', text: 'text-error' },
};

const cardTypeIcons: Record<string, string> = {
  ASSET: '📦',
  FLOW: '🔄',
  ATTACK: '⚔️',
  FINDING: '🔍',
};

interface FlowCardNodeProps {
  data: FlowCardData;
  selected: boolean;
}

function FlowCardNode({ data, selected }: FlowCardNodeProps) {
  const colors = statusColors[data.status] || statusColors.NOT_STARTED;
  const icon = cardTypeIcons[data.card_type] || '📋';

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border min-w-[180px] transition-all backdrop-blur-sm',
        colors.bg,
        colors.border,
        selected && 'ring-2 ring-secondary'
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-white/30" />
      
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className={cn('font-semibold text-sm', colors.text)}>
          {data.name}
        </span>
      </div>
      
      <div className={cn('text-xs font-mono uppercase', colors.text)}>
        {data.status?.replace('_', ' ')}
      </div>
      
      {data.results && Object.keys(data.results).length > 0 && (
        <div className="mt-2 text-xs text-white/40 font-mono">
          {Object.keys(data.results).length} results
        </div>
      )}
      
      {data.error && (
        <div className="mt-2 text-xs text-error font-mono truncate">
          {data.error}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-white/30" />
    </div>
  );
}

const nodeTypes: NodeTypes = {
  flowCard: FlowCardNode as unknown as NodeTypes[string],
};

export function FlowChart({ cards, className, onCardClick, selectedCardId }: FlowChartProps) {
  const initialNodes = useMemo(() => {
    return cards.map((card, index) => ({
      id: card.id,
      type: 'flowCard',
      position: { x: 250, y: index * 150 },
      data: { ...card },
      selected: card.id === selectedCardId,
    } as Node));
  }, [cards, selectedCardId]);

  const initialEdges = useMemo(() => {
    return cards.slice(0, -1).map((card, i) => ({
      id: `e${card.id}-${cards[i + 1].id}`,
      source: card.id,
      target: cards[i + 1].id,
      type: 'smoothstep',
      animated: card.status === 'RUNNING',
      style: { strokeWidth: 2, stroke: 'rgba(0, 212, 255, 0.5)' },
    }));
  }, [cards]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: unknown, node: Node) => {
      if (onCardClick && node.data) {
        onCardClick(node.data as FlowCardData);
      }
    },
    [onCardClick],
  );

  if (cards.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-64 rounded-lg border border-dashed border-white/20', className)}>
        <div className="text-center">
          <p className="text-lg text-white/50 mb-2">No flow cards yet</p>
          <p className="text-sm text-white/30">Start a target to generate flow cards</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('h-96 rounded-lg border border-white/10', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls className="!bg-surface-100 !border-white/20 [&>button]:!bg-surface-100 [&>button]:!border-white/20 [&>button]:!text-white/70" />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as FlowCardData;
            return statusColors[data?.status || 'NOT_STARTED']?.bg || '#1d1f28';
          }}
          maskColor="rgba(12, 14, 20, 0.8)"
          className="!bg-surface-100"
        />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="rgba(255,255,255,0.1)" />
      </ReactFlow>
    </div>
  );
}
