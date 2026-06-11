'use client';

import { useState, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { SectionFieldsForm } from '@/components/blueprint/SectionFieldsForm';

// CodeEditor com syntax highlight pra JSON - dynamic import (client-only,
// usa document/window internamente).
const CodeEditor = dynamic(
  () => import('@uiw/react-textarea-code-editor').then((m) => m.default),
  { ssr: false }
);
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { DocumentBlueprint, BlueprintSection, BlueprintSubSection } from '@/types';
import { useBlueprints } from '@/hooks/use-blueprints';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { useToast } from '@/hooks/use-toast';
import {
  Plus,
  GripVertical,
  Trash2,
  Save,
  ChevronRight,
  Loader2,
  Layers,
  X,
  ChevronsUpDown,
} from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import api from '@/lib/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// ========== ExpandableTextarea ==========

function ExpandableTextarea({
  value,
  onChange,
  onEnhance,
  placeholder,
  disabled,
  className,
  rows = 4,
  expandedRows = 12,
  label,
  enhanceContext,
}: {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onEnhance?: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  rows?: number;
  expandedRows?: number;
  label?: string;
  enhanceContext?: string;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="relative">
      <Textarea
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={expanded ? expandedRows : rows}
        disabled={disabled}
        className={`${className || ''} pr-36 transition-all`}
      />
      {onEnhance && (
        <div className="absolute top-1.5 right-8">
          <AIEnhanceButton
            value={value}
            onEnhance={onEnhance}
            context={enhanceContext || 'conteúdo de blueprint jurídico'}
            disabled={disabled}
          />
        </div>
      )}
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="absolute top-1.5 right-1.5 p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        title={expanded ? 'Recolher' : 'Expandir'}
      >
        <ChevronsUpDown className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

// ========== Helpers ==========

/** Generate a section_key from section_name: lowercase, replace spaces/special chars with _, remove accents */
function generateSectionKey(name: string): string {
  return name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // remove accents
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '_') // replace non-alphanumeric with _
    .replace(/^_|_$/g, ''); // trim leading/trailing _
}

// ========== Types ==========

interface SectionAgent {
  id: string;
  name: string;
  agent_type: string;
  is_active: boolean;
}

interface SectionsStepProps {
  blueprint: DocumentBlueprint;
  onUpdate: (blueprint: DocumentBlueprint) => void;
}

// ========== Sub-section editor (inline) ==========

interface SubSectionEditorProps {
  subSection: BlueprintSubSection;
  agents: SectionAgent[];
  onSave: (data: Partial<BlueprintSubSection>) => void;
  onDelete: () => void;
  isSaving: boolean;
}

function SubSectionEditor({ subSection, agents, onSave, onDelete, isSaving }: SubSectionEditorProps) {
  const [subNumber, setSubNumber] = useState(subSection.sub_number || '');
  const [subName, setSubName] = useState(subSection.sub_name || '');
  const [subDescription, setSubDescription] = useState(subSection.description || '');
  const [defaultText, setDefaultText] = useState(subSection.default_text || '');
  const [generatorAgentId, setGeneratorAgentId] = useState(
    subSection.generator_agent_id || ''
  );

  const handleSave = () => {
    onSave({
      sub_number: subNumber,
      sub_name: subName,
      sub_key: generateSectionKey(subName),
      description: subDescription,
      default_text: defaultText,
      generator_agent: generatorAgentId && generatorAgentId !== 'none' ? generatorAgentId : null,
    });
  };

  return (
    <div className="border rounded-lg p-3 space-y-3 bg-muted/30">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Sub-seção {subSection.sub_number || 'Nova'}
        </p>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 text-destructive hover:text-destructive"
          onClick={onDelete}
          disabled={isSaving}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Numero</Label>
          <Input
            value={subNumber}
            onChange={(e) => setSubNumber(e.target.value)}
            placeholder="1.1"
            className="h-8 text-sm"
            disabled={isSaving}
          />
        </div>
        <div className="col-span-3 space-y-1">
          <Label className="text-xs">Nome</Label>
          <Input
            value={subName}
            onChange={(e) => setSubName(e.target.value)}
            placeholder="Nome da sub-secao"
            className="h-8 text-sm"
            disabled={isSaving}
          />
        </div>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Descricao</Label>
        <div className="relative">
          <Textarea
            value={subDescription}
            onChange={(e) => setSubDescription(e.target.value)}
            placeholder="Descricao da sub-secao..."
            rows={2}
            className="text-sm resize-none pr-32"
            disabled={isSaving}
          />
          <div className="absolute top-1 right-1">
            <AIEnhanceButton
              value={subDescription}
              onEnhance={setSubDescription}
              context="descrição de sub-seção de blueprint jurídico"
              disabled={isSaving}
            />
          </div>
        </div>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Texto Padrao</Label>
        <div className="relative">
          <Textarea
            value={defaultText}
            onChange={(e) => setDefaultText(e.target.value)}
            placeholder="Texto padrao quando a IA nao gera conteudo..."
            rows={10}
            className="text-sm resize-y min-h-[240px] pr-32"
            disabled={isSaving}
          />
          <div className="absolute top-1 right-1">
            <AIEnhanceButton
              value={defaultText}
              onEnhance={setDefaultText}
              context="texto padrão de sub-seção de documento jurídico"
              objective="Melhore a qualidade, clareza e precisão jurídica do texto"
              disabled={isSaving}
            />
          </div>
        </div>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Agente Gerador</Label>
        <Select value={generatorAgentId} onValueChange={setGeneratorAgentId} disabled={isSaving}>
          <SelectTrigger className="h-8 text-sm">
            <SelectValue placeholder="Selecione um agente..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Nenhum</SelectItem>
            {agents
              .filter((a) => a.agent_type === 'generator' && a.is_active)
              .map((agent) => (
                <SelectItem key={agent.id} value={agent.id}>
                  {agent.name}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex justify-end">
        <Button size="sm" variant="outline" onClick={handleSave} disabled={isSaving}>
          {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5 mr-1" />}
          Salvar Sub-secao
        </Button>
      </div>
    </div>
  );
}

// ========== Sortable section item ==========

interface SortableSectionItemProps {
  section: BlueprintSection;
  isSelected: boolean;
  onSelect: (section: BlueprintSection) => void;
}

function SortableSectionItem({ section, isSelected, onSelect }: SortableSectionItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: section.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 50 : undefined,
  };

  return (
    <div ref={setNodeRef} style={style}>
      <button
        onClick={() => onSelect(section)}
        className={`w-full flex items-center gap-2 p-2.5 rounded-md text-left transition-all text-sm
          ${
            isSelected
              ? 'bg-primary/10 border border-primary/30 text-primary'
              : 'hover:bg-muted/50 border border-transparent'
          }
        `}
      >
        <span
          {...attributes}
          {...listeners}
          className="touch-none"
          onClick={(e) => e.stopPropagation()}
        >
          <GripVertical className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0 cursor-grab" />
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-muted-foreground">
              {section.section_number}.
            </span>
            <span className="truncate font-medium text-xs">
              {section.section_name}
            </span>
          </div>
          <div className="flex items-center gap-1 mt-1">
            {section.is_active && (
              <Badge variant="secondary" className="text-[9px] px-1 py-0 h-3.5">
                Ativo
              </Badge>
            )}
            {section.is_required && (
              <Badge variant="outline" className="text-[9px] px-1 py-0 h-3.5 border-red-200 text-red-600">
                Obrigatorio
              </Badge>
            )}
          </div>
        </div>
        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      </button>
    </div>
  );
}

// ========== Main component ==========

export function SectionsStep({ blueprint, onUpdate }: SectionsStepProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { useBlueprintSections } = useBlueprints();

  // Selected section
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);

  // Section form state
  const [sectionForm, setSectionForm] = useState<{
    section_number: number;
    section_name: string;
    section_key: string;
    description: string;
    instructions: string;
    legal_reference: string;
    is_required: boolean;
    allow_skip: boolean;
    is_active: boolean;
    generator_agent_id: string;
    validator_agent_id: string;
    section_fields_json: string;
  }>({
    section_number: 1,
    section_name: '',
    section_key: '',
    description: '',
    instructions: '',
    legal_reference: '',
    is_required: true,
    allow_skip: false,
    is_active: true,
    generator_agent_id: '',
    validator_agent_id: '',
    section_fields_json: '[]',
  });

  // Preview do formulario derivado do section_fields_json - usado pra
  // mostrar o resultado renderizado ao lado do editor JSON.
  const [previewValues, setPreviewValues] = useState<Record<string, any>>({});
  const { parsedFields, jsonError } = useMemo(() => {
    const raw = sectionForm.section_fields_json?.trim() || '';
    if (!raw) return { parsedFields: [], jsonError: null as string | null };
    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        return { parsedFields: [], jsonError: 'Esperado um array.' };
      }
      return { parsedFields: parsed, jsonError: null as string | null };
    } catch (err: any) {
      return { parsedFields: [], jsonError: err.message || 'JSON inválido.' };
    }
  }, [sectionForm.section_fields_json]);

  // Fetch sections
  const {
    data: sectionsData,
    isLoading: isLoadingSections,
  } = useBlueprintSections(blueprint.id);

  const sections: BlueprintSection[] = sectionsData?.sections || blueprint.sections || [];

  // Fetch agents
  const { data: agentsData } = useQuery({
    queryKey: ['section-agents'],
    queryFn: async () => {
      const response = await api.get<{ agents?: SectionAgent[]; results?: SectionAgent[] } | SectionAgent[]>(
        '/api/v1/intelligent-assistant/section-agents/'
      );
      const data = response.data;
      if (Array.isArray(data)) return data;
      if ('agents' in data && data.agents) return data.agents;
      if ('results' in data && data.results) return data.results;
      return [];
    },
  });

  const agents: SectionAgent[] = Array.isArray(agentsData) ? agentsData : [];

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Sorted sections (by order, then section_number)
  const sortedSections = useMemo(
    () => [...sections].sort((a, b) => (a.order ?? a.section_number) - (b.order ?? b.section_number)),
    [sections]
  );

  // Reorder handler
  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const oldIndex = sortedSections.findIndex((s) => s.id === active.id);
      const newIndex = sortedSections.findIndex((s) => s.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;

      const reordered = [...sortedSections];
      const [moved] = reordered.splice(oldIndex, 1);
      reordered.splice(newIndex, 0, moved);

      const sectionIds = reordered.map((s) => s.id);

      try {
        await api.put(
          `/api/v1/intelligent-assistant/blueprints/${blueprint.id}/sections/reorder/`,
          { section_ids: sectionIds }
        );
        queryClient.invalidateQueries({ queryKey: ['blueprint-sections', blueprint.id] });
        queryClient.invalidateQueries({ queryKey: ['blueprint', blueprint.id] });
        toast({ title: 'Ordem atualizada!' });
      } catch {
        toast({ title: 'Erro ao reordenar', variant: 'destructive' });
      }
    },
    [sortedSections, blueprint.id, queryClient, toast]
  );

  // Populate form when section is selected
  const selectSection = useCallback(
    (section: BlueprintSection) => {
      setSelectedSectionId(section.id);
      setSectionForm({
        section_number: section.section_number,
        section_name: section.section_name,
        section_key: section.section_key,
        description: section.description || '',
        instructions: section.instructions || '',
        legal_reference: section.legal_reference || '',
        is_required: section.is_required,
        allow_skip: section.allow_skip,
        is_active: section.is_active,
        generator_agent_id: section.generator_agent_id || section.generator_agent?.id || '',
        validator_agent_id: section.validator_agent_id || section.validator_agent?.id || '',
        section_fields_json: JSON.stringify(section.section_fields || [], null, 2),
      });
    },
    []
  );

  const selectedSection = sections.find((s) => s.id === selectedSectionId);

  // Auto-generate section_key from name
  const handleNameChange = (value: string) => {
    setSectionForm((prev) => ({
      ...prev,
      section_name: value,
      section_key: generateSectionKey(value),
    }));
  };

  // ========== Mutations ==========

  // Create section
  const createSectionMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, any> = {
        blueprint: blueprint.id,
        section_number: (sections.length > 0
          ? Math.max(...sections.map((s) => s.section_number)) + 1
          : 1),
        section_name: 'Nova Secao',
        section_key: `nova_secao_${Date.now()}`,
        description: '',
        order: sections.length + 1,
        is_required: true,
        allow_skip: false,
        is_active: true,
      };
      const response = await api.post<BlueprintSection>(
        `/api/v1/intelligent-assistant/blueprints/${blueprint.id}/sections/create/`,
        payload
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections', blueprint.id] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', blueprint.id] });
      toast({ title: 'Seção criada!' });
      selectSection(data);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.response?.data?.error || 'Erro ao criar seção.';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    },
  });

  // Update section
  const updateSectionMutation = useMutation({
    mutationFn: async () => {
      if (!selectedSectionId) throw new Error('Nenhuma seção selecionada');

      let parsedFields: any[] = [];
      try {
        parsedFields = JSON.parse(sectionForm.section_fields_json);
      } catch {
        // If JSON is invalid, keep empty
      }

      const payload: Record<string, any> = {
        section_number: sectionForm.section_number,
        section_name: sectionForm.section_name,
        section_key: sectionForm.section_key,
        description: sectionForm.description,
        instructions: sectionForm.instructions,
        legal_reference: sectionForm.legal_reference,
        is_required: sectionForm.is_required,
        allow_skip: sectionForm.allow_skip,
        is_active: sectionForm.is_active,
        section_fields: parsedFields,
      };

      // Add agent IDs if set
      if (sectionForm.generator_agent_id && sectionForm.generator_agent_id !== 'none') {
        payload.generator_agent = sectionForm.generator_agent_id;
      } else {
        payload.generator_agent = null;
      }
      if (sectionForm.validator_agent_id && sectionForm.validator_agent_id !== 'none') {
        payload.validator_agent = sectionForm.validator_agent_id;
      } else {
        payload.validator_agent = null;
      }

      const response = await api.patch<BlueprintSection>(
        `/api/v1/intelligent-assistant/blueprints/${blueprint.id}/sections/${selectedSectionId}/`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections', blueprint.id] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', blueprint.id] });
      toast({ title: 'Seção atualizada!' });
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.response?.data?.error || 'Erro ao atualizar seção.';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    },
  });

  // Delete section
  const deleteSectionMutation = useMutation({
    mutationFn: async (sectionId: string) => {
      await api.delete(
        `/api/v1/intelligent-assistant/blueprints/${blueprint.id}/sections/${sectionId}/delete/`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprint-sections', blueprint.id] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', blueprint.id] });
      setSelectedSectionId(null);
      toast({ title: 'Seção removida!' });
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.response?.data?.error || 'Erro ao remover seção.';
      toast({ title: 'Erro', description: message, variant: 'destructive' });
    },
  });

  const isSaving =
    createSectionMutation.isPending ||
    updateSectionMutation.isPending ||
    deleteSectionMutation.isPending;

  // ========== Render ==========

  return (
    <div className="flex gap-4 min-h-[calc(100vh-12rem)]">
      {/* Left panel: Sections list */}
      <div className="w-72 shrink-0 flex flex-col border rounded-lg">
        <div className="p-3 border-b bg-muted/30">
          <h3 className="text-sm font-semibold">Secoes</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {sections.length} secao(es) cadastrada(s)
          </p>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {isLoadingSections ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : sections.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <Layers className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-xs">Nenhuma seção cadastrada</p>
              </div>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={sortedSections.map((s) => s.id)}
                  strategy={verticalListSortingStrategy}
                >
                  {sortedSections.map((section) => (
                    <SortableSectionItem
                      key={section.id}
                      section={section}
                      isSelected={selectedSectionId === section.id}
                      onSelect={selectSection}
                    />
                  ))}
                </SortableContext>
              </DndContext>
            )}
          </div>
        </ScrollArea>

        {/* Add section button */}
        <div className="p-2 border-t">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => createSectionMutation.mutate()}
            disabled={isSaving}
          >
            {createSectionMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Plus className="h-4 w-4 mr-1" />
            )}
            Adicionar Secao
          </Button>
        </div>
      </div>

      {/* Right panel: Section editor */}
      <div className="flex-1 min-w-0 flex flex-col">
        {!selectedSectionId ? (
          // Empty state
          <div className="flex flex-col items-center justify-center flex-1 text-muted-foreground gap-3">
            <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
              <Layers className="h-8 w-8 opacity-50" />
            </div>
            <p className="text-sm font-medium">Selecione uma seção para editar</p>
            <p className="text-xs">Clique em uma seção na lista ao lado ou crie uma nova.</p>
          </div>
        ) : (
          <Card>
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  Seção {sectionForm.section_number}: {sectionForm.section_name || '(sem nome)'}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setSelectedSectionId(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Basic fields */}
              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Numero</Label>
                  <Input
                    type="number"
                    value={sectionForm.section_number}
                    onChange={(e) =>
                      setSectionForm((prev) => ({ ...prev, section_number: parseInt(e.target.value) || 0 }))
                    }
                    disabled={isSaving}
                    className="h-9"
                  />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label className="text-xs">Nome da Secao</Label>
                  <Input
                    value={sectionForm.section_name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="Nome da secao"
                    disabled={isSaving}
                    className="h-9"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Chave</Label>
                  <Input
                    value={sectionForm.section_key}
                    onChange={(e) =>
                      setSectionForm((prev) => ({ ...prev, section_key: e.target.value }))
                    }
                    placeholder="section_key"
                    disabled={isSaving}
                    className="h-9 font-mono text-xs"
                  />
                </div>
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label className="text-xs">Descricao</Label>
                <ExpandableTextarea
                  value={sectionForm.description}
                  onChange={(e) =>
                    setSectionForm((prev) => ({ ...prev, description: e.target.value }))
                  }
                  onEnhance={(text) =>
                    setSectionForm((prev) => ({ ...prev, description: text }))
                  }
                  enhanceContext="descrição de seção de blueprint jurídico"
                  placeholder="Descreva o objetivo desta secao..."
                  rows={4}
                  expandedRows={10}
                  disabled={isSaving}
                  className="text-sm"
                />
              </div>

              {/* Instructions */}
              <div className="space-y-2">
                <Label className="text-xs">Instrucoes para o Agente</Label>
                <ExpandableTextarea
                  value={sectionForm.instructions}
                  onChange={(e) =>
                    setSectionForm((prev) => ({ ...prev, instructions: e.target.value }))
                  }
                  onEnhance={(text) =>
                    setSectionForm((prev) => ({ ...prev, instructions: text }))
                  }
                  enhanceContext="instruções para agente de IA gerar seção de documento jurídico"
                  placeholder="Instrucoes especificas para o agente de IA gerar esta secao..."
                  rows={5}
                  expandedRows={14}
                  disabled={isSaving}
                  className="text-sm"
                />
              </div>

              {/* Legal Reference */}
              <div className="space-y-2">
                <Label className="text-xs">Referencia Legal</Label>
                <Input
                  value={sectionForm.legal_reference}
                  onChange={(e) =>
                    setSectionForm((prev) => ({ ...prev, legal_reference: e.target.value }))
                  }
                  placeholder="Art. 18, Lei 14.133/2021"
                  disabled={isSaving}
                  className="h-9 text-sm"
                />
              </div>

              <Separator />

              {/* Agent selects */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Agente Gerador</Label>
                  <Select
                    value={sectionForm.generator_agent_id || 'none'}
                    onValueChange={(val) =>
                      setSectionForm((prev) => ({ ...prev, generator_agent_id: val }))
                    }
                    disabled={isSaving}
                  >
                    <SelectTrigger className="h-9 text-sm">
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nenhum</SelectItem>
                      {agents
                        .filter((a) => a.agent_type === 'generator' && a.is_active)
                        .map((agent) => (
                          <SelectItem key={agent.id} value={agent.id}>
                            {agent.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-xs">Agente Validador</Label>
                  <Select
                    value={sectionForm.validator_agent_id || 'none'}
                    onValueChange={(val) =>
                      setSectionForm((prev) => ({ ...prev, validator_agent_id: val }))
                    }
                    disabled={isSaving}
                  >
                    <SelectTrigger className="h-9 text-sm">
                      <SelectValue placeholder="Selecione..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Nenhum</SelectItem>
                      {agents
                        .filter((a) => a.agent_type === 'validator' && a.is_active)
                        .map((agent) => (
                          <SelectItem key={agent.id} value={agent.id}>
                            {agent.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Separator />

              {/* Flags */}
              <div className="flex flex-wrap gap-6">
                <div className="flex items-center gap-2">
                  <Switch
                    id="sec-required"
                    checked={sectionForm.is_required}
                    onCheckedChange={(val) =>
                      setSectionForm((prev) => ({ ...prev, is_required: val }))
                    }
                    disabled={isSaving}
                  />
                  <Label htmlFor="sec-required" className="text-xs">
                    Obrigatorio
                  </Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="sec-skip"
                    checked={sectionForm.allow_skip}
                    onCheckedChange={(val) =>
                      setSectionForm((prev) => ({ ...prev, allow_skip: val }))
                    }
                    disabled={isSaving}
                  />
                  <Label htmlFor="sec-skip" className="text-xs">
                    Permitir Pular
                  </Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="sec-active"
                    checked={sectionForm.is_active}
                    onCheckedChange={(val) =>
                      setSectionForm((prev) => ({ ...prev, is_active: val }))
                    }
                    disabled={isSaving}
                  />
                  <Label htmlFor="sec-active" className="text-xs">
                    Ativo
                  </Label>
                </div>
              </div>

              <Separator />

              {/* Section Fields - JSON editor + preview ao vivo */}
              <div className="space-y-2">
                <Label className="text-xs">Campos Estruturados</Label>
                <div className="grid grid-cols-2 gap-3">
                  {/* Esquerda: JSON editor com syntax highlight */}
                  <div className="space-y-1">
                    <p className="text-[10px] text-muted-foreground font-medium">JSON</p>
                    <div className="border rounded-md overflow-hidden">
                      <CodeEditor
                        value={sectionForm.section_fields_json}
                        language="json"
                        onChange={(e: any) =>
                          setSectionForm((prev) => ({ ...prev, section_fields_json: e.target.value }))
                        }
                        padding={12}
                        disabled={isSaving}
                        style={{
                          fontSize: 12,
                          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                          minHeight: 200,
                          backgroundColor: 'transparent',
                        }}
                      />
                    </div>
                    {jsonError && (
                      <p className="text-[10px] text-destructive">JSON inválido: {jsonError}</p>
                    )}
                  </div>

                  {/* Direita: preview do formulário renderizado ao vivo */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] text-muted-foreground font-medium">Preview do formulário</p>
                      {parsedFields && parsedFields.length > 0 && Object.keys(previewValues).length > 0 && (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="h-6 text-[10px] px-2"
                          onClick={() => {
                            // Mescla o que o admin digitou no preview como `default_value`
                            // em cada campo do JSON. Campos sem valor digitado não são
                            // alterados. Re-serializa o JSON com os defaults.
                            const updated = parsedFields.map((field: any) => {
                              const v = previewValues[field.name];
                              if (v === undefined || v === '' || (Array.isArray(v) && v.length === 0)) {
                                return field;
                              }
                              return { ...field, default_value: v };
                            });
                            setSectionForm((prev) => ({
                              ...prev,
                              section_fields_json: JSON.stringify(updated, null, 2),
                            }));
                            toast({
                              title: 'Padrão atualizado',
                              description: 'Os valores do preview foram salvos como padrão dos campos. Clique em "Salvar Seção" pra persistir.',
                            });
                          }}
                          disabled={isSaving}
                          title="Inserir os valores atuais como default_value em cada campo do JSON"
                        >
                          💾 Salvar como padrão
                        </Button>
                      )}
                    </div>
                    <div className="border rounded-md p-3 min-h-[200px] bg-muted/20">
                      {parsedFields && parsedFields.length > 0 ? (
                        <SectionFieldsForm
                          fields={parsedFields}
                          values={previewValues}
                          onChange={setPreviewValues}
                          compact
                        />
                      ) : (
                        <p className="text-xs text-muted-foreground italic">
                          {jsonError
                            ? 'Corrija o JSON pra ver o preview.'
                            : 'Adicione campos no JSON pra ver o preview aqui.'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-[10px] text-muted-foreground">
                  Esquerda: edite o JSON. Direita: preview em tempo real (campos <code>richtext</code> ficam como TinyMCE).
                </p>
              </div>

              <Separator />

              {/* Sub-sections */}
              <Accordion type="single" collapsible>
                <AccordionItem value="sub-sections" className="border-none">
                  <AccordionTrigger className="py-2 text-sm hover:no-underline">
                    <div className="flex items-center gap-2">
                      Sub-secoes
                      {selectedSection?.sub_sections && selectedSection.sub_sections.length > 0 && (
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
                          {selectedSection.sub_sections.length}
                        </Badge>
                      )}
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-3">
                      {selectedSection?.sub_sections && selectedSection.sub_sections.length > 0 ? (
                        selectedSection.sub_sections
                          .sort((a, b) => a.order - b.order)
                          .map((sub) => (
                            <SubSectionEditor
                              key={sub.id}
                              subSection={sub}
                              agents={agents}
                              onSave={async (data) => {
                                try {
                                  await api.patch(
                                    `/api/v1/intelligent-assistant/sub-sections/${sub.id}/`,
                                    data
                                  );
                                  queryClient.invalidateQueries({
                                    queryKey: ['blueprint-sections', blueprint.id],
                                  });
                                  toast({ title: 'Sub-seção atualizada!' });
                                } catch (err: any) {
                                  const message = err?.response?.data?.detail || 'Erro ao atualizar sub-secao.';
                                  toast({ title: 'Erro', description: message, variant: 'destructive' });
                                }
                              }}
                              onDelete={async () => {
                                try {
                                  await api.delete(
                                    `/api/v1/intelligent-assistant/sub-sections/${sub.id}/delete/`
                                  );
                                  queryClient.invalidateQueries({
                                    queryKey: ['blueprint-sections', blueprint.id],
                                  });
                                  toast({ title: 'Sub-seção removida!' });
                                } catch (err: any) {
                                  const message = err?.response?.data?.detail || 'Erro ao remover sub-secao.';
                                  toast({ title: 'Erro', description: message, variant: 'destructive' });
                                }
                              }}
                              isSaving={isSaving}
                            />
                          ))
                      ) : (
                        <p className="text-xs text-muted-foreground text-center py-3">
                          Nenhuma sub-seção cadastrada.
                        </p>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        disabled={isSaving}
                        onClick={async () => {
                          try {
                            const subCount = selectedSection?.sub_sections?.length || 0;
                            await api.post(
                              `/api/v1/intelligent-assistant/sections/${selectedSectionId}/sub-sections/`,
                              {
                                sub_number: `${sectionForm.section_number}.${subCount + 1}`,
                                sub_name: 'Nova Sub-secao',
                                sub_key: `nova_sub_secao_${Date.now()}`,
                                order: subCount + 1,
                                is_required: false,
                                is_active: true,
                              }
                            );
                            queryClient.invalidateQueries({
                              queryKey: ['blueprint-sections', blueprint.id],
                            });
                            toast({ title: 'Sub-seção criada!' });
                          } catch (err: any) {
                            const message = err?.response?.data?.detail || 'Erro ao criar sub-secao.';
                            toast({ title: 'Erro', description: message, variant: 'destructive' });
                          }
                        }}
                      >
                        <Plus className="h-3.5 w-3.5 mr-1" />
                        Adicionar Sub-secao
                      </Button>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              <Separator />

              {/* Action buttons */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    if (selectedSectionId) {
                      deleteSectionMutation.mutate(selectedSectionId);
                    }
                  }}
                  disabled={isSaving}
                >
                  {deleteSectionMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4 mr-1" />
                  )}
                  Excluir Secao
                </Button>

                <Button
                  onClick={() => updateSectionMutation.mutate()}
                  disabled={isSaving}
                >
                  {updateSectionMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Salvar Secao
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
