"""
Management command para vincular legislacao importada (kb.Document) aos agentes corretos.

Para SectionAgentConfig: cria KnowledgeBase wrappers (camada 'global') e vincula via M2M.
Para AgentPrompt: vincula kb.Document diretamente via M2M.

IMPORTANTE: Alem de criar KnowledgeBase wrappers, copia os embeddings
de kb.DocumentChunk para KnowledgeBaseEmbedding para que os documentos
aparecam na pagina /dashboard/knowledge-base com chunks populados.
"""
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.kb.models import Document, DocumentChunk
from apps.intelligent_assistant.models.agent import SectionAgentConfig
from apps.intelligent_assistant.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseEmbedding,
)
from apps.agents.models import AgentPrompt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento: keyword de area -> substrings de titulo de legislacao
# ---------------------------------------------------------------------------
AGENT_LEGISLATION_MAP = {
    # Geradores (SectionAgentConfig) — match por substring no nome do agente
    'civel': [
        'Codigo Civil', 'Codigo de Processo Civil', 'Constituicao Federal',
        'LINDB', 'Mediacao', 'Arbitragem',
    ],
    'recursal': [
        'Codigo de Processo Civil', 'Constituicao Federal',
        'Juizados Especiais', 'Juizados Especiais Federais', 'Juizados da Fazenda',
    ],
    'constitucional': [
        'Constituicao Federal', 'Mandado de Seguranca', 'ADPF', 'ADI/ADC',
        'Mandado de Injuncao', 'Habeas Data', 'Acao Popular',
    ],
    'trabalhista': [
        'Codigo de Processo Civil', 'CLT', 'Constituicao Federal',
        'FGTS', 'Beneficios da Previdencia', 'Seguridade Social',
    ],
    'criminal': [
        'Codigo Penal', 'Codigo de Processo Penal', 'Constituicao Federal',
        'Maria da Penha', 'Execucoes Penais', 'Crimes Hediondos',
        'Drogas', 'Abuso de Autoridade', 'Lavagem de Dinheiro',
        'Organizacoes Criminosas', 'Tortura', 'Crimes Ciberneticos',
    ],
    'extrajudicial': [
        'Codigo Civil', 'Constituicao Federal', 'Registros Publicos',
        'Mediacao', 'Arbitragem',
    ],
    'familia': [
        'Codigo Civil', 'Estatuto da Crianca', 'Constituicao Federal',
        'Alienacao Parental', 'Guarda Compartilhada',
    ],
    'consumidor': [
        'Defesa do Consumidor', 'Codigo Civil', 'Constituicao Federal',
        'Superendividamento',
    ],
    'previdenciario': [
        'Constituicao Federal', 'Beneficios da Previdencia',
        'Seguridade Social', 'Juizados Especiais Federais',
    ],
    'digital': [
        'LGPD', 'Marco Civil', 'Constituicao Federal',
        'Crimes Ciberneticos', 'Direitos Autorais', 'Propriedade Industrial',
    ],
    'ambiental': [
        'Constituicao Federal', 'Acao Civil Publica', 'Crimes Ambientais',
        'Codigo Florestal', 'Politica Nacional do Meio Ambiente', 'Recursos Hidricos',
    ],
    'eleitoral': [
        'Constituicao Federal', 'Codigo Eleitoral', 'Eleicoes',
        'Inelegibilidades', 'Partidos Politicos',
    ],
    'militar': [
        'Codigo Penal Militar', 'Processo Penal Militar', 'Constituicao Federal',
        'Estatuto dos Militares',
    ],
    'internacional': [
        'Codigo de Processo Civil', 'Constituicao Federal', 'LINDB',
    ],
    'empresarial': [
        'Codigo Civil', 'Falencia', 'Constituicao Federal',
        'Sociedades por Acoes', 'Arbitragem', 'Registro de Empresas',
        'Anticorrupcao Empresarial',
    ],
    'tributario': [
        'Codigo Tributario', 'Constituicao Federal', 'Execucao Fiscal',
        'Responsabilidade Fiscal',
    ],
    'especializado': [
        'Constituicao Federal', 'Codigo de Processo Civil',
        'Juizados Especiais', 'Improbidade', 'Licitacoes',
        'Juizados Especiais Federais', 'Juizados da Fazenda',
    ],
    'administrativo': [
        'Constituicao Federal', 'Improbidade', 'Licitacoes',
        'Mandado de Seguranca', 'Processo Administrativo Federal',
        'Acesso a Informacao', 'Servidores Publicos Federais',
        'Responsabilidade Fiscal', 'Concessoes',
    ],
    'imobiliario': [
        'Codigo Civil', 'Codigo de Processo Civil', 'Constituicao Federal',
        'Inquilinato', 'Registros Publicos', 'Condominio', 'Estatuto da Cidade',
    ],
    'saude': [
        'Constituicao Federal', 'Defesa do Consumidor', 'Organica da Saude',
    ],
    'sucessoes': ['Codigo Civil', 'Codigo de Processo Civil', 'Constituicao Federal'],
    'idoso': [
        'Estatuto do Idoso', 'Constituicao Federal',
        'Pessoa com Deficiencia',
    ],
    'lgpd': ['LGPD', 'Marco Civil', 'Constituicao Federal', 'Crimes Ciberneticos'],
    'desportivo': ['Constituicao Federal', 'Lei Geral do Esporte'],
    'agrario': ['Constituicao Federal', 'Estatuto da Terra'],
    'profissional': ['Constituicao Federal', 'Advocacia e OAB'],
}

