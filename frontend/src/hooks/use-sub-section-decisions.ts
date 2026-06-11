'use client';

import { useState, useEffect, useCallback } from 'react';
import type { BlueprintSubSection, SubSectionDecision } from '@/types';

type SubSectionsMap = Record<number, BlueprintSubSection[]>;

/**
 * Decide o `action` inicial de uma sub-seção no primeiro render.
 *
 * - `'generate'` quando a sub tem campos estruturados (`section_fields`) ou
 *   agente gerador. Sem isso, o `SubSectionPanel` não renderiza os campos
 *   condicionais e o usuário precisa clicar em outra opção e voltar pra
 *   forçar o handler a derivar o action.
 * - `'default'` caso contrário (cai no `default_text` da sub).
 */
function deriveSubSectionAction(
  sub: Pick<BlueprintSubSection, 'section_fields' | 'generator_agent_name'>,
): SubSectionDecision['action'] {
  const hasFieldsOrAgent =
    (sub.section_fields && sub.section_fields.length > 0) ||
    !!sub.generator_agent_name;
  return hasFieldsOrAgent ? 'generate' : 'default';
}

/**
 * Gerencia o estado e o ciclo de vida das decisões de sub-seções (grupos OU)
 * usadas nas telas de geração de documento (ETP, TR, Anexos, Edital).
 *
 * Inicialização:
 * - Itens únicos: cria entrada com action derivado por `deriveSubSectionAction`.
 * - Grupos OU (mais de uma opção com o mesmo `sub_number`): cria entrada
 *   apenas na última opção do grupo - convenção do projeto: a última é a
 *   "padrão / sem detalhamento" do blueprint.
 */
export function useSubSectionDecisions(subSectionsMap: SubSectionsMap) {
  const [decisions, setDecisions] = useState<Record<string, SubSectionDecision>>({});

  useEffect(() => {
    const allSubs = Object.values(subSectionsMap).flat();
    if (allSubs.length === 0) return;

    const bySubNumber = new Map<string, BlueprintSubSection[]>();
    allSubs.forEach((sub) => {
      const list = bySubNumber.get(sub.sub_number) || [];
      list.push(sub);
      bySubNumber.set(sub.sub_number, list);
    });

    setDecisions((prev) => {
      const next = { ...prev };
      let changed = false;

      bySubNumber.forEach((group) => {
        if (group.length === 1) {
          const sub = group[0];
          if (!next[sub.sub_key]) {
            next[sub.sub_key] = {
              action: deriveSubSectionAction(sub),
              fields_data: {},
              feedback: '',
            };
            changed = true;
          }
        } else {
          const hasAnyDecision = group.some((s) => next[s.sub_key]);
          if (!hasAnyDecision) {
            const lastSub = group[group.length - 1];
            next[lastSub.sub_key] = {
              action: deriveSubSectionAction(lastSub),
              fields_data: {},
              feedback: '',
            };
            changed = true;
          }
        }
      });

      return changed ? next : prev;
    });
  }, [subSectionsMap]);

  const onChange = useCallback(
    (subKey: string, decision: SubSectionDecision | null) => {
      setDecisions((prev) => {
        const next = { ...prev };
        if (decision === null) {
          delete next[subKey];
        } else {
          next[subKey] = decision;
        }
        return next;
      });
    },
    [],
  );

  const reset = useCallback(() => {
    setDecisions({});
  }, []);

  return { decisions, onChange, reset };
}
