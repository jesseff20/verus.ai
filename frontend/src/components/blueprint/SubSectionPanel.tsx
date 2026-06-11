'use client';

import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { SectionFieldsForm } from './SectionFieldsForm';
import { Info, Sparkles, FileText } from 'lucide-react';
import type { BlueprintSubSection, SubSectionDecision } from '@/types';

interface SubSectionPanelProps {
  subSections: BlueprintSubSection[];
  decisions: Record<string, SubSectionDecision>;
  onDecisionChange: (subKey: string, decision: SubSectionDecision | null) => void;
}

type SubGroup = {
  subNumber: string;
  items: BlueprintSubSection[];
};

export function SubSectionPanel({
  subSections,
  decisions,
  onDecisionChange,
}: SubSectionPanelProps) {
  /* -- Agrupar por sub_number (preserva ordem) -- */
  const groups = useMemo<SubGroup[]>(() => {
    const map = new Map<string, BlueprintSubSection[]>();
    const order: string[] = [];
    for (const sub of subSections) {
      if (!map.has(sub.sub_number)) {
        map.set(sub.sub_number, []);
        order.push(sub.sub_number);
      }
      map.get(sub.sub_number)!.push(sub);
    }
    return order.map((num) => ({ subNumber: num, items: map.get(num)! }));
  }, [subSections]);

  /* -- Handlers: item único (sem OU) -- */
  const handleToggle = (sub: BlueprintSubSection, checked: boolean) => {
    const current = decisions[sub.sub_key];
    onDecisionChange(sub.sub_key, {
      action: checked ? 'generate' : 'default',
      fields_data: current?.fields_data || {},
      feedback: current?.feedback || '',
    });
  };

  const handleFieldsChange = (sub: BlueprintSubSection, values: Record<string, any>) => {
    const current = decisions[sub.sub_key];
    onDecisionChange(sub.sub_key, {
      action: current?.action || 'generate',
      fields_data: values,
      feedback: current?.feedback || '',
    });
  };

  const handleFeedbackChange = (sub: BlueprintSubSection, feedback: string) => {
    const current = decisions[sub.sub_key];
    onDecisionChange(sub.sub_key, {
      action: current?.action || 'generate',
      fields_data: current?.fields_data || {},
      feedback,
    });
  };

  /* -- OU toggle (2 opções) -- */
  const handleOuToggle = (group: SubGroup, checked: boolean) => {
    const [first, second] = group.items;
    const selected = checked ? first : second;
    const deselected = checked ? second : first;

    const hasFieldsOrAgent =
      (selected.section_fields && selected.section_fields.length > 0) ||
      !!selected.generator_agent_name;

    onDecisionChange(selected.sub_key, {
      action: hasFieldsOrAgent ? 'generate' : 'default',
      fields_data: decisions[selected.sub_key]?.fields_data || {},
      feedback: decisions[selected.sub_key]?.feedback || '',
    });
    onDecisionChange(deselected.sub_key, null); // remove
  };

  /* -- OU radio (3+ opções) -- */
  const handleOuSelect = (group: SubGroup, selectedKey: string) => {
    for (const sub of group.items) {
      if (sub.sub_key === selectedKey) {
        const hasFieldsOrAgent =
          (sub.section_fields && sub.section_fields.length > 0) ||
          !!sub.generator_agent_name;
        onDecisionChange(sub.sub_key, {
          action: hasFieldsOrAgent ? 'generate' : 'default',
          fields_data: decisions[sub.sub_key]?.fields_data || {},
          feedback: decisions[sub.sub_key]?.feedback || '',
        });
      } else {
        onDecisionChange(sub.sub_key, null); // remove
      }
    }
  };

  /* -- Achar opção selecionada num grupo OU -- */
  const getSelectedKey = (group: SubGroup): string | null => {
    for (const sub of group.items) {
      if (decisions[sub.sub_key]) return sub.sub_key;
    }
    return null;
  };

  /* -- Detalhes expandidos da sub selecionada -- */
  const renderSubDetails = (sub: BlueprintSubSection) => {
    const decision = decisions[sub.sub_key];
    const isGenerate = decision?.action === 'generate';
    const hasAgent = !!sub.generator_agent_name;

    return (
      <div className="mt-3 space-y-3">
        {isGenerate && hasAgent && (
          <div className="flex items-center gap-1.5 text-[10px] text-primary">
            <Sparkles size={10} />
            <span>Gerador: {sub.generator_agent_name}</span>
          </div>
        )}

        {isGenerate && sub.help_text && (
          <div className="flex items-start gap-1.5 p-2 bg-blue-50 rounded-lg">
            <Info size={12} className="text-blue-500 mt-0.5 shrink-0" />
            <p className="text-[11px] text-blue-700">{sub.help_text}</p>
          </div>
        )}

        {isGenerate && sub.section_fields && sub.section_fields.length > 0 && (
          <SectionFieldsForm
            fields={sub.section_fields}
            values={decision?.fields_data || {}}
            onChange={(values) => handleFieldsChange(sub, values)}
            compact
          />
        )}


        {!isGenerate && sub.default_text && (
          <div className="flex items-start gap-1.5 p-2 bg-slate-100 rounded-lg">
            <FileText size={12} className="text-slate-400 mt-0.5 shrink-0" />
            <p className="text-[11px] text-slate-500 italic line-clamp-3">
              {sub.default_text}
            </p>
          </div>
        )}
      </div>
    );
  };

  /* ═══════════════════════════════════════════════
     Renderização por tipo de grupo
     ═══════════════════════════════════════════════ */

  /* -- Item único (sem OU) -- */
  const renderSingle = (sub: BlueprintSubSection) => {
    const decision = decisions[sub.sub_key];
    const isGenerate = decision?.action === 'generate';

    return (
      <div
        key={sub.id}
        className={cn(
          'rounded-xl border p-3 transition-all',
          isGenerate ? 'border-primary/30 bg-primary/5' : 'border-slate-200 bg-slate-50/50'
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-400">{sub.sub_number}</span>
              <p className="text-sm font-medium leading-tight">{sub.sub_name}</p>
              {sub.is_required && (
                <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 bg-red-50 text-red-600 border-red-200">
                  Obrigatório
                </Badge>
              )}
            </div>
            {sub.description && (
              <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{sub.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[10px] font-medium text-slate-400 uppercase">
              {isGenerate ? 'Gerar' : 'N/A'}
            </span>
            <Switch
              checked={isGenerate}
              onCheckedChange={(checked) => handleToggle(sub, checked)}
              disabled={sub.is_required && !sub.default_text}
            />
          </div>
        </div>
        {renderSubDetails(sub)}
      </div>
    );
  };

  /* -- OU binário (2 opções) - 1 toggle -- */
  const renderOuToggle = (group: SubGroup) => {
    const [first, second] = group.items;
    const selectedKey = getSelectedKey(group);
    const isFirstSelected = selectedKey === first.sub_key;
    const activeSub = isFirstSelected ? first : second;

    return (
      <div
        key={`ou-${group.subNumber}`}
        className={cn(
          'rounded-xl border p-3 transition-all',
          isFirstSelected ? 'border-primary/30 bg-primary/5' : 'border-slate-200 bg-slate-50/50'
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-400">{group.subNumber}</span>
              <p className="text-sm font-medium leading-tight">{activeSub.sub_name}</p>
            </div>
            {activeSub.description && (
              <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{activeSub.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[10px] font-medium text-slate-400 uppercase">
              {isFirstSelected ? 'Sim' : 'Não'}
            </span>
            <Switch
              checked={isFirstSelected}
              onCheckedChange={(checked) => handleOuToggle(group, checked)}
            />
          </div>
        </div>
        {renderSubDetails(activeSub)}
      </div>
    );
  };

  /* -- OU múltiplo (3+ opções) - radio buttons -- */
  const renderOuRadio = (group: SubGroup) => {
    const selectedKey = getSelectedKey(group);
    const activeSub = selectedKey
      ? group.items.find((s) => s.sub_key === selectedKey) ?? null
      : null;

    return (
      <div
        key={`ou-${group.subNumber}`}
        className={cn(
          'rounded-xl border p-3 transition-all',
          activeSub ? 'border-primary/30 bg-primary/5' : 'border-slate-200 bg-slate-50/50'
        )}
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-bold text-slate-400">{group.subNumber}</span>
          <p className="text-sm font-medium leading-tight">Escolha uma opção:</p>
        </div>

        <RadioGroup
          value={selectedKey || ''}
          onValueChange={(key) => handleOuSelect(group, key)}
          className="space-y-2"
        >
          {group.items.map((sub) => (
            <div key={sub.id} className="flex items-start gap-2">
              <RadioGroupItem value={sub.sub_key} id={sub.sub_key} className="mt-0.5" />
              <Label
                htmlFor={sub.sub_key}
                className="text-xs font-medium cursor-pointer leading-tight"
              >
                {sub.sub_name}
              </Label>
            </div>
          ))}
        </RadioGroup>

        {activeSub && renderSubDetails(activeSub)}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {groups.map((group) => {
        if (group.items.length === 1) return renderSingle(group.items[0]);
        if (group.items.length === 2) return renderOuToggle(group);
        return renderOuRadio(group);
      })}
    </div>
  );
}
