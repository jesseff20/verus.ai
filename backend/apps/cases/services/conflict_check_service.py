"""
Serviço de Verificação de Conflito de Interesses (OAB Art. 19).
"""
import logging
from django.db.models import Q
from apps.cases.models import LegalCase, Client

logger = logging.getLogger(__name__)


class ConflictCheckService:
    """Verifica conflitos de interesse ao cadastrar novo cliente."""

    @staticmethod
    def check_conflicts(name: str, cpf_cnpj: str = '', client_id=None) -> dict:
        """
        Cruza dados do novo cliente com partes adversas de todos os casos.

        Returns dict with:
        - has_conflicts: bool
        - conflicts: list of conflict details
        - severity: 'none' | 'warning' | 'critical'
        """
        conflicts = []

        # 1. Busca por CPF/CNPJ exato (critical)
        if cpf_cnpj:
            cpf_clean = cpf_cnpj.replace('.', '').replace('-', '').replace('/', '')
            cases_by_cpf = LegalCase.objects.filter(
                Q(parte_contraria_cpf_cnpj__icontains=cpf_clean) |
                Q(parte_contraria_cpf_cnpj=cpf_cnpj)
            ).select_related('advogado_responsavel', 'client')

            for case in cases_by_cpf:
                conflicts.append({
                    'type': 'cpf_cnpj_match',
                    'severity': 'critical',
                    'case_id': str(case.id),
                    'case_titulo': case.titulo,
                    'numero_processo': case.numero_processo,
                    'parte_contraria': case.parte_contraria,
                    'advogado': case.advogado_responsavel.get_full_name() if case.advogado_responsavel else None,
                    'client_name': case.client.name if case.client else case.cliente_nome,
                    'message': f'CPF/CNPJ "{cpf_cnpj}" aparece como parte contrária no caso "{case.titulo}"',
                })

        # 2. Busca por nome similar (warning)
        if name and len(name) >= 3:
            name_parts = name.strip().split()
            name_query = Q()
            for part in name_parts:
                if len(part) >= 3:
                    name_query |= Q(parte_contraria__icontains=part)

            if name_query:
                cases_by_name = LegalCase.objects.filter(name_query).select_related(
                    'advogado_responsavel', 'client'
                )

                existing_case_ids = {c['case_id'] for c in conflicts}

                for case in cases_by_name:
                    if str(case.id) in existing_case_ids:
                        continue

                    # Calculate name similarity
                    similarity = ConflictCheckService._name_similarity(name, case.parte_contraria)
                    if similarity >= 0.6:
                        severity = 'critical' if similarity >= 0.9 else 'warning'
                        conflicts.append({
                            'type': 'name_similarity',
                            'severity': severity,
                            'similarity': round(similarity, 2),
                            'case_id': str(case.id),
                            'case_titulo': case.titulo,
                            'numero_processo': case.numero_processo,
                            'parte_contraria': case.parte_contraria,
                            'advogado': case.advogado_responsavel.get_full_name() if case.advogado_responsavel else None,
                            'client_name': case.client.name if case.client else case.cliente_nome,
                            'message': f'Nome similar encontrado: "{case.parte_contraria}" no caso "{case.titulo}" (similaridade: {round(similarity*100)}%)',
                        })

        # 3. Verifica se o nome aparece como cliente em caso onde ele seria parte contrária
        if name:
            reverse_conflicts = Client.objects.filter(
                Q(name__icontains=name) | (Q(cpf_cnpj=cpf_cnpj) if cpf_cnpj else Q())
            ).exclude(id=client_id) if client_id else Client.objects.filter(
                Q(name__icontains=name) | (Q(cpf_cnpj=cpf_cnpj) if cpf_cnpj else Q())
            )

            for client in reverse_conflicts:
                for case in client.cases.all():
                    if case.parte_contraria and ConflictCheckService._name_similarity(name, case.cliente_nome) >= 0.8:
                        conflicts.append({
                            'type': 'reverse_conflict',
                            'severity': 'critical',
                            'case_id': str(case.id),
                            'case_titulo': case.titulo,
                            'numero_processo': case.numero_processo,
                            'existing_client': client.name,
                            'message': f'Cliente existente "{client.name}" já é representado em caso onde nome similar é parte contrária',
                        })

        # Determine overall severity
        severities = [c['severity'] for c in conflicts]
        if 'critical' in severities:
            overall_severity = 'critical'
        elif 'warning' in severities:
            overall_severity = 'warning'
        else:
            overall_severity = 'none'

        # Gather metadata for transparency
        total_cases_checked = LegalCase.objects.count()
        total_clients_checked = Client.objects.count()
        total_adverse_parties = LegalCase.objects.exclude(
            parte_contraria__isnull=True
        ).exclude(parte_contraria='').count()

        criteria_used = ['CPF/CNPJ exato']
        if name and len(name) >= 3:
            criteria_used.append('Similaridade de nome (threshold 60%)')
        criteria_used.append('Conflito reverso (cliente existente como parte contrária)')

        search_scope = [
            'Casos ativos',
            'Casos arquivados',
            'Clientes cadastrados',
        ]

        return {
            'has_conflicts': len(conflicts) > 0,
            'total_conflicts': len(conflicts),
            'severity': overall_severity,
            'conflicts': conflicts,
            'oab_reference': 'Art. 19 do Código de Ética e Disciplina da OAB',
            'total_cases_checked': total_cases_checked,
            'total_clients_checked': total_clients_checked,
            'total_adverse_parties_checked': total_adverse_parties,
            'criteria_used': criteria_used,
            'search_scope': search_scope,
        }

    @staticmethod
    def _name_similarity(name1: str, name2: str) -> float:
        """Simple name similarity using token overlap."""
        if not name1 or not name2:
            return 0.0
        tokens1 = set(name1.lower().split())
        tokens2 = set(name2.lower().split())
        # Remove common prepositions
        stop_words = {'de', 'da', 'do', 'dos', 'das', 'e', 'a', 'o'}
        tokens1 -= stop_words
        tokens2 -= stop_words
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        return len(intersection) / len(union)
