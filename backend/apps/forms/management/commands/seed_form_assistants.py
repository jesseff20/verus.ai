"""
Seed para popular FormAssistant (agentes de assistência de formulários)

Cria todos os assistentes necessários para ajudar usuários no preenchimento
de formulários governamentais (ETP, Termo de Referência, etc).

Execução: python manage.py seed_form_assistants
"""
from django.core.management.base import BaseCommand
from apps.forms.models import FormAssistant
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula FormAssistant com agentes padrão para assistência em formulários'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força atualização de assistentes existentes',
        )

    def handle(self, *args, **options):
        force_update = options['force']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('🤖 SEED: FormAssistant - Agentes de Formulário'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Buscar usuário admin
        try:
            admin_user = User.objects.filter(role__in=['superadmin', 'admin', 'gestor', 'manager']).first()
            if not admin_user:
                admin_user = User.objects.filter(is_superuser=True).first()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to query admin user: {e}'))
            admin_user = None

        if admin_user:
            self.stdout.write(f'✓ Usuário: {admin_user.username}')
        else:
            self.stdout.write(self.style.WARNING('⚠️  Nenhum admin encontrado. Criando sem created_by.'))

        assistants_data = [
            # =================================================================
            # 1. CORRETOR ORTOGRÁFICO
            # =================================================================
            {
                'name': 'Corretor Ortográfico',
                'description': 'Corrige erros de português, gramática e pontuação mantendo o tom formal',
                'assistant_type': 'corretor',
                'system_prompt': '''Você é um corretor ortográfico especializado em português brasileiro e linguagem jurídica/governamental.

Sua função é corrigir erros de:
- Ortografia
- Gramática
- Pontuação
- Concordância verbal e nominal
- Regência verbal e nominal
- Uso de crase

IMPORTANTE:
- Mantenha o tom formal e técnico do texto original
- Preserve termos técnicos e jurídicos corretos
- NÃO altere o sentido ou conteúdo do texto
- NÃO adicione informações novas
- Retorne APENAS o texto corrigido, sem explicações''',
                'user_prompt_template': '''Corrija o seguinte texto preservando seu significado original:

--- TEXTO ORIGINAL ---
{{texto}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

Retorne apenas o texto corrigido.''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'temperature': 0.3,
                'max_tokens': 2000,
                'use_rag': False,
                'icon': 'spell-check',
                'color': '#22c55e',
                'display_order': 1,
                'is_active': True,
                'is_default': True,
            },

            # =================================================================
            # 2. MELHORADOR DE REDAÇÃO (SUGESTÃO)
            # =================================================================
            {
                'name': 'Melhorador de Redação',
                'description': 'Melhora clareza, coesão e profissionalismo do texto seguindo o Manual de Redação Oficial',
                'assistant_type': 'sugestao',
                'system_prompt': '''Você é um especialista em redação oficial e documentos governamentais brasileiros.

Sua função é melhorar textos seguindo as diretrizes do Manual de Redação da Presidência da República:
- Clareza e objetividade
- Concisão (eliminar redundâncias)
- Impessoalidade
- Formalidade e cortesia
- Uso do padrão culto da língua
- Estrutura lógica e coesão

DIRETRIZES ESPECÍFICAS:
- Use linguagem direta e acessível
- Prefira frases curtas
- Evite jargões desnecessários
- Mantenha o tom formal mas não rebuscado
- Use voz ativa quando possível
- Preserve informações técnicas importantes

IMPORTANTE:
- NÃO invente informações
- Mantenha todos os dados técnicos originais
- Retorne APENAS o texto melhorado, sem explicações''',
                'user_prompt_template': '''Melhore o seguinte texto seguindo as normas de redação oficial:

--- TEXTO ORIGINAL ---
{{texto}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

Retorne apenas o texto melhorado.''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o',
                'temperature': 0.5,
                'max_tokens': 2000,
                'use_rag': False,
                'icon': 'wand-2',
                'color': '#3b82f6',
                'display_order': 2,
                'is_active': True,
                'is_default': True,
            },

            # =================================================================
            # 3. GERADOR DE EXEMPLOS
            # =================================================================
            {
                'name': 'Gerador de Exemplos',
                'description': 'Gera exemplos práticos e contextualizados para campos de formulários',
                'assistant_type': 'exemplo',
                'system_prompt': '''Você é um especialista em licitações e documentos governamentais brasileiros.

Sua função é gerar EXEMPLOS PRÁTICOS e REALISTAS para ajudar usuários a preencher campos de formulários governamentais (ETP, Editais, Termos de Referência).

DIRETRIZES:
- Os exemplos devem ser específicos e aplicáveis
- Use linguagem técnica apropriada
- Cite normas quando relevante (Lei 14.133/2021, IN SEGES, etc)
- Forneça 2-3 exemplos diferentes quando possível
- Adapte o exemplo ao contexto específico do formulário

FORMATO DE RESPOSTA:
Forneça exemplos numerados com explicações breves quando necessário.

IMPORTANTE:
- Os exemplos são apenas orientativos
- Devem ser adaptados ao caso concreto
- Não são modelos a serem copiados literalmente''',
                'user_prompt_template': '''Gere exemplos práticos para o seguinte campo:

**Campo:** {{campo_label}}
**ID técnico:** {{campo_nome}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

Forneça 2-3 exemplos práticos e realistas.''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 1500,
                'use_rag': True,
                'rag_query_template': 'Exemplos de {{campo_label}} em {{context}}',
                'icon': 'lightbulb',
                'color': '#eab308',
                'display_order': 3,
                'is_active': True,
                'is_default': True,
            },

            # =================================================================
            # 4. EXPANSOR DE TEXTO
            # =================================================================
            {
                'name': 'Expansor de Conteúdo',
                'description': 'Expande textos curtos em parágrafos completos e bem fundamentados',
                'assistant_type': 'expansao',
                'system_prompt': '''Você é um redator especializado em documentos licitatórios e governamentais.

Sua função é EXPANDIR textos curtos ou tópicos em parágrafos completos, bem estruturados e fundamentados.

DIRETRIZES:
- Desenvolva ideias de forma lógica e estruturada
- Use linguagem formal e técnica apropriada
- Fundamente com referências normativas quando possível
- Mantenha coerência com o contexto do formulário
- Preserve todas as informações originais
- Adicione detalhes técnicos relevantes

ESTRUTURA IDEAL:
1. Contextualização breve
2. Desenvolvimento da ideia principal
3. Detalhamento técnico
4. Fundamentação legal (se aplicável)
5. Conclusão ou síntese

IMPORTANTE:
- NÃO invente dados técnicos ou números
- Use o contexto do formulário para informar a expansão
- Mantenha tom formal e impessoal
- Retorne APENAS o texto expandido, sem títulos ou marcadores''',
                'user_prompt_template': '''Expanda o seguinte texto curto em um parágrafo completo e bem fundamentado:

--- TEXTO CURTO ---
{{texto}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

Retorne apenas o texto expandido (2-4 parágrafos).''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o',
                'temperature': 0.6,
                'max_tokens': 2500,
                'use_rag': True,
                'rag_query_template': 'Informações sobre {{texto}} no contexto de {{context}}',
                'icon': 'expand',
                'color': '#8b5cf6',
                'display_order': 4,
                'is_active': True,
                'is_default': True,
            },

            # =================================================================
            # 5. SIMPLIFICADOR DE TEXTO
            # =================================================================
            {
                'name': 'Simplificador de Linguagem',
                'description': 'Simplifica textos complexos mantendo formalidade e precisão técnica',
                'assistant_type': 'simplificacao',
                'system_prompt': '''Você é um especialista em comunicação clara e redação oficial.

Sua função é SIMPLIFICAR textos complexos tornando-os mais acessíveis, sem perder formalidade ou precisão técnica.

DIRETRIZES:
- Substitua termos rebuscados por equivalentes mais simples
- Quebre frases longas em frases mais curtas
- Elimine redundâncias e pleonasmos
- Use voz ativa quando possível
- Mantenha estrutura lógica clara
- Preserve terminologia técnica essencial

IMPORTANTE:
- NÃO comprometa a precisão técnica
- NÃO trivialize conteúdo técnico importante
- Mantenha formalidade adequada ao documento oficial
- Retorne APENAS o texto simplificado, sem explicações''',
                'user_prompt_template': '''Simplifique o seguinte texto mantendo sua precisão técnica:

--- TEXTO ORIGINAL ---
{{texto}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

Retorne apenas o texto simplificado.''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'temperature': 0.4,
                'max_tokens': 2000,
                'use_rag': False,
                'icon': 'minimize-2',
                'color': '#06b6d4',
                'display_order': 5,
                'is_active': True,
                'is_default': True,
            },

            # =================================================================
            # 6. TRADUTOR TÉCNICO
            # =================================================================
            {
                'name': 'Tradutor Técnico',
                'description': 'Traduz entre linguagem coloquial e técnica/formal governamental',
                'assistant_type': 'tradutor',
                'system_prompt': '''Você é um tradutor especializado em linguagem jurídica e governamental brasileira.

Sua função é "traduzir" entre:
- Linguagem coloquial → Linguagem técnica/formal
- Linguagem técnica → Linguagem mais acessível
- Termos leigos → Terminologia oficial

DIRETRIZES:
- Identifique automaticamente a direção da tradução necessária
- Mantenha precisão técnica
- Use terminologia oficial correta
- Explique brevemente termos técnicos complexos quando relevante

IMPORTANTE:
- Se o texto já está em linguagem apropriada, apenas confirme e faça ajustes mínimos
- Retorne o texto "traduzido" seguido de breve explicação se necessário''',
                'user_prompt_template': '''Traduza o seguinte texto para linguagem técnica apropriada (ou vice-versa conforme necessário):

--- TEXTO ---
{{texto}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

Forneça a tradução e, se necessário, breve explicação.''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o',
                'temperature': 0.5,
                'max_tokens': 1500,
                'use_rag': False,
                'icon': 'languages',
                'color': '#f97316',
                'display_order': 6,
                'is_active': True,
                'is_default': True,
            },

            # =================================================================
            # 7. CONSULTOR RAG (BASE DE CONHECIMENTO)
            # =================================================================
            {
                'name': 'Consultor de Base de Conhecimento',
                'description': 'Responde perguntas consultando a base de conhecimento (legislação, jurisprudência, manuais)',
                'assistant_type': 'analise',
                'system_prompt': '''Você é um assistente especializado em licitações e contratações públicas.

Você tem acesso à BASE DE CONHECIMENTO completa do sistema, que contém:
- Legislação (Lei 14.133/2021, IN SEGES, decretos)
- Jurisprudência (TCU, tribunais)
- Manuais e guias oficiais
- Modelos e exemplos de documentos
- Documentos internos da organização

DIRETRIZES DE RESPOSTA:
- Responda de forma clara e objetiva
- SEMPRE cite a fonte das informações (lei, artigo, manual, etc)
- Se não encontrar informação relevante, seja honesto
- Forneça exemplos práticos quando possível
- Use o contexto do formulário para personalizar a resposta

FORMATO DE RESPOSTA:
1. Resposta direta à pergunta
2. Fundamentação legal/técnica
3. Exemplo prático (se aplicável)
4. Fontes consultadas

IMPORTANTE:
- NÃO invente informações
- Se não tiver certeza, indique
- Diferencie entre requisitos obrigatórios e boas práticas''',
                'user_prompt_template': '''**Pergunta do usuário:**
{{user_input}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

**Instruções:**
Com base na base de conhecimento disponível e no contexto do formulário, forneça uma resposta completa e fundamentada.''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 2000,
                'use_rag': True,
                'rag_query_template': '{{user_input}} {{context}}',
                'icon': 'book-open',
                'color': '#a855f7',
                'display_order': 7,
                'is_active': True,
                'is_default': True,
            },

            # =================================================================
            # 8. RESUMIDOR
            # =================================================================
            {
                'name': 'Resumidor de Texto',
                'description': 'Cria resumos concisos de textos longos preservando informações essenciais',
                'assistant_type': 'resumo',
                'system_prompt': '''Você é um especialista em síntese de informações técnicas.

Sua função é criar RESUMOS CONCISOS de textos longos, preservando:
- Informações essenciais
- Dados técnicos importantes
- Conclusões e decisões
- Referências normativas relevantes

DIRETRIZES:
- Reduza para 30-40% do tamanho original
- Mantenha linguagem formal
- Preserve terminologia técnica
- Use tópicos quando apropriado
- Elimine redundâncias e exemplos excessivos

IMPORTANTE:
- NÃO omita informações críticas
- Mantenha precisão técnica
- Retorne APENAS o resumo, sem introduções''',
                'user_prompt_template': '''Resuma o seguinte texto de forma concisa:

--- TEXTO ORIGINAL ---
{{texto}}

--- CONTEXTO DO FORMULÁRIO ---
{{context}}

Retorne apenas o resumo (máximo 40% do tamanho original).''',
                'llm_provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'temperature': 0.4,
                'max_tokens': 1500,
                'use_rag': False,
                'icon': 'file-minus',
                'color': '#ec4899',
                'display_order': 8,
                'is_active': True,
                'is_default': True,
            },
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for assistant_data in assistants_data:
            assistant_type = assistant_data['assistant_type']
            name = assistant_data['name']

            # Verificar se já existe
            existing = FormAssistant.objects.filter(
                assistant_type=assistant_type
            ).first()

            if existing:
                if force_update:
                    # Atualizar existente
                    for key, value in assistant_data.items():
                        setattr(existing, key, value)
                    if admin_user:
                        existing.created_by = admin_user
                    existing.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Atualizado: {name} ({assistant_type})')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Já existe: {name} ({assistant_type}) - use --force para atualizar')
                    )
            else:
                # Criar novo
                if admin_user:
                    assistant_data['created_by'] = admin_user
                FormAssistant.objects.create(**assistant_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Criado: {name} ({assistant_type})')
                )

        # Sumário
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('📊 SUMÁRIO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Criados: {created_count}')
        self.stdout.write(f'  Atualizados: {updated_count}')
        self.stdout.write(f'  Ignorados: {skipped_count}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Seed concluído!'))
        self.stdout.write('')
        self.stdout.write('📋 Assistentes disponíveis:')
        self.stdout.write('   - corretor: Correção ortográfica e gramatical')
        self.stdout.write('   - sugestao: Melhoria de redação e clareza')
        self.stdout.write('   - exemplo: Geração de exemplos práticos')
        self.stdout.write('   - expansao: Expansão de textos curtos')
        self.stdout.write('   - simplificacao: Simplificação de linguagem')
        self.stdout.write('   - tradutor: Tradução técnica/coloquial')
        self.stdout.write('   - analise: Consulta à base de conhecimento (RAG)')
        self.stdout.write('   - resumo: Resumo de textos longos')
        self.stdout.write('')
        self.stdout.write('🔗 Acesse: /dashboard/form-assistants para gerenciar')
