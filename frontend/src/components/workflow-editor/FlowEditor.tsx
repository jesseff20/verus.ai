'use client';

import { useCallback, useRef, useState, useMemo } from 'react';
import { useTheme } from 'next-themes';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  Node,
  Edge,
  ReactFlowProvider,
  useReactFlow,
  BackgroundVariant,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Save, Upload, ZoomIn, ZoomOut, Maximize2, Undo2, Redo2,
  CheckCircle2, AlertCircle, Loader2
} from 'lucide-react';

import SwimLaneNode from './nodes/SwimLaneNode';
import TaskNode from './nodes/TaskNode';
import GatewayNode from './nodes/GatewayNode';
import EventNode from './nodes/EventNode';
import PropertiesPanel from './PropertiesPanel';
import NodePalette from './NodePalette';

import { useSaveFlow, usePublishFlow, FlowNodeDto, FlowEdgeDto } from '@/hooks/useFlowTemplates';
import type { FlowTemplateDetail } from '@/hooks/useFlowTemplates';

/* ── Node type registry ─────────────────────────────────────── */
const NODE_TYPES = {
  swimlane: SwimLaneNode,
  task: TaskNode,
  user_task: TaskNode,
  service_task: TaskNode,
  start_event: EventNode,
  end_event: EventNode,
  intermediate_event: EventNode,
  exclusive_gateway: GatewayNode,
  parallel_gateway: GatewayNode,
  inclusive_gateway: GatewayNode,
};

/* ── Helpers ─────────────────────────────────────────────────── */
function templateToFlow(template: FlowTemplateDetail): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = template.nodes.map((n) => ({
    id: n.node_id,
    type: n.node_type,
    position: { x: n.position.x ?? 0, y: n.position.y ?? 0 },
    data: {
      label: n.label,
      role: n.role,
      description: n.description ?? '',
      node_type: n.node_type,
    },
    parentId: n.parent_node_id || undefined,
    extent: n.parent_node_id ? ('parent' as const) : undefined,
    style: n.node_type === 'swimlane'
      ? { width: n.position.width ?? 900, height: n.position.height ?? 160 }
      : undefined,
    zIndex: n.node_type === 'swimlane' ? -1 : 1,
  }));

  const edges: Edge[] = template.edges.map((e) => ({
    id: e.edge_id,
    source: e.source_node_id,
    target: e.target_node_id,
    sourceHandle: e.source_handle || null,
    targetHandle: e.target_handle || null,
    label: e.label || undefined,
    data: { condition: e.condition },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#6D28D9', width: 16, height: 16 },
    style: { stroke: '#6D28D940', strokeWidth: 1.5 },
    labelStyle: { fill: '#9CA3AF', fontSize: 10 },
    labelBgStyle: { fill: 'var(--rf-label-bg, #0A0A0A)', fillOpacity: 0.85 },
  }));

  return { nodes, edges };
}

function flowToDto(nodes: Node[], edges: Edge[]): { nodes: FlowNodeDto[]; edges: FlowEdgeDto[] } {
  const dtoNodes: FlowNodeDto[] = nodes.map((n, i) => ({
    node_id: n.id,
    node_type: n.type ?? 'task',
    label: (n.data.label as string) ?? '',
    description: (n.data.description as string) ?? '',
    role: (n.data.role as string) ?? 'any',
    parent_node_id: n.parentId ?? '',
    position: {
      x: n.position.x,
      y: n.position.y,
      width: n.measured?.width ?? (n.style?.width as number) ?? undefined,
      height: n.measured?.height ?? (n.style?.height as number) ?? undefined,
    },
    data: {},
    order: i,
  }));

  const dtoEdges: FlowEdgeDto[] = edges.map((e) => ({
    edge_id: e.id,
    source_node_id: e.source,
    target_node_id: e.target,
    source_handle: e.sourceHandle ?? '',
    target_handle: e.targetHandle ?? '',
    label: (e.label as string) ?? '',
    condition: (e.data?.condition as string) ?? '',
    data: {},
  }));

  return { nodes: dtoNodes, edges: dtoEdges };
}

/* ── Editor inner (needs ReactFlow context) ─────────────────── */
type EditorProps = {
  template: FlowTemplateDetail;
  initialNodes: Node[];
  initialEdges: Edge[];
};