# Mapeamento extra: agent_type do AgentPrompt -> area no mapa acima
AGENT_TYPE_AREA_MAP = {
    'advogado_civil': 'civel',
    'advogado_criminal': 'criminal',
    'advogado_trabalhista': 'trabalhista',
    'advogado_tributario': 'tributario',
    'advogado_administrativo': 'administrativo',
    'advogado_previdenciario': 'previdenciario',
    'advogado_consumidor': 'consumidor',
    'advogado_familia': 'familia',
    'advogado_empresarial': 'empresarial',
    'advogado_ambiental': 'ambiental',
    'advogado_digital_lgpd': 'digital',
    'advogado_constitucional': 'constitucional',
    'advogado_imobiliario': 'imobiliario',
    'advogado_saude': 'saude',
    'advogado_eleitoral': 'eleitoral',
    'advogado_militar': 'militar',
    'advogado_internacional': 'internacional',
    'advogado_desportivo': 'desportivo',
    'advogado_agrario': 'agrario',
    'advogado_profissional': 'profissional',
    'analista_juridico': 'civel',  # analista geral recebe base civil
}


def _detect_area(name: str) -> str | None:
    """Detecta a area juridica a partir do nome do agente (case-insensitive)."""
    lower = name.lower()
    for area in AGENT_LEGISLATION_MAP:
        if area in lower:
            return area
    return None


def _find_documents(keywords: list[str], all_docs: list) -> list:
    """Filtra documentos cujo titulo contem alguma das keywords."""
    matched = []
    for doc in all_docs:
        title_lower = doc.title.lower()
        for kw in keywords:
            if kw.lower() in title_lower:
                matched.append(doc)
                break
    return matched


