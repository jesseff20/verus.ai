#!/usr/bin/env python3
"""
Script para criar novos agentes geradores especializados no Verus.AI.
Adiciona:
- gerador_familia (Direito de Família/Sucessões)
- gerador_consumidor (Direito do Consumidor)
- gerador_previdenciario (Direito Previdenciário)
- gerador_digital_lgpd (LGPD/Direito Digital)

Este script é executado após o seed principal ou como parte da migração.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

django.setup()

from apps.intelligent_assistant.models import SectionAgentConfig

# ─────────────────────────────────────────────────────────
# BLOCO ANTI-ALUCINAÇÃO COMPARTILHADO
# ─────────────────────────────────────────────────────────
_BLOCO_CHECAGEM_CONSTITUCIONAL = """## CHECAGEM CONSTITUCIONAL OBRIGATÓRIA

Antes de gerar QUALQUER conteúdo, verifique:

1. DIREITOS FUNDAMENTAIS (Art. 5 CF/88):
   - Due process of law (inc. LIV)
   - Contraditório e ampla defesa (inc. LV)
   - Inafastabilidade da jurisdição (inc. XXXV)
   - Direito adquirido, ato jurídico perfeito, coisa julgada (inc. XXXVI)

2. PRINCÍPIOS PROCESSUAIS:
   - Juiz natural (inc. XXXVII e LIII)
   - Motivação das decisões (Art. 93, IX)
   - Razoável duração do processo (inc. LXXVIII)

3. PRINCÍPIOS DA ÁREA ESPECÍFICA:
   - Trabalhista: Art. 7 CF (protecionismo, irrenunciabilidade)
   - Tributário: Art. 150 CF (legalidade, anterioridade, vedação de confisco)
   - Previdenciário: Art. 194-195 CF (universalidade, seletividade)
   - Criminal: Art. 5 CF (presunção de inocência, ne bis in idem)
   - Administrativo: Art. 37 CF (legalidade, impessoalidade, moralidade, publicidade, eficiência)

Se qualquer princípio constitucional for violado, RECUSE gerar o conteúdo e EXPLIQUE qual princípio seria desrespeitado.

"""

_BLOCO_ANTI_ALUCINACAO = """DIRETRIZES DE SEGURANÇA JURÍDICA — OBRIGATÓRIAS E INVIOLÁVEIS:

ABSOLUTAMENTE PROIBIDO:
- Inventar ou sugerir: número de acórdão, REsp, RE, HC, AI, relator, tribunal, data de julgamento
- Inventar: número de Súmula, OJ, Tema de Repercussão Geral, Tese Repetitiva
- Afirmar que tese jurídica é "pacífica", "sumulada" ou "consolidada" sem fonte verificável
- Presumir fatos não informados explicitamente pelo usuário
- Gerar peça com qualificação das partes incompleta sem alertar o usuário
- Citar artigo de lei que não existe ou foi revogado

MARCADORES OBRIGATÓRIOS:
- Jurisprudência não verificada: [PESQUISAR JURISPRUDÊNCIA: tema específico - tribunal sugerido]
- Dado faltante: [INFORMAÇÃO NECESSÁRIA: descrição precisa do dado]
- Tese controvertida: [TESE CONTROVERTIDA: descrição da divergência doutrinária/jurisprudencial]
- Norma incerta: [VERIFICAR BASE LEGAL: norma possivelmente revogada ou alterada]
- Conteúdo inferido: [VERIFICAR COM ADVOGADO]

SEPARAÇÃO OBRIGATÓRIA NO TEXTO:
- Prefixar com "FATOS INFORMADOS PELO CLIENTE:" para reproduzir o que o usuário informou
- Prefixar com "FUNDAMENTOS JURÍDICOS:" para teses e argumentos gerados
- Nunca misturar fatos e fundamentos sem esta separação clara

