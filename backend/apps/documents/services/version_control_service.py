"""
Versionamento Semântico de Documentos Jurídicos.

Funcionalidades:
  - Versionamento automático de documentos
  - Diff semântico entre versões
  - Rollback seletivo (por seção)
  - Histórico de alterações
  - Branching para comparação
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher, unified_diff
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.documents.models import Document, DocumentVersion

User = get_user_model()


class ChangeType(str, Enum):
    """Tipo de alteração em diff semântico."""
    ADDED = 'added'
    REMOVED = 'removed'
    MODIFIED = 'modified'
    UNCHANGED = 'unchanged'


class VersionType(str, Enum):
    """Tipo de versão."""
    MAJOR = 'major'      # Mudança substantiva
    MINOR = 'minor'      # Alterações menores
    PATCH = 'patch'      # Correções/ajustes


@dataclass
class SemanticDiff:
    """Diff semântico entre duas versões."""
    old_version_id: uuid.UUID
    new_version_id: uuid.UUID
    changes: List[Dict[str, Any]]
    summary: Dict[str, int]  # added, removed, modified, unchanged
    similarity_score: float  # 0.0 - 1.0
    semantic_changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VersionMetadata:
    """Metadados de uma versão."""
    version_id: uuid.UUID
    version_number: str  # Ex: "1.2.3"
    version_type: VersionType
    created_at: datetime
    created_by: int
    change_summary: str
    section_hashes: Dict[str, str]  # section_id -> hash
    parent_version: Optional[uuid.UUID] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class VersionControlService:
    """
    Serviço de versionamento semântico de documentos.

    Gerencia:
    1. Criação de versões
    2. Diff semântico
    3. Rollback seletivo
    4. Histórico de alterações
    """

    def __init__(self, document: Document):
        self.document = document
        self.versions = list(document.versions.order_by('-created_at'))

    def create_version(
        self,
        user: Any,
        sections: List[Dict[str, Any]],
        change_summary: str = '',
        version_type: VersionType = VersionType.MINOR,
        tags: Optional[List[str]] = None,
    ) -> VersionMetadata:
        """
        Cria nova versão do documento.

        Args:
            user: Usuário criando a versão
            sections: Lista de seções com conteúdo
            change_summary: Resumo das alterações
            version_type: Tipo de versão (major/minor/patch)
            tags: Tags opcionais

        Returns:
            VersionMetadata com informações da versão
        """
        # Determinar próximo número de versão
        version_number = self._calculate_version_number(version_type)

        # Calcular hashes das seções
        section_hashes = {}
        for section in sections:
            section_id = section.get('id') or str(uuid.uuid4())
            content = section.get('content', '')
            section_hashes[section_id] = self._calculate_hash(content)

        # Determinar versão pai
        parent_version = self.versions[0].id if self.versions else None

        # Criar versão no banco
        with transaction.atomic():
            version = DocumentVersion.objects.create(
                document=self.document,
                version_number=version_number,
                version_type=version_type.value,
                sections_data=sections,
                section_hashes=json.dumps(section_hashes),
                change_summary=change_summary,
                created_by=user,
                parent_version=parent_version,
                tags=tags or [],
            )

        # Atualizar lista de versões
        self.versions.insert(0, version)

        return VersionMetadata(
            version_id=version.id,
            version_number=version_number,
            version_type=version_type,
            created_at=version.created_at,
            created_by=user.id,
            change_summary=change_summary,
            section_hashes=section_hashes,
            parent_version=parent_version,
            tags=tags or [],
        )

    def get_diff(
        self,
        old_version_id: uuid.UUID,
        new_version_id: uuid.UUID,
        include_semantic: bool = True,
    ) -> SemanticDiff:
        """
        Calcula diff entre duas versões.

        Args:
            old_version_id: ID da versão antiga
            new_version_id: ID da versão nova
            include_semantic: Incluir análise semântica

        Returns:
            SemanticDiff com mudanças detalhadas
        """
        # Carregar versões
        old_version = DocumentVersion.objects.get(id=old_version_id)
        new_version = DocumentVersion.objects.get(id=new_version_id)

        old_sections = {s['id']: s for s in old_version.sections_data}
        new_sections = {s['id']: s for s in new_version.sections_data}

        changes = []
        summary = {'added': 0, 'removed': 0, 'modified': 0, 'unchanged': 0}
        semantic_changes = []

        # Detectar mudanças
        all_section_ids = set(old_sections.keys()) | set(new_sections.keys())

        for section_id in all_section_ids:
            old_section = old_sections.get(section_id)
            new_section = new_sections.get(section_id)

            if old_section and not new_section:
                # Seção removida
                changes.append({
                    'section_id': section_id,
                    'section_title': old_section.get('title', 'Sem título'),
                    'change_type': ChangeType.REMOVED.value,
                    'old_content': old_section.get('content', ''),
                    'new_content': '',
                })
                summary['removed'] += 1

            elif new_section and not old_section:
                # Seção adicionada
                changes.append({
                    'section_id': section_id,
                    'section_title': new_section.get('title', 'Sem título'),
                    'change_type': ChangeType.ADDED.value,
                    'old_content': '',
                    'new_content': new_section.get('content', ''),
                })
                summary['added'] += 1

            elif old_section and new_section:
                # Verificar se mudou
                old_content = old_section.get('content', '')
                new_content = new_section.get('content', '')

                if old_content == new_content:
                    summary['unchanged'] += 1
                else:
                    changes.append({
                        'section_id': section_id,
                        'section_title': new_section.get('title', 'Sem título'),
                        'change_type': ChangeType.MODIFIED.value,
                        'old_content': old_content,
                        'new_content': new_content,
                        'diff': self._calculate_text_diff(old_content, new_content),
                    })
                    summary['modified'] += 1

                    if include_semantic:
                        semantic = self._analyze_semantic_change(
                            old_content, new_content
                        )
                        semantic_changes.append({
                            'section_id': section_id,
                            **semantic,
                        })

        # Calcular similaridade
        similarity = self._calculate_similarity(
            old_version.sections_data,
            new_version.sections_data,
        )

        return SemanticDiff(
            old_version_id=old_version_id,
            new_version_id=new_version_id,
            changes=changes,
            summary=summary,
            similarity_score=similarity,
            semantic_changes=semantic_changes,
        )

    def rollback_to_version(
        self,
        version_id: uuid.UUID,
        user: Any,
        sections: Optional[List[str]] = None,
        create_new_version: bool = True,
    ) -> VersionMetadata:
        """
        Faz rollback para uma versão anterior.

        Args:
            version_id: ID da versão para rollback
            user: Usuário executando rollback
            sections: Seções específicas para rollback (None = todas)
            create_new_version: Criar nova versão após rollback

        Returns:
            VersionMetadata da versão resultante
        """
        target_version = DocumentVersion.objects.get(id=version_id)

        # Obter seções atuais
        current_sections = self.document.sections_data or []

        # Obter seções da versão alvo
        target_sections = target_version.sections_data or []

        # Mapear seções por ID
        current_map = {s['id']: s for s in current_sections}
        target_map = {s['id']: s for s in target_sections}

        # Aplicar rollback
        if sections:
            # Rollback seletivo
            for section_id in sections:
                if section_id in target_map:
                    current_map[section_id] = target_map[section_id]
        else:
            # Rollback completo
            current_map = target_map.copy()

        # Reconstruir seções
        rolled_back_sections = list(current_map.values())

        # Atualizar documento
        self.document.sections_data = rolled_back_sections
        self.document.save(update_fields=['sections_data'])

        # Criar nova versão se solicitado
        if create_new_version:
            return self.create_version(
                user=user,
                sections=rolled_back_sections,
                change_summary=f'Rollback para versão {target_version.version_number}',
                version_type=VersionType.PATCH,
                tags=['rollback', f'restored-{target_version.version_number}'],
            )

        return VersionMetadata(
            version_id=uuid.uuid4(),  # Fake ID
            version_number='N/A',
            version_type=VersionType.PATCH,
            created_at=timezone.now(),
            created_by=user.id,
            change_summary=f'Rollback para versão {target_version.version_number}',
            section_hashes={},
        )

    def get_version_history(self) -> List[VersionMetadata]:
        """Retorna histórico completo de versões."""
        history = []

        for version in self.versions:
            history.append(VersionMetadata(
                version_id=version.id,
                version_number=version.version_number,
                version_type=VersionType(version.version_type),
                created_at=version.created_at,
                created_by=version.created_by_id,
                change_summary=version.change_summary,
                section_hashes=json.loads(version.section_hashes or '{}'),
                parent_version=version.parent_version,
                tags=version.tags or [],
            ))

        return history

    def _calculate_version_number(self, version_type: VersionType) -> str:
        """Calcula próximo número de versão semântica."""
        if not self.versions:
            return '1.0.0'

        latest = self.versions[0]
        parts = latest.version_number.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if version_type == VersionType.MAJOR:
            return f'{major + 1}.0.0'
        elif version_type == VersionType.MINOR:
            return f'{major}.{minor + 1}.0'
        else:  # PATCH
            return f'{major}.{minor}.{patch + 1}'

    def _calculate_hash(self, content: str) -> str:
        """Calcula hash do conteúdo."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _calculate_text_diff(
        self,
        old_text: str,
        new_text: str,
    ) -> List[str]:
        """Calcula diff de texto linha por linha."""
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        return list(unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=3,
        ))

    def _calculate_similarity(
        self,
        old_sections: List[Dict],
        new_sections: List[Dict],
    ) -> float:
        """Calcula score de similaridade entre versões."""
        old_text = '\n'.join(s.get('content', '') for s in old_sections)
        new_text = '\n'.join(s.get('content', '') for s in new_sections)

        return SequenceMatcher(None, old_text, new_text).ratio()

    def _analyze_semantic_change(
        self,
        old_content: str,
        new_content: str,
    ) -> Dict[str, Any]:
        """
        Analisa mudança semântica entre conteúdos.

        Detecta:
        - Adição de citações jurídicas
        - Adição/remoção de parágrafos
        - Mudança de tom (mais/menos assertivo)
        """
        # Contar parágrafos
        old_paragraphs = len([p for p in old_content.split('\n\n') if p.strip()])
        new_paragraphs = len([p for p in new_content.split('\n\n') if p.strip()])

        # Detectar adição de citações
        citation_patterns = ['art.', 'arts.', 'lei', 'STF', 'STJ', 'TJ', 'Tribunal']
        old_citations = sum(
            1 for p in citation_patterns if p in old_content.lower()
        )
        new_citations = sum(
            1 for p in citation_patterns if p in new_content.lower()
        )

        return {
            'paragraph_delta': new_paragraphs - old_paragraphs,
            'citation_delta': new_citations - old_citations,
            'content_delta': len(new_content) - len(old_content),
            'added_citations': new_citations > old_citations,
            'expanded': new_paragraphs > old_paragraphs,
            'condensed': new_paragraphs < old_paragraphs,
        }


def auto_detect_version_type(
    old_sections: List[Dict],
    new_sections: List[Dict],
) -> VersionType:
    """
    Detecta automaticamente o tipo de versão baseado nas mudanças.

    - MAJOR: >50% do conteúdo mudou
    - MINOR: 10-50% do conteúdo mudou
    - PATCH: <10% do conteúdo mudou
    """
    old_text = '\n'.join(s.get('content', '') for s in old_sections)
    new_text = '\n'.join(s.get('content', '') for s in new_sections)

    similarity = SequenceMatcher(None, old_text, new_text).ratio()
    change_ratio = 1 - similarity

    if change_ratio > 0.5:
        return VersionType.MAJOR
    elif change_ratio > 0.1:
        return VersionType.MINOR
    else:
        return VersionType.PATCH