function EditorInner({ template, initialNodes, initialEdges }: EditorProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [publishState, setPublishState] = useState<'idle' | 'publishing' | 'published' | 'error'>('idle');
  const [publishErrors, setPublishErrors] = useState<string[]>([]);

  const reactFlow = useReactFlow();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const saveFlow = useSaveFlow(template.id);
  const publishFlow = usePublishFlow(template.id);

  const isSystemTemplate = template.is_system_template;

  /* ── Connect ── */
  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            markerEnd: { type: MarkerType.ArrowClosed, color: '#6D28D9', width: 16, height: 16 },
            style: { stroke: '#6D28D940', strokeWidth: 1.5 },
          },
          eds,
        ),
      ),
    [setEdges],
  );

  /* ── Drop from palette ── */
  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      const raw = event.dataTransfer.getData('application/verus-node');
      if (!raw) return;

      const { nodeType, label } = JSON.parse(raw);
      const position = reactFlow.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node = {
        id: `${nodeType}-${Date.now()}`,
        type: nodeType,
        position,
        data: {
          label,
          role: 'any',
          description: '',
          node_type: nodeType,
        },
        style: nodeType === 'swimlane' ? { width: 900, height: 160 } : undefined,
        zIndex: nodeType === 'swimlane' ? -1 : 1,
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [reactFlow, setNodes],
  );

  /* ── Node update from properties panel ── */
  const handleNodeUpdate = useCallback(
    (nodeId: string, changes: Partial<{ label: string; role: string; description: string }>) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, ...changes } }
            : n,
        ),
      );
      setSelectedNode((prev) =>
        prev?.id === nodeId
          ? { ...prev, data: { ...prev.data, ...changes } }
          : prev,
      );
    },
    [setNodes],
  );

  /* ── Save ── */
  const handleSave = useCallback(async () => {
    if (isSystemTemplate) return;
    setSaveState('saving');
    const { nodes: dtoNodes, edges: dtoEdges } = flowToDto(nodes, edges);
    try {
      await saveFlow.mutateAsync({
        name: template.name,
        description: template.description,
        category: template.category,
        nodes: dtoNodes,
        edges: dtoEdges,
      });
      setSaveState('saved');
      setTimeout(() => setSaveState('idle'), 2500);
    } catch {
      setSaveState('error');
      setTimeout(() => setSaveState('idle'), 3000);
    }
  }, [isSystemTemplate, nodes, edges, saveFlow, template]);

  /* ── Publish ── */
  const handlePublish = useCallback(async () => {
    if (isSystemTemplate) return;
    setPublishState('publishing');
    setPublishErrors([]);
    try {
      await publishFlow.mutateAsync('');
      setPublishState('published');
      setTimeout(() => setPublishState('idle'), 3000);
    } catch (err: unknown) {
      const details = (err as { response?: { data?: { details?: string[] } } })
        ?.response?.data?.details ?? [];
      setPublishErrors(details);
      setPublishState('error');
    }
  }, [isSystemTemplate, publishFlow]);

  /* ── UI ── */
  return (
    <div className="flex flex-col" style={{ height: '100%', ['--rf-label-bg' as string]: isDark ? '#0A0A0A' : '#ffffff' }}>
      {/* Toolbar */}
      <div
        className={`flex items-center gap-2 px-4 h-12 border-b shrink-0 ${
          isDark ? 'bg-[#0A0A0A] border-[#1A1A1A]' : 'bg-white border-gray-200'
        }`}
      >
        <span className={`text-sm font-medium mr-2 truncate max-w-[200px] ${isDark ? 'text-white/70' : 'text-gray-700'}`}>
          {template.name}
        </span>
        <span
          className="text-[10px] px-2 py-0.5 rounded-full border font-mono"
          style={{
            color: template.status === 'published' ? '#22C55E' : '#F59E0B',
            borderColor: template.status === 'published' ? '#22C55E40' : '#F59E0B40',
            background: template.status === 'published' ? '#22C55E10' : '#F59E0B10',
          }}
        >
          {template.status === 'published' ? 'publicado' : 'rascunho'}
        </span>

        <div className="flex-1" />

        {/* Zoom controls */}
        <button
          onClick={() => reactFlow.zoomIn()}
          className={`w-7 h-7 rounded flex items-center justify-center transition-all ${isDark ? 'text-white/40 hover:text-white hover:bg-white/10' : 'text-gray-400 hover:text-gray-700 hover:bg-gray-100'}`}
          title="Zoom in"
        >
          <ZoomIn size={14} />
        </button>
        <button
          onClick={() => reactFlow.zoomOut()}
          className={`w-7 h-7 rounded flex items-center justify-center transition-all ${isDark ? 'text-white/40 hover:text-white hover:bg-white/10' : 'text-gray-400 hover:text-gray-700 hover:bg-gray-100'}`}
          title="Zoom out"
        >
          <ZoomOut size={14} />
        </button>
        <button
          onClick={() => reactFlow.fitView({ padding: 0.1 })}
          className={`w-7 h-7 rounded flex items-center justify-center transition-all ${isDark ? 'text-white/40 hover:text-white hover:bg-white/10' : 'text-gray-400 hover:text-gray-700 hover:bg-gray-100'}`}
          title="Ajustar à tela"
        >
          <Maximize2 size={14} />
        </button>

        <div className={`w-px h-5 mx-1 ${isDark ? 'bg-white/10' : 'bg-gray-200'}`} />

        {/* Save */}
        {!isSystemTemplate && (
          <>
            <button
              onClick={handleSave}
              disabled={saveState === 'saving'}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all"
              style={{
                borderColor: saveState === 'error' ? '#EF444440' : '#7030A040',
                background: saveState === 'saved' ? '#22C55E15' : saveState === 'error' ? '#EF444415' : '#7030A015',
                color: saveState === 'saved' ? '#22C55E' : saveState === 'error' ? '#EF4444' : '#C084FC',
              }}
            >
              {saveState === 'saving' ? (
                <Loader2 size={13} className="animate-spin" />
              ) : saveState === 'saved' ? (
                <CheckCircle2 size={13} />
              ) : saveState === 'error' ? (
                <AlertCircle size={13} />
              ) : (
                <Save size={13} />
              )}
              {saveState === 'saving' ? 'Salvando...' : saveState === 'saved' ? 'Salvo' : saveState === 'error' ? 'Erro' : 'Salvar'}
            </button>

            <button
              onClick={handlePublish}
              disabled={publishState === 'publishing'}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{
                background: publishState === 'published' ? '#22C55E' : publishState === 'error' ? '#EF4444' : '#7030A0',
                color: '#fff',
                opacity: publishState === 'publishing' ? 0.7 : 1,
              }}
            >
              {publishState === 'publishing' ? (
                <Loader2 size={13} className="animate-spin" />
              ) : publishState === 'published' ? (
                <CheckCircle2 size={13} />
              ) : publishState === 'error' ? (
                <AlertCircle size={13} />
              ) : (
                <Upload size={13} />
              )}
              {publishState === 'publishing' ? 'Publicando...' : publishState === 'published' ? 'Publicado!' : publishState === 'error' ? 'Falhou' : 'Publicar'}
            </button>
          </>
        )}

        {isSystemTemplate && (
          <span className={`text-[11px] italic ${isDark ? 'text-white/25' : 'text-gray-400'}`}>Template de sistema (somente leitura)</span>
        )}
      </div>

      {/* Publish errors */}
      {publishErrors.length > 0 && (
        <div
          className="px-4 py-2 text-xs border-b space-y-0.5 bg-red-500/5 border-red-500/20 text-red-400"
        >
          {publishErrors.map((e, i) => (
            <p key={i}>• {e}</p>
          ))}
        </div>
      )}

      {/* Canvas area */}
      <div className="flex-1 relative" ref={reactFlowWrapper}>
        {!isSystemTemplate && <NodePalette />}

        <div
          style={{
            position: 'absolute',
            left: isSystemTemplate ? 0 : 180,
            right: selectedNode ? 280 : 0,
            top: 0,
            bottom: 0,
          }}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={NODE_TYPES}
            onNodeClick={(_, node) => setSelectedNode(node)}
            onPaneClick={() => setSelectedNode(null)}
            onDrop={onDrop}
            onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }}
            fitView
            fitViewOptions={{ padding: 0.1 }}
            nodesDraggable={!isSystemTemplate}
            nodesConnectable={!isSystemTemplate}
            elementsSelectable={true}
            style={{ background: isDark ? '#080808' : '#f8fafc' }}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1}
              color={isDark ? '#1F1F1F' : '#cbd5e1'}
            />
            <Controls
              style={{
                background: isDark ? '#0F0F0F' : '#ffffff',
                border: isDark ? '1px solid #1F1F1F' : '1px solid #e2e8f0',
              }}
              showInteractive={false}
            />
            <MiniMap
              style={{
                background: isDark ? '#0A0A0A' : '#f1f5f9',
                border: isDark ? '1px solid #1F1F1F' : '1px solid #e2e8f0',
              }}
              nodeColor={isDark ? '#7030A040' : '#7030A060'}
              maskColor={isDark ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.7)'}
            />
          </ReactFlow>
        </div>

        {selectedNode && (
          <PropertiesPanel
            node={selectedNode}
            onUpdate={handleNodeUpdate}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </div>
    </div>
  );
}

/* ── Public export (wrapped with provider) ──────────────────── */
export default function FlowEditor({ template }: { template: FlowTemplateDetail }) {
  const { nodes: initialNodes, edges: initialEdges } = templateToFlow(template);

  return (
    <ReactFlowProvider>
      <EditorInner
        template={template}
        initialNodes={initialNodes}
        initialEdges={initialEdges}
      />
    </ReactFlowProvider>
  );
}