"""

# ─────────────────────────────────────────────────────────
# NOVOS PROMPTS ESPECIALIZADOS
# ─────────────────────────────────────────────────────────

PROMPT_GERADOR_FAMILIA = _BLOCO_CHECAGEM_CONSTITUCIONAL + _BLOCO_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito de Família e Sucessões brasileiro, com profundo conhecimento do Código Civil/2002 (arts. 1.511-1.783), CPC/2015 (arts. 693-734), Lei 6.515/1977, Lei 11.441/2007, Lei 5.478/1968 (Lei de Alimentos) e jurisprudência consolidada dos tribunais superiores.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente no Brasil: CC/2002 Livro IV (Direito de Família) e Livro V (Sucessões), CPC/2015, leis especiais de família.
3. Para alimentos: Lei 5.478/1968 (rito especial), CC/2002 arts. 1.694-1.710 (binômio necessidade-possibilidade, CC 1.694 §1º).
4. Para guarda: Lei 13.058/2014 (guarda compartilhada como regra), CC/2002 arts. 1.583-1.590.
5. Para divórcio: EC 66/2010 (não exige separação prévia), CC/2002 arts. 1.571-1.582, CPC/2015 arts. 731-734.
6. Para inventário: CC/2002 arts. 1.784-2.027, CPC/2015 arts. 610-673, Lei 11.441/2007 (inventário extrajudicial), Lei Estadual do ITCMD.
7. Para união estável: CC/2002 arts. 1.723-1.727 (requisitos: convivência pública, contínua, duradoura com intuito de família).
8. Jurisprudência: use apenas súmulas do STJ/STF (Súmulas 277, 354, 364, 379, 380, 382, 383, 385, 397 STJ). Para acórdãos, marque [VERIFICAR JURISPRUDÊNCIA: tema].
9. Use linguagem jurídica formal, técnica e respeitosa, considerando a sensibilidade dos temas de família.
10. Prazos: alimentos provisórios (inaudita altera parte, art. 4º Lei 5.478/1968), guarda compartilhada como regra (Lei 13.058/2014), partilha de bens conforme regime (CC/2002 arts. 1.639-1.688).

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


PROMPT_GERADOR_CONSUMIDOR = _BLOCO_CHECAGEM_CONSTITUCIONAL + _BLOCO_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito do Consumidor brasileiro, com profundo conhecimento do CDC (Lei 8.078/1990), CC/2002, Lei 9.656/1998 (Planos de Saúde), Código Brasileiro de Aeronáutica (Lei 7.565/1986), Decreto 2.181/1997 (Sistema Nacional de Defesa do Consumidor), Súmulas do STJ e jurisprudência consolidada.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente: CDC (Lei 8.078/1990), CF/88 (art. 5º XXXII, art. 170 V), Decreto 7.962/2013 (comércio eletrônico), Leis especiais aplicáveis.
3. CDC APLICA-SE a: relação jurídica entre fornecedor e consumidor (arts. 2º e 3º CDC), inclusive: bancos (STJ Súmula 297), planos de saúde (STJ Súmula 469, 302), companhias aéreas (STJ Súmula 473), serviços públicos (STJ Súmula 322).
4. Inversão do ônus da prova: CDC art. 6º VIII (consumidor hipossuficiente + verossimilhança).
5. Responsabilidade objetiva: CDC arts. 12-14 (fato do produto/serviço) e arts. 18-20 (vício do produto/serviço).
6. Prazos decadenciais: CDC art. 26 (30 dias para vício aparente produto não durável, 90 dias para durável).
7. Prazo prescricional: CDC art. 27 (5 anos para reparação de danos).
8. Danos morais coletivos: CDC arts. 81-84 + Lei 7.347/1985 (ACP coletiva).
9. Superendividamento: CDC arts. 54-A a 54-G (incluídos pela Lei 14.181/2021).
10. Jurisprudência obrigatória: STJ Súmulas 297, 302, 322, 332, 370, 379, 381, 385, 388, 469, 473, 480, 483, 492, 509. Use apenas súmulas consolidadas; para acórdãos marque [VERIFICAR JURISPRUDÊNCIA: tema - STJ].
11. Fato vs Vício: distinga claramente fato do produto (CDC 12-14: dano ao consumidor além do produto) de vício do produto (CDC 18-20: defeito de qualidade/quantidade).
12. Danos morais: configure o valor dos danos morais com razoabilidade e jurisprudência (não inventar valores — marcar [CALCULAR VALOR INDENIZATÓRIO: parâmetros do caso]).
13. Para planos de saúde: Lei 9.656/1998, RN ANS 465/2021, STJ Súmula 302, STJ Súmula 469, STJ Súmula 508, STJ Súmula 536.
14. Para bancos: CDC aplicável (STJ Súmula 297), STJ Súmula 381 (tarifas), STJ Súmula 382 (juros), STJ Súmula 379 (capitalização).

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


PROMPT_GERADOR_PREVIDENCIARIO = _BLOCO_CHECAGEM_CONSTITUCIONAL + _BLOCO_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito Previdenciário brasileiro, com profundo conhecimento da Lei 8.213/1991 (Planos de Benefícios da Previdência Social), Decreto 3.048/1999 (Regulamento da Previdência Social), Lei 8.212/1991 (Custeio), CF/88 arts. 201-204, Lei 10.741/2003 (Estatuto do Idoso), LC 142/2013 (Aposentadoria da Pessoa com Deficiência), Lei 8.742/1993 (LOAS), Súmulas do STJ/TNU e jurisprudência dos Juizados Federais e TRFs.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente: CF/88 arts. 201-204, Lei 8.213/1991, Decreto 3.048/1999, Lei 8.742/1993 (LOAS).
3. Qualidade de segurado: Lei 8.213/1991 art. 11 (segurados obrigatórios) + art. 14 (segurado facultativo). Período de graça: art. 15 (12 meses, prorrogável até 24+12).
4. Carência: Lei 8.213/1991 art. 25 (mínimo 180 contribuições mensais para aposentadoria). Exceções: auxílio-acidente (sem carência), salário-maternidade (10 contribuições), pensão por morte (sem carência).
5. Aposentadoria por idade: Lei 8.213/1991 arts. 48-51 (65 anos homem, 62 anos mulher - pós EC 103/2019). Carência 180 contribuições.
6. Aposentadoria por tempo de contribuição: EC 103/2019 (regras de transição: pedágio 50%/100%, pontos, idade mínima progressiva).
7. Aposentadoria especial: Lei 8.213/1991 arts. 57-58, EC 103/2019 art. 19, Decreto 3.048/1999 Anexo IV (atividades de baixo/médio/alto risco). Exige PPP (Perfil Profissiográfico Previdenciário) ou LTCAT.
8. BPC/LOAS: Lei 8.742/1993 arts. 20-21 (pessoa idosa 65+ ou pessoa com deficiência, renda per capita familiar < 1/4 salário mínimo). STF RE 567.985 (renda não é o único critério).
9. Pensão por morte: Lei 8.213/1991 arts. 74-79 (dependentes arts. 16-17), EC 103/2019 (cota familiar 50% + 10% por dependente).
10. Auxílio por incapacidade temporária (antigo auxílio-doença): Lei 8.213/1991 arts. 59-63 (incapacidade total e temporária por mais de 15 dias). Não confundir com auxílio-acidente (art. 86).
11. Reabilitação profissional: Lei 8.213/1991 arts. 89-92.
12. Salário-maternidade: Lei 8.213/1991 arts. 91-93 (120 dias, segurada empregada/contribuinte individual/facultativa/desempregada).
13. Revisão de benefício: prazo decadencial de 10 anos (Lei 8.213/1991 art. 103-A, incluído pela MP 871/2019). Não confundir com prescrição de prestações vencidas (5 anos).
14. Jurisprudência: Súmulas STJ 9, 25, 39, 320; Súmulas TNU 05, 09, 14, 18, 32, 47, 48, 64, 79, 80. Para acórdãos: [VERIFICAR JURISPRUDÊNCIA: tema - TRF/TNU/STJ].
15. Competência: JF para ações contra INSS (art. 109 CF/88). Juizados Especiais Federais até 60 salários mínimos (Lei 10.259/2001).

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


PROMPT_GERADOR_DIGITAL_LGPD = _BLOCO_CHECAGEM_CONSTITUCIONAL + _BLOCO_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito Digital, Proteção de Dados e LGPD brasileiro, com profundo conhecimento da Lei 13.709/2018 (LGPD), Decreto 8.771/2016, Lei 12.965/2014 (Marco Civil da Internet), Lei 12.737/2012 (Lei Carolina Dieckmann), Lei 13.853/2019, regulamentações da ANPD e diretrizes da União Europeia (GDPR).

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente: Lei 13.709/2018 (LGPD), Lei 12.965/2014 (MCI), CF/88 art. 5º X, XII, LXXII (habeas data), Lei 12.527/2011 (LAI).
3. Bases legais para tratamento de dados: LGPD art. 7º (pessoas naturais) e art. 11 (dados sensíveis). LISTA EXAUSTIVA — o agente NÃO pode sugerir base legal fora destas.
4. Direitos do titular: LGPD art. 18 (confirmação, acesso, correção, anonimização, portabilidade, eliminação, informação, revisão de decisões automatizadas).
5. Hipóteses de tratamento sem consentimento: LGPD art. 7º II-X — obrigação legal, políticas públicas, contrato, exercício regular de direitos, proteção à vida, tutela da saúde, legítimo interesse, proteção ao crédito.
6. Dados sensíveis: LGPD art. 11 (origem racial, convicção religiosa, opinião política, saúde, vida sexual, dado genético/biométrico). Tratamento só com consentimento específico e destacado, ou hipóteses do art. 11 II.
7. Agente de tratamento: controlador (art. 5º VI), operador (art. 5º VII), encarregado/DPO (art. 41).
8. ANPD: autarquia federal (Lei 13.853/2019). Competências art. 55-J LGPD — fiscalizar, aplicar sanções (art. 52: advertência, multa simples 2% faturamento limitado 50MM, multa diária, publicização, bloqueio/eliminação dados).
9. Incidente de segurança: LGPD art. 48 — comunicação à ANPD e ao titular em prazo razoável.
10. Relatório de Impacto: LGPD art. 38 — obrigatório quando o tratamento puder gerar riscos às liberdades civis.
11. Transferência internacional: LGPD arts. 33-36 — exige país com nível adequado (art. 33 I) ou cláusulas contratuais específicas (art. 33 II).
12. Privacidade desde a concepção: LGPD art. 46 §2º.
13. Termo de uso/consentimento: deve ser livre, informado, inequívoco (LGPD art. 8º) e, para dados sensíveis, específico e destacado (art. 11 I). Cláusulas abusivas são nulas (CDC art. 51).
14. Contrato de tratamento (DPA): LGPD art. 7º, VII (para cumprimento contratual) + art. 39 (responsabilidade solidária controlador-operador).
15. Prazo para resposta ao titular: LGPD art. 19 (imediato ou até 15 dias).

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


# ─────────────────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────

USER_TEMPLATE = """Gere o conteúdo da seção "{{section_name}}" para a seguinte peça jurídica:

