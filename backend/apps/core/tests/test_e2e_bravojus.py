"""
Testes E2E - Verus.AI

Testa fluxos completos das funcionalidades:
1. Versionamento Semântico
2. Biblioteca Viva de Argumentos
3. Colaboração em Tempo Real
4. Integração com Tribunais
5. Radar de Precedentes
"""

import uuid
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class E2ETestCase(TestCase):
    """Case base para testes E2E"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@verus.ai',
            password='test123',
            role='superadmin'
        )
        self.client.force_authenticate(user=self.user)


class TestVersionamentoSemantico(E2ETestCase):
    """Testes E2E para Versionamento Semântico"""

    def setUp(self):
        super().setUp()
        from apps.documents.models import Document
        from apps.forms.models import FormTemplate

        # Criar form template
        self.form_template = FormTemplate.objects.create(
            name='Template Teste',
            schema={'type': 'object', 'properties': {}}
        )

        # Criar documento
        self.document = Document.objects.create(
            user=self.user,
            form_template=self.form_template,
            title='Documento Teste',
            data={'sections': []}
        )

    def test_criar_versao(self):
        """Testa criação de versão de documento"""
        sections = [
            {
                'id': str(uuid.uuid4()),
                'title': 'Seção 1',
                'content': 'Conteúdo da seção 1'
            }
        ]

        response = self.client.post(
            f'/api/v1/documents/items/{self.document.id}/versions/create/',
            {
                'sections': sections,
                'change_summary': 'Versão inicial',
                'version_type': 'minor'
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'version_id' in response.data
        assert response.data['version_number'] == '1.0.0'

    def test_listar_versoes(self):
        """Testa listagem de versões"""
        # Criar primeira versão
        self.client.post(
            f'/api/v1/documents/items/{self.document.id}/versions/create/',
            {
                'sections': [{'id': str(uuid.uuid4()), 'title': 'Teste', 'content': 'Conteúdo'}],
                'change_summary': 'Versão 1',
                'version_type': 'minor'
            },
            format='json'
        )

        # Listar versões
        response = self.client.get(
            f'/api/v1/documents/items/{self.document.id}/versions/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_diff_versoes(self):
        """Testa diff entre versões"""
        # Criar duas versões
        sections_v1 = [{'id': str(uuid.uuid4()), 'title': 'Teste', 'content': 'Conteúdo original'}]
        sections_v2 = [{'id': str(uuid.uuid4()), 'title': 'Teste', 'content': 'Conteúdo modificado'}]

        resp1 = self.client.post(
            f'/api/v1/documents/items/{self.document.id}/versions/create/',
            {'sections': sections_v1, 'version_type': 'minor'},
            format='json'
        )

        resp2 = self.client.post(
            f'/api/v1/documents/items/{self.document.id}/versions/create/',
            {'sections': sections_v2, 'version_type': 'minor'},
            format='json'
        )

        version1_id = resp1.data['version_id']
        version2_id = resp2.data['version_id']

        # Calcular diff
        response = self.client.get(
            f'/api/v1/documents/items/{self.document.id}/versions/diff/',
            {
                'old_version': version1_id,
                'new_version': version2_id
            }
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'summary' in response.data
        assert 'changes' in response.data


class TestBibliotecaArgumentosE2ETestCase:
    """Testes E2E para Biblioteca Viva de Argumentos"""

    def test_criar_argumento(self):
        """Testa criação de argumento jurídico"""
        response = self.client.post(
            '/api/v1/legal-library/arguments/',
            {
                'title': 'Tese de Prescrição',
                'content': 'Conteúdo da tese de prescrição...',
                'summary': 'Argumento sobre prescrição',
                'category': 'merito',
                'specialty': 'CIV',
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Tese de Prescrição'

    def test_listar_argumentos(self):
        """Testa listagem de argumentos"""
        # Criar argumento
        self.client.post(
            '/api/v1/legal-library/arguments/',
            {
                'title': 'Teste',
                'content': 'Conteúdo',
                'category': 'merito',
                'specialty': 'CIV',
            },
            format='json'
        )

        response = self.client.get('/api/v1/legal-library/arguments/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_sugerir_argumentos(self):
        """Testa sugestão de argumentos por contexto"""
        response = self.client.get(
            '/api/v1/legal-library/arguments/suggest/',
            {'query': 'prescrição', 'limit': 5}
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'suggestions' in response.data

    def test_registrar_uso_argumento(self):
        """Testa registro de uso de argumento"""
        # Criar argumento
        resp = self.client.post(
            '/api/v1/legal-library/arguments/',
            {
                'title': 'Teste',
                'content': 'Conteúdo',
                'category': 'merito',
                'specialty': 'CIV',
            },
            format='json'
        )

        argument_id = resp.data['id']

        # Registrar uso
        response = self.client.post(
            f'/api/v1/legal-library/arguments/{argument_id}/use/',
            {
                'document_id': str(uuid.uuid4()),
                'section_title': 'Fundamentação'
            },
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK


class TestColaboracaoE2ETestCase:
    """Testes E2E para Colaboração em Tempo Real"""

    def setUp(self):
        super().setUp()
        from apps.documents.models import Document
        from apps.forms.models import FormTemplate

        self.form_template = FormTemplate.objects.create(
            name='Template Teste',
            schema={'type': 'object', 'properties': {}}
        )

        self.document = Document.objects.create(
            user=self.user,
            form_template=self.form_template,
            title='Documento Colaborativo'
        )

    def test_criar_sessao_colaboracao(self):
        """Testa criação de sessão de colaboração"""
        response = self.client.post(
            f'/api/v1/collaboration/documents/{self.document.id}/start-session/',
            {},
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['document_id'] == str(self.document.id)

    def test_entrar_sessao(self):
        """Testa entrada em sessão de colaboração"""
        # Criar sessão
        resp = self.client.post(
            f'/api/v1/collaboration/documents/{self.document.id}/start-session/',
            {},
            format='json'
        )
        session_id = resp.data['id']

        # Entrar na sessão
        response = self.client.post(
            f'/api/v1/collaboration/sessions/{session_id}/join/',
            {},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_listar_colaboradores(self):
        """Testa listagem de colaboradores"""
        # Criar e entrar na sessão
        resp = self.client.post(
            f'/api/v1/collaboration/documents/{self.document.id}/start-session/',
            {},
            format='json'
        )
        session_id = resp.data['id']
        self.client.post(f'/api/v1/collaboration/sessions/{session_id}/join/')

        # Listar colaboradores
        response = self.client.get(
            f'/api/v1/collaboration/sessions/{session_id}/collaborators/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'collaborators' in response.data

    def test_criar_comentario(self):
        """Testa criação de comentário"""
        # Criar sessão
        resp = self.client.post(
            f'/api/v1/collaboration/documents/{self.document.id}/start-session/',
            {},
            format='json'
        )
        session_id = resp.data['id']

        # Criar comentário
        response = self.client.post(
            f'/api/v1/collaboration/comments/?session_id={session_id}',
            {'content': 'Comentário de teste'},
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_criar_sugestao(self):
        """Testa criação de sugestão"""
        # Criar sessão
        resp = self.client.post(
            f'/api/v1/collaboration/documents/{self.document.id}/start-session/',
            {},
            format='json'
        )
        session_id = resp.data['id']

        # Criar sugestão
        response = self.client.post(
            f'/api/v1/collaboration/suggestions/?session_id={session_id}',
            {
                'original_text': 'Texto original',
                'suggested_text': 'Texto sugerido',
                'comment': 'Melhoria'
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED


class TestIntegracaoTribunaisE2ETestCase:
    """Testes E2E para Integração com Tribunais"""

    def test_criar_tribunal(self):
        """Testa criação de integração com tribunal"""
        response = self.client.post(
            '/api/v1/integration/tribunais/',
            {
                'name': 'TJSP',
                'code': 'TJSP',
                'system_type': 'esaj',
                'api_endpoint': 'https://esaj.tjsp.jus.br',
                'is_active': True
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_listar_tribunais(self):
        """Testa listagem de tribunais"""
        # Criar tribunal
        self.client.post(
            '/api/v1/integration/tribunais/',
            {
                'name': 'TJSP',
                'code': 'TJSP',
                'system_type': 'esaj',
                'api_endpoint': 'https://esaj.tjsp.jus.br',
                'is_active': True
            },
            format='json'
        )

        response = self.client.get('/api/v1/integration/tribunais/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data.get('results'), list)

    def test_sincronizar_processo(self):
        """Testa sincronização de processo"""
        # Criar tribunal
        resp = self.client.post(
            '/api/v1/integration/tribunais/',
            {
                'name': 'TJSP',
                'code': 'TJSP',
                'system_type': 'esaj',
                'api_endpoint': 'https://esaj.tjsp.jus.br',
                'is_active': True
            },
            format='json'
        )
        tribunal_id = resp.data['id']

        # Sincronizar processo
        response = self.client.post(
            '/api/v1/integration/processes/sync/',
            {
                'tribunal_id': tribunal_id,
                'process_number': '0000000-00.2024.8.26.0000'
            },
            format='json'
        )

        # Pode retornar 202 (pendente) ou 200 (completo)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]

    def test_criar_peticao(self):
        """Testa criação de petição para protocolo"""
        # Criar tribunal
        resp = self.client.post(
            '/api/v1/integration/tribunais/',
            {
                'name': 'TJSP',
                'code': 'TJSP',
                'system_type': 'esaj',
                'is_active': True
            },
            format='json'
        )
        tribunal_id = resp.data['id']

        # Criar petição
        response = self.client.post(
            '/api/v1/integration/petitions/',
            {
                'tribunal_id': tribunal_id,
                'process_number': '0000000-00.2024.8.26.0000',
                'petition_type': 'inicial',
                'petition_title': 'Petição Inicial',
                'petition_content': 'Conteúdo da petição...',
                'attachments': []
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED


class TestRadarPrecedentesE2ETestCase:
    """Testes E2E para Radar de Precedentes"""

    def test_analisar_precedentes(self):
        """Testa análise de precedentes"""
        response = self.client.post(
            '/api/v1/jurisprudence/radar/analyze/',
            {
                'query': 'responsabilidade civil dano moral',
                'specialty': 'CIV',
                'include_timeline': True,
                'limit_precedents': 10
            },
            format='json'
        )

        # Deve retornar 200 (com dados) ou 200 vazio (sem dados)
        assert response.status_code == status.HTTP_200_OK
        assert 'query' in response.data

    def test_listar_tribunais_stats(self):
        """Testa listagem de estatísticas por tribunal"""
        response = self.client.get('/api/v1/jurisprudence/radar/tribunais/')

        assert response.status_code == status.HTTP_200_OK
        assert 'tribunais' in response.data

    def test_listar_teses_stats(self):
        """Testa listagem de estatísticas por tese"""
        response = self.client.get('/api/v1/jurisprudence/radar/teses/')

        assert response.status_code == status.HTTP_200_OK
        assert 'theses' in response.data


class TestFluxoCompleto(E2ETestCase):
    """Teste de fluxo completo integrado"""

    def test_fluxo_documento_completo(self):
        """
        Testa fluxo completo:
        1. Criar documento
        2. Criar versão
        3. Iniciar colaboração
        4. Adicionar comentário
        5. Usar argumento da biblioteca
        6. Sincronizar com tribunal
        """
        from apps.documents.models import Document
        from apps.forms.models import FormTemplate

        # Setup
        form_template = FormTemplate.objects.create(
            name='Template Teste',
            schema={'type': 'object', 'properties': {}}
        )

        document = Document.objects.create(
            user=self.user,
            form_template=form_template,
            title='Documento Completo'
        )

        # 1. Criar versão
        resp = self.client.post(
            f'/api/v1/documents/items/{document.id}/versions/create/',
            {
                'sections': [{'id': str(uuid.uuid4()), 'title': 'Teste', 'content': 'Conteúdo'}],
                'version_type': 'minor'
            },
            format='json'
        )
        assert resp.status_code == status.HTTP_201_CREATED

        # 2. Iniciar colaboração
        resp = self.client.post(
            f'/api/v1/collaboration/documents/{document.id}/start-session/',
            {},
            format='json'
        )
        assert resp.status_code == status.HTTP_201_CREATED
        session_id = resp.data['id']

        # 3. Adicionar comentário
        resp = self.client.post(
            f'/api/v1/collaboration/comments/?session_id={session_id}',
            {'content': 'Comentário'},
            format='json'
        )
        assert resp.status_code == status.HTTP_201_CREATED

        # 4. Criar e usar argumento
        resp = self.client.post(
            '/api/v1/legal-library/arguments/',
            {
                'title': 'Argumento Teste',
                'content': 'Conteúdo',
                'category': 'merito',
                'specialty': 'CIV'
            },
            format='json'
        )
        argument_id = resp.data['id']

        resp = self.client.post(
            f'/api/v1/legal-library/arguments/{argument_id}/use/',
            {'document_id': str(document.id)},
            format='json'
        )
        assert resp.status_code == status.HTTP_200_OK

        # 5. Criar tribunal e sincronizar
        resp = self.client.post(
            '/api/v1/integration/tribunais/',
            {
                'name': 'TJSP',
                'code': 'TJSP',
                'system_type': 'esaj',
                'is_active': True
            },
            format='json'
        )
        tribunal_id = resp.data['id']

        resp = self.client.post(
            '/api/v1/integration/processes/sync/',
            {
                'tribunal_id': tribunal_id,
                'process_number': '0000000-00.2024.8.26.0000',
                'case_id': str(document.id)
            },
            format='json'
        )
        assert resp.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]

        print('✅ Fluxo completo testado com sucesso!')