def _sync_embeddings_to_kb(kb: KnowledgeBase, doc: Document, stdout=None) -> int:
    """
    Copia embeddings de kb.DocumentChunk para KnowledgeBaseEmbedding.

    Isso garante que a KnowledgeBase wrapper apareca na UI com chunks
    populados e seja utilizavel para busca vetorial.

    Chunks SEM embedding (gerados com --no-embeddings) sao copiados com um
    vetor zero para que a contagem de fontes/chunks apareca corretamente na
    UI. A busca vetorial ignora esses chunks pela similaridade nula.

    Retorna o numero de embeddings criados (0 se ja existiam).
    """
    # Verificar se ja possui embeddings para este source_name
    existing = KnowledgeBaseEmbedding.objects.filter(
        knowledge_base=kb,
        source_name=doc.title,
    ).exists()
    if existing:
        return 0

    # Buscar chunks do Document original
    chunks = DocumentChunk.objects.filter(document=doc).order_by('chunk_index')
    if not chunks.exists():
        if stdout:
            stdout.write(f'    [sync] {doc.title}: 0 chunks no kb.DocumentChunk (pulando)')
        return 0

    # Vetor zero para chunks sem embedding (placeholder ate embeddings serem gerados)
    ZERO_VECTOR = [0.0] * 1024

    # Criar KnowledgeBaseEmbeddings em batch
    embeddings_to_create = []
    for chunk in chunks:
        embeddings_to_create.append(
            KnowledgeBaseEmbedding(
                knowledge_base=kb,
                source_name=doc.title,
                source_type='url',
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.content,
                chunk_size=len(chunk.content),
                embedding=chunk.embedding if chunk.embedding is not None else ZERO_VECTOR,
                embedding_model='intfloat/multilingual-e5-large',
                metadata={
                    'origin': 'seed_legislacao',
                    'kb_document_id': str(doc.id),
                    'has_real_embedding': chunk.embedding is not None,
                    **(chunk.metadata or {}),
                },
            )
        )

    if embeddings_to_create:
        KnowledgeBaseEmbedding.objects.bulk_create(
            embeddings_to_create, ignore_conflicts=True
        )

    return len(embeddings_to_create)