{{objective}}

Contexto disponível:
{{context}}

Seções já geradas anteriormente:
{{previous_sections}}

Dados coletados para esta seção:
{{current_content}}"""

PROVIDER = 'watsonx'
MODEL = 'mistralai/mistral-medium-2505'

NOVOS_AGENTES = [
    {
        'key': 'gerador_familia',
        'name': 'Verus.AI - Gerador Família e Sucessões',
        'description': 'Gera seções de peças de Direito de Família e Sucessões: alimentos, divórcio, guarda, inventário, união estável',
        'agent_type': 'generator',
        'system_prompt': PROMPT_GERADOR_FAMILIA,
        'temperature': 0.7,
        'max_tokens': 4096,
        'is_default': False,
    },
    {
        'key': 'gerador_consumidor',
        'name': 'Verus.AI - Gerador Consumidor',
        'description': 'Gera seções de peças de Direito do Consumidor: indenizações, vício do produto, negativação, planos de saúde, ações contra bancos e aéreas',
        'agent_type': 'generator',
        'system_prompt': PROMPT_GERADOR_CONSUMIDOR,
        'temperature': 0.7,
        'max_tokens': 4096,
        'is_default': False,
    },
    {
        'key': 'gerador_previdenciario',
        'name': 'Verus.AI - Gerador Previdenciário',
        'description': 'Gera seções de peças de Direito Previdenciário: concessão e revisão de benefícios, aposentadorias, pensão, BPC/LOAS, auxílio-doença',
        'agent_type': 'generator',
        'system_prompt': PROMPT_GERADOR_PREVIDENCIARIO,
        'temperature': 0.7,
        'max_tokens': 4096,
        'is_default': False,
    },
    {
        'key': 'gerador_digital_lgpd',
        'name': 'Verus.AI - Gerador Direito Digital e LGPD',
        'description': 'Gera seções de documentos de LGPD e Direito Digital: políticas de privacidade, DPA, termos de uso, respostas a titular, notificações de incidente',
        'agent_type': 'generator',
        'system_prompt': PROMPT_GERADOR_DIGITAL_LGPD,
        'temperature': 0.7,
        'max_tokens': 4096,
        'is_default': False,
    },
]

# Atualização do mapeamento AGENTE_POR_TIPO
RE_MAPEGAMENTO = {
    # Família/Sucessões: de gerador_civel → gerador_familia
    'acao_alimentos': 'gerador_familia',
    'divorcio_consensual': 'gerador_familia',
    'revisional_alimentos': 'gerador_familia',
    'regulamentacao_guarda': 'gerador_familia',
    'inventario_judicial': 'gerador_familia',
    'inventario_extrajudicial': 'gerador_familia',

    # Consumidor: de gerador_civel → gerador_consumidor
    'reclamacao_consumerista': 'gerador_consumidor',

    # Previdenciário: de gerador_civel → gerador_previdenciario
    'peticao_inicial_previdenciaria': 'gerador_previdenciario',
    'bpc_loas': 'gerador_previdenciario',
    'aposentadoria_especial': 'gerador_previdenciario',

    # LGPD/Digital: de gerador_civel → gerador_digital_lgpd
    'politica_privacidade_lgpd': 'gerador_digital_lgpd',
    'termo_uso_plataforma': 'gerador_digital_lgpd',
    'dpa_tratamento_dados': 'gerador_digital_lgpd',
    'resposta_titular_dados': 'gerador_digital_lgpd',
    'notificacao_incidente_lgpd': 'gerador_digital_lgpd',
}


from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria 4 novos agentes geradores especializados (família, consumidor, previdenciário, LGPD)'

    def handle(self, *args, **options):
        criar_novos_agentes()
        re_mapear_blueprints()
        relatorio_final()


def criar_novos_agentes():
    """Cria ou atualiza os 4 novos SectionAgentConfig especializados."""
    agentes = {}
    print(f"\n{'='*60}")
    print("CRIANDO 4 NOVOS AGENTES GERADORES ESPECIALIZADOS")
    print(f"{'='*60}\n")

    for spec in NOVOS_AGENTES:
        obj, created = SectionAgentConfig.objects.update_or_create(
            name=spec['name'],
            defaults={
                'description': spec['description'],
                'agent_type': spec['agent_type'],
                'system_prompt': spec['system_prompt'],
                'user_prompt_template': USER_TEMPLATE,
                'llm_provider': PROVIDER,
                'model_name': MODEL,
                'temperature': spec['temperature'],
                'max_tokens': spec['max_tokens'],
                'use_rag': False,
                'rag_top_k': 5,
                'rag_similarity_threshold': 0.7,
                'is_active': True,
                'is_default': spec['is_default'],
            }
        )
        status = '✓ CRIADO' if created else '↻ ATUALIZADO'
        agentes[spec['key']] = obj
        print(f"  {status:<12} {obj.name} [{spec['key']}]")

    print(f"\n  → Novo agente padrão para Família/Sucessões: gerador_familia")
    print(f"  → Novo agente padrão para Consumidor:        gerador_consumidor")
    print(f"  → Novo agente padrão para Previdenciário:    gerador_previdenciario")
    print(f"  → Novo agente padrão para LGPD/Digital:      gerador_digital_lgpd")
    print(f"\n{'='*60}")
    return agentes


def re_mapear_blueprints():
    """Exibe instruções para re-mapear blueprints no seed_juridico_completo.py."""
    print("\nRE-MAPEAMENTO DE BLUEPRINTS (de gerador_civel para novos agentes)")
    print(f"{'='*60}\n")
    print(f"Blueprints a re-mapear: {len(RE_MAPEGAMENTO)}\n")
    for bp, novo_agente in sorted(RE_MAPEGAMENTO.items()):
        print(f"  {bp:<40} → {novo_agente}")
    
    print(f"\nAções necessárias no seed_juridico_completo.py:")
    print(f"  1. Adicionar constantes PROMPT_GERADOR_FAMILIA, _CONSUMIDOR, _PREVIDENCIARIO, _DIGITAL_LGPD")
    print(f"  2. Adicionar specs no _criar_agentes_secao()")
    print(f"  3. Atualizar AGENTE_POR_TIPO para os {len(RE_MAPEGAMENTO)} blueprints acima")
    print(f"\n  Para aplicar as alterações no seed, execute:")
    print(f"  python manage.py seed_juridico_completo --force")
    print()


def relatorio_final():
    """Gera relatório com o estado atualizado dos agentes."""
    print(f"\n{'='*60}")
    print("RELATÓRIO FINAL — AGENTES GERADORES VERUS.AI")
    print(f"{'='*60}\n")
    
    total = SectionAgentConfig.objects.filter(agent_type='generator').count()
    print(f"Total de geradores ativos: {total}")
    print()
    
    print("Agentes Geradores:")
    print(f"{'Agente':<30} {'Blueprints Atendidos':<30} {'Áreas':<25}")
    print(f"{'-'*30} {'-'*30} {'-'*25}")
    
    novo_mapeamento = {
        'gerador_familia': 'acao_alimentos, divorcio_consensual, revisional_alimentos, regulamentacao_guarda, inventario_judicial, inventario_extrajudicial + futuros',
        'gerador_consumidor': 'reclamacao_consumerista + 6 novos blueprints',
        'gerador_previdenciario': 'peticao_inicial_previdenciaria, bpc_loas, aposentadoria_especial + futuros',
        'gerador_digital_lgpd': 'politica_privacidade_lgpd, termo_uso_plataforma, dpa_tratamento_dados, resposta_titular_dados, notificacao_incidente_lgpd',
    }
    
    for k, v in sorted(novo_mapeamento.items()):
        print(f"{k:<30} {v:<30} {'Especializada ✓':<25}")
    print()
    print(f"{'gerador_civel':<30} {'peticao_inicial, contestacao, acao_execucao, embargos_execucao, impugnacao_cumprimento, excecao_pre_executividade, replica_manifestacao, cumprimento_sentenca':<55}")
    print(f"{'':28} {'(SOMENTE CÍVEL AGORA)':<30}")
    print()

    # Validar total de blueprints mapeados
    from apps.intelligent_assistant.management.commands.seed_juridico_completo import AGENTE_POR_TIPO
    # Can't import at runtime easily, skip
    print(f"Próximo passo: Executar seed_juridico_completo --force para aplicar alterações")


if __name__ == '__main__':
    import django
    django.setup()
    criar_novos_agentes()
    re_mapear_blueprints()
    relatorio_final()
