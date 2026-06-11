"""
Migration: Fase 1 — Pipeline configurável de KBs e agentes.

Novos modelos:
- AgentKnowledgeBaseLink (vínculo configurável agente ↔ KB)
- SectionPipelineStep (pipeline multi-step por seção)

Alterações em modelos existentes:
- KnowledgeBase: novo kb_layer 'section_example', novo FK 'section'
- KnowledgeBaseEmbedding: novo campo 'summary'
- SectionAgentConfig: novos agent_type 'analyzer' e 'refiner'
"""
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("intelligent_assistant", "0021_alter_uploadeddocument_file_type"),
    ]

    operations = [
        # 1. Alterar KnowledgeBase.kb_layer para incluir 'section_example'
        migrations.AlterField(
            model_name="knowledgebase",
            name="kb_layer",
            field=models.CharField(
                choices=[
                    ("global", "Global (Normas Gerais)"),
                    ("blueprint", "Blueprint (Base do Documento)"),
                    ("agent", "Agente (Melhores Resultados)"),
                    ("section_example", "Exemplo Real de Seção"),
                ],
                default="global",
                help_text="Camada na hierarquia: global (todos acessam), blueprint (por tipo de documento), agent (melhores resultados), section_example (exemplos reais por seção)",
                max_length=20,
                verbose_name="Camada",
            ),
        ),
        # 2. Adicionar FK section na KnowledgeBase
        migrations.AddField(
            model_name="knowledgebase",
            name="section",
            field=models.ForeignKey(
                blank=True,
                help_text="Seção específica (apenas para camada section_example)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="example_kbs",
                to="intelligent_assistant.blueprintsection",
                verbose_name="Seção Associada",
            ),
        ),
        # 3. Adicionar summary no KnowledgeBaseEmbedding
        migrations.AddField(
            model_name="knowledgebaseembedding",
            name="summary",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Summary do chunk gerado por IA (estrutura, padrão de escrita, etc.)",
                verbose_name="Resumo Interpretativo",
            ),
            preserve_default=False,
        ),
        # 4. Alterar SectionAgentConfig.agent_type para incluir 'analyzer' e 'refiner'
        migrations.AlterField(
            model_name="sectionagentconfig",
            name="agent_type",
            field=models.CharField(
                choices=[
                    ("generator", "Gerador de Conteúdo"),
                    ("validator", "Validador de Conteúdo"),
                    ("analyzer", "Analisador de Exemplos"),
                    ("refiner", "Refinador com Feedback"),
                ],
                default="generator",
                max_length=20,
                verbose_name="Tipo de Agente",
            ),
        ),
        # 5. Criar modelo AgentKnowledgeBaseLink
        migrations.CreateModel(
            name="AgentKnowledgeBaseLink",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        default=0,
                        help_text="Ordem de consulta (0 = primeiro). Menor = maior prioridade.",
                        verbose_name="Prioridade",
                    ),
                ),
                (
                    "purpose",
                    models.CharField(
                        choices=[
                            ("examples", "Exemplos Reais da Seção"),
                            ("evaluation", "Padrões Avaliados (4+ estrelas)"),
                            ("normative", "Normas e Legislação"),
                            ("context", "Contexto do Usuário (sessão)"),
                            ("reference", "Referência Geral"),
                        ],
                        default="reference",
                        help_text="Como o agente deve interpretar os resultados desta KB",
                        max_length=20,
                        verbose_name="Propósito",
                    ),
                ),
                (
                    "instruction",
                    models.TextField(
                        blank=True,
                        help_text='Instrução para o agente sobre como usar os resultados desta KB. Ex: "Extraia o padrão de escrita destes exemplos reais"',
                        verbose_name="Instrução de Uso",
                    ),
                ),
                (
                    "top_k",
                    models.IntegerField(
                        default=5,
                        help_text="Número de chunks a recuperar desta KB",
                        verbose_name="Top K",
                    ),
                ),
                (
                    "min_similarity",
                    models.FloatField(
                        default=0.6,
                        help_text="Threshold de similaridade para incluir resultados (0.0 a 1.0)",
                        verbose_name="Similaridade Mínima",
                    ),
                ),
                (
                    "include_summary",
                    models.BooleanField(
                        default=False,
                        help_text="Se True, inclui o summary interpretativo junto com o chunk",
                        verbose_name="Incluir Resumo",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Ativo"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "agent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="kb_links",
                        to="intelligent_assistant.sectionagentconfig",
                        verbose_name="Agente",
                    ),
                ),
                (
                    "knowledge_base",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_links",
                        to="intelligent_assistant.knowledgebase",
                        verbose_name="Base de Conhecimento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vínculo Agente ↔ KB",
                "verbose_name_plural": "Vínculos Agente ↔ KB",
                "ordering": ["agent", "priority"],
                "indexes": [
                    models.Index(
                        fields=["agent", "priority"],
                        name="ia_agentkblink_agent_priority_idx",
                    ),
                    models.Index(
                        fields=["is_active"],
                        name="ia_agentkblink_is_active_idx",
                    ),
                ],
                "unique_together": {("agent", "knowledge_base")},
            },
        ),
        # 6. Criar modelo SectionPipelineStep
        migrations.CreateModel(
            name="SectionPipelineStep",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "step_order",
                    models.IntegerField(
                        help_text="Ordem de execução (1, 2, 3...). Menor = primeiro.",
                        verbose_name="Ordem do Passo",
                    ),
                ),
                (
                    "step_type",
                    models.CharField(
                        choices=[
                            ("analyze", "Analisar Exemplos"),
                            ("generate", "Gerar Conteúdo"),
                            ("validate", "Validar Conteúdo"),
                            ("refine", "Refinar com Feedback"),
                        ],
                        help_text="Tipo de operação que este passo executa",
                        max_length=20,
                        verbose_name="Tipo do Passo",
                    ),
                ),
                (
                    "output_variable",
                    models.CharField(
                        default="output",
                        help_text="Nome da variável que recebe o output deste step (acessível pelo próximo step via {{variavel}})",
                        max_length=50,
                        verbose_name="Variável de Saída",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Ativo"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pipeline_steps",
                        to="intelligent_assistant.blueprintsection",
                        verbose_name="Seção",
                    ),
                ),
                (
                    "agent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pipeline_steps",
                        to="intelligent_assistant.sectionagentconfig",
                        verbose_name="Agente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Passo do Pipeline",
                "verbose_name_plural": "Passos do Pipeline",
                "ordering": ["section", "step_order"],
                "indexes": [
                    models.Index(
                        fields=["section", "step_order"],
                        name="ia_pipelinestep_section_order_idx",
                    ),
                ],
                "unique_together": {("section", "step_order")},
            },
        ),
    ]
