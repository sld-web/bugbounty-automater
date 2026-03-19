import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Edge,
  Connection,
  BackgroundVariant,
  NodeTypes,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { cn } from '../../utils/helpers';

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
}

interface FlowChartProps {
  cards: FlowCardData[];
  className?: string;
  onCardClick?: (card: FlowCardData) => void;
  selectedCardId?: string;
}

const statusColors: Record<string, { bg: string; border: string; text: string }> = {
  NOT_STARTED: { bg: 'bg-gray-100', border: 'border-gray-300', text: 'text-gray-600' },
  RUNNING: { bg: 'bg-blue-100', border: 'border-blue-500', text: 'text-blue-700' },
  REVIEW: { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-700' },
  DONE: { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-700' },
  FLAGGED: { bg: 'bg-orange-100', border: 'border-orange-500', text: 'text-orange-700' },
  BLOCKED: { bg: 'bg-purple-100', border: 'border-purple-500', text: 'text-purple-700' },
  FAILED: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-700' },
};

const cardTypeIcons: Record<string, string> = {
  ASSET: '📦',
  FLOW: '🔄',
  ATTACK: '⚔️',
  FINDING: '🔍',
};

function FlowCardNode({ data, selected }: { data: FlowCardData; selected: boolean }) {
  const colors = statusColors[data.status] || statusColors.NOT_STARTED;
  const icon = cardTypeIcons[data.card_type] || '📋';

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[180px] transition-all',
        colors.bg,
        colors.border,
        selected && 'ring-2 ring-offset-2 ring-blue-500',
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className={cn('font-semibold text-sm', colors.text)}>
          {data.name}
        </span>
      </div>
      
      <div className={cn('text-xs', colors.text)}>
        {data.status.replace('_', ' ')}
      </div>
      
      {data.results && Object.keys(data.results).length > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          {Object.keys(data.results).length} results
        </div>
      )}
      
      {data.error && (
        <div className="mt-2 text-xs text-red-600 truncate">
          {data.error}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    </div>
  );
}

const nodeTypes: NodeTypes = {
  flowCard: FlowCardNode as unknown as NodeTypes['placeholder'],
};

export function FlowChart({ cards, className, onCardClick, selectedCardId }: FlowChartProps) {
  const initialNodes = useMemo(() => {
    return cards.map((card, index) => ({
      id: card.id,
      type: 'flowCard',
      position: { x: 250, y: index * 150 },
      data: card,
      selected: card.id === selectedCardId,
    }));
  }, [cards, selectedCardId]);

  const initialEdges = useMemo(() => {
    const edges: Edge[] = [];
    for (let i = 0; i < cards.length - 1; i++) {
      edges.push({
        id: `e${cards[i].id}-${cards[i + 1].id}`,
        source: cards[i].id,
        target: cards[i + 1].id,
        type: 'smoothstep',
        animated: cards[i].status === 'RUNNING',
        style: { strokeWidth: 2 },
      });
    }
    return edges;
  }, [cards]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

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
      <div className={cn('flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300', className)}>
        <div className="text-center text-gray-500">
          <p className="text-lg mb-2">No flow cards yet</p>
          <p className="text-sm">Start a target to generate flow cards</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('h-96 rounded-lg border border-gray-200', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as FlowCardData;
            return statusColors[data?.status]?.bg || '#e5e7eb';
          }}
        />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