class Command(BaseCommand):
    help = 'Vincula legislacao importada (kb.Document category=lei) aos agentes (SectionAgentConfig e AgentPrompt)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Revincula mesmo se o agente ja possuir knowledge_bases',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria vinculado sem efetuar alteracoes',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        # 1. Buscar todos os Documents de legislacao
        lei_docs = list(Document.objects.filter(category='lei', is_active=True))
        if not lei_docs:
            self.stdout.write(self.style.WARNING(
                '  Nenhum Document com category=lei encontrado. '
                'Execute seed_legislacao primeiro.'
            ))
            return

        self.stdout.write(f'  {len(lei_docs)} legislacoes encontradas na KB.\n')

        # 1.5 Garantir que TODA legislacao tenha KnowledgeBase wrapper + embeddings
        # Isso e necessario para que as legislacoes aparecam na pagina /dashboard/knowledge-base
        self._ensure_all_kb_wrappers(lei_docs, dry_run)

        # 2. Vincular SectionAgentConfigs
        self._link_section_agents(lei_docs, force, dry_run)

        # 3. Vincular AgentPrompts
        self._link_agent_prompts(lei_docs, force, dry_run)

    # ------------------------------------------------------------------
    # Garantir wrappers + embeddings para TODA legislacao
    # ------------------------------------------------------------------
    def _ensure_all_kb_wrappers(self, lei_docs, dry_run):
        """
        Cria KnowledgeBase wrappers + sincroniza embeddings para TODOS os
        Documents de legislacao, garantindo que aparecam na UI da KB.
        """
        self.stdout.write('  --- Criando KnowledgeBase wrappers para todas as legislacoes ---')
        created = 0
        synced = 0

        for doc in lei_docs:
            kb_name = f'Legislacao: {doc.title}'

            if dry_run:
                exists = KnowledgeBase.objects.filter(name=kb_name).exists()
                if not exists:
                    self.stdout.write(f'  [dry-run] Criaria KB: {kb_name}')
                continue

            kb, was_created = KnowledgeBase.objects.get_or_create(
                name=kb_name,
                defaults={
                    'description': f'Base de conhecimento da legislacao: {doc.title}',
                    'kb_layer': 'global',
                    'is_active': True,
                },
            )
            if was_created:
                created += 1

            emb_count = _sync_embeddings_to_kb(kb, doc, stdout=self.stdout)
            if emb_count:
                synced += 1

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'  KBs: {created} criadas, {synced} com embeddings sincronizados '
                f'(de {len(lei_docs)} legislacoes).\n'
            ))
        else:
            self.stdout.write('  [dry-run] Nenhuma alteracao realizada.\n')

    # ------------------------------------------------------------------
    # SectionAgentConfig  (M2M -> KnowledgeBase)
    # ------------------------------------------------------------------
    def _link_section_agents(self, lei_docs, force, dry_run):
        agents = SectionAgentConfig.objects.filter(is_active=True)
        linked = 0
        skipped = 0

        self.stdout.write('  --- SectionAgentConfig ---')

        for agent in agents:
            # Pular se ja tem KBs e nao e --force
            if not force and agent.knowledge_bases.exists():
                skipped += 1
                continue

            area = _detect_area(agent.name)
            if not area:
                continue

            keywords = AGENT_LEGISLATION_MAP.get(area, [])
            if not keywords:
                continue

            docs = _find_documents(keywords, lei_docs)
            if not docs:
                continue

            if dry_run:
                doc_names = ', '.join(d.title for d in docs)
                self.stdout.write(
                    f'  [dry-run] {agent.name} <- {len(docs)} docs: {doc_names}'
                )
                linked += 1
                continue

            # Para cada doc, garantir que existe um KnowledgeBase wrapper
            # E sincronizar embeddings de kb.DocumentChunk -> KnowledgeBaseEmbedding
            kbs = []
            for doc in docs:
                kb_name = f'Legislacao: {doc.title}'
                kb, _ = KnowledgeBase.objects.get_or_create(
                    name=kb_name,
                    defaults={
                        'description': f'Base de conhecimento da legislacao: {doc.title}',
                        'kb_layer': 'global',
                        'is_active': True,
                    },
                )
                # Copiar embeddings do DocumentChunk -> KnowledgeBaseEmbedding
                synced = _sync_embeddings_to_kb(kb, doc, stdout=self.stdout)
                if synced:
                    self.stdout.write(
                        f'    [sync] {doc.title}: {synced} embeddings copiados para KB'
                    )
                kbs.append(kb)

            if force:
                # Remover apenas KBs de legislacao antes de revincular
                existing_leg_kbs = agent.knowledge_bases.filter(
                    name__startswith='Legislacao: '
                )
                agent.knowledge_bases.remove(*existing_leg_kbs)

            agent.knowledge_bases.add(*kbs)

            if not agent.use_rag:
                agent.use_rag = True
                agent.save(update_fields=['use_rag'])

            linked += 1
            self.stdout.write(self.style.SUCCESS(
                f'  {agent.name} <- {len(kbs)} KBs vinculadas'
            ))

        self.stdout.write(
            f'  SectionAgentConfig: {linked} vinculados, {skipped} ja possuiam KBs.\n'
        )

    # ------------------------------------------------------------------
    # AgentPrompt  (M2M -> kb.Document direto)
    # ------------------------------------------------------------------
    def _link_agent_prompts(self, lei_docs, force, dry_run):
        agents = AgentPrompt.objects.filter(is_active=True)
        linked = 0
        skipped = 0

        self.stdout.write('  --- AgentPrompt ---')

        for agent in agents:
            if not force and agent.knowledge_bases.exists():
                skipped += 1
                continue

            # Determinar area pelo agent_type ou pelo nome
            area = AGENT_TYPE_AREA_MAP.get(agent.agent_type)
            if not area:
                area = _detect_area(agent.name)
            if not area:
                continue

            keywords = AGENT_LEGISLATION_MAP.get(area, [])
            if not keywords:
                continue

            docs = _find_documents(keywords, lei_docs)
            if not docs:
                continue

            if dry_run:
                doc_names = ', '.join(d.title for d in docs)
                self.stdout.write(
                    f'  [dry-run] {agent.name} <- {len(docs)} docs: {doc_names}'
                )
                linked += 1
                continue

            if force:
                # Remover apenas docs de legislacao antes de revincular
                existing_leg_docs = agent.knowledge_bases.filter(category='lei')
                agent.knowledge_bases.remove(*existing_leg_docs)

            agent.knowledge_bases.add(*docs)

            if not agent.use_rag:
                agent.use_rag = True
                agent.save(update_fields=['use_rag'])

            linked += 1
            self.stdout.write(self.style.SUCCESS(
                f'  {agent.name} <- {len(docs)} Documents vinculados'
            ))

        self.stdout.write(
            f'  AgentPrompt: {linked} vinculados, {skipped} ja possuiam KBs.\n'
        )
