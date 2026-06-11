#!/usr/bin/env python
"""
Management command para criar Template e Formulário completo de ETP
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.forms.models import FormTemplate
from apps.templates.models import DocumentTemplate
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria template de documento HTML e formulário completo de ETP'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('🚀 CRIANDO TEMPLATE E FORMULÁRIO COMPLETO DE ETP'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Buscar usuário admin para criar os templates
        try:
            admin_user = User.objects.filter(role__in=['superadmin', 'admin', 'gestor', 'manager']).first()
            if not admin_user:
                admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('Nenhum usuário admin encontrado. Execute populate_users primeiro.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao buscar usuário: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'✓ Usuário: {admin_user.username}'))

        # Criar template de documento HTML
        template_id = self.criar_template_documento(admin_user)

        # Criar formulário
        form_id = self.criar_formulario(admin_user)

        # Resumo
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('📊 RESUMO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if template_id and form_id:
            self.stdout.write(self.style.SUCCESS(f'✅ Template UUID: {template_id}'))
            self.stdout.write(self.style.SUCCESS(f'✅ Formulário UUID: {form_id}'))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 Tudo criado com sucesso!'))
            self.stdout.write('')
            self.stdout.write('📝 Próximos passos:')
            self.stdout.write('1. Acesse /criar-documento no frontend')
            self.stdout.write('2. Selecione o Template e Formulário criados')
            self.stdout.write('3. Comece a preencher!')
        else:
            self.stdout.write(self.style.ERROR('❌ Houve erros na criação.'))

    def criar_template_documento(self, admin_user):
        """Cria template de documento HTML"""
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📄 Criando Template de Documento...'))

        # Ler o arquivo HTML
        html_path = os.path.join(
            os.path.dirname(__file__),
            '../../../../../frontend/template_exemplo_etp.html'
        )

        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ Arquivo não encontrado: {html_path}'))
            return None

        # Verificar se já existe
        existing = DocumentTemplate.objects.filter(
            name="Template ETP - Estudo Técnico Preliminar"
        ).first()

        if existing:
            self.stdout.write(self.style.WARNING(f'⚠️  Template já existe com UUID: {existing.id}'))
            return existing.id

        # Criar template
        template = DocumentTemplate.objects.create(
            name="Template ETP - Estudo Técnico Preliminar",
            description="Template completo de ETP conforme Lei 14.133/2021 com 15 seções",
            content=html_content,
            is_active=True,
            created_by=admin_user
        )

        self.stdout.write(self.style.SUCCESS(f'✅ Template criado com UUID: {template.id}'))
        return template.id

    def criar_formulario(self, admin_user):
        """Cria formulário JSON com estrutura flat"""
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📝 Criando Formulário...'))

        # Verificar se já existe
        existing = FormTemplate.objects.filter(
            name="Formulário ETP - Estudo Técnico Preliminar"
        ).first()

        if existing:
            self.stdout.write(self.style.WARNING(f'⚠️  Formulário já existe com UUID: {existing.id}'))
            return existing.id

        # Campos em estrutura flat (conforme populate_forms.py)
        fields = [
            # Seção 1: Informações Básicas
            {
                "id": "orgao",
                "type": "text",
                "label": "Órgão/Entidade",
                "required": True,
                "placeholder": "Ex: Prefeitura Municipal de...",
                "help_text": "Nome completo do órgão ou entidade pública"
            },
            {
                "id": "unidade_administrativa",
                "type": "text",
                "label": "Unidade Administrativa",
                "required": True,
                "placeholder": "Ex: Secretaria de Administração",
                "help_text": "Unidade administrativa responsável"
            },
            {
                "id": "numero_processo",
                "type": "text",
                "label": "Número do Processo",
                "required": True,
                "placeholder": "Ex: 2024/001234-5",
                "help_text": "Número completo do processo administrativo"
            },
            {
                "id": "objeto_contratacao",
                "type": "textarea",
                "label": "Objeto da Contratação",
                "required": True,
                "placeholder": "Descreva o objeto da contratação...",
                "help_text": "Descrição clara e objetiva do que será contratado"
            },
            {
                "id": "responsavel_elaboracao",
                "type": "text",
                "label": "Responsável pela Elaboração",
                "required": True,
                "placeholder": "Nome completo",
                "help_text": "Nome do servidor responsável pela elaboração do ETP"
            },
            {
                "id": "cargo_responsavel",
                "type": "text",
                "label": "Cargo do Responsável",
                "required": True,
                "placeholder": "Ex: Analista de Compras",
                "help_text": "Cargo ocupado pelo responsável"
            },
            {
                "id": "matricula_responsavel",
                "type": "text",
                "label": "Matrícula do Responsável",
                "required": False,
                "placeholder": "Ex: 123456",
                "help_text": "Matrícula funcional (se aplicável)"
            },
            {
                "id": "data_elaboracao",
                "type": "date",
                "label": "Data de Elaboração",
                "required": True,
                "help_text": "Data de elaboração do documento"
            },

            # Seção 2: Descrição da Necessidade
            {
                "id": "introducao",
                "type": "textarea",
                "label": "Introdução",
                "required": True,
                "placeholder": "Apresente o contexto geral...",
                "help_text": "Apresentação geral do documento e seu propósito"
            },
            {
                "id": "contexto_demanda",
                "type": "textarea",
                "label": "Contexto da Demanda",
                "required": True,
                "placeholder": "Descreva o contexto que originou a demanda...",
                "help_text": "Explique a situação atual e o que motivou a necessidade"
            },
            {
                "id": "justificativa_contratacao",
                "type": "textarea",
                "label": "Justificativa da Contratação",
                "required": True,
                "placeholder": "Justifique a necessidade da contratação...",
                "help_text": "Por que esta contratação é necessária? Quais problemas resolve?"
            },
            {
                "id": "relacao_planejamento",
                "type": "textarea",
                "label": "Relação com o Planejamento Estratégico",
                "required": True,
                "placeholder": "Explique como se relaciona com o planejamento...",
                "help_text": "Como esta contratação se alinha aos objetivos estratégicos?"
            },

            # Seção 3: Área Requisitante
            {
                "id": "area_requisitante",
                "type": "text",
                "label": "Unidade Requisitante",
                "required": True,
                "placeholder": "Ex: Departamento de TI",
                "help_text": "Área que demandou a contratação"
            },
            {
                "id": "responsavel_area",
                "type": "text",
                "label": "Responsável pela Área",
                "required": True,
                "placeholder": "Nome do responsável",
                "help_text": "Gestor ou responsável pela área requisitante"
            },
            {
                "id": "contato_area",
                "type": "text",
                "label": "Contato da Área",
                "required": True,
                "placeholder": "Email e/ou telefone",
                "help_text": "Informações de contato da área requisitante"
            },

            # Seção 4: Requisitos da Contratação
            {
                "id": "requisitos_objeto",
                "type": "textarea",
                "label": "Requisitos do Objeto",
                "required": True,
                "placeholder": "Descreva os requisitos do objeto...",
                "help_text": "Características e especificações do que será contratado"
            },
            {
                "id": "requisitos_tecnicos",
                "type": "textarea",
                "label": "Requisitos Técnicos",
                "required": True,
                "placeholder": "Liste os requisitos técnicos...",
                "help_text": "Especificações técnicas obrigatórias"
            },
            {
                "id": "requisitos_qualidade",
                "type": "textarea",
                "label": "Requisitos de Qualidade",
                "required": True,
                "placeholder": "Defina os padrões de qualidade...",
                "help_text": "Padrões de qualidade exigidos"
            },
            {
                "id": "requisitos_capacitacao",
                "type": "textarea",
                "label": "Requisitos de Capacitação",
                "required": False,
                "placeholder": "Necessidades de treinamento...",
                "help_text": "Treinamentos ou capacitações necessárias (se aplicável)"
            },

            # Seção 5: Pesquisa de Mercado
            {
                "id": "pesquisa_precos",
                "type": "textarea",
                "label": "Descrição da Pesquisa de Preços",
                "required": True,
                "placeholder": "Descreva como foi feita a pesquisa...",
                "help_text": "Metodologia utilizada na pesquisa de preços"
            },
            {
                "id": "fornecedor_1",
                "type": "text",
                "label": "Fornecedor 1",
                "required": True,
                "placeholder": "Nome do fornecedor",
                "help_text": "Primeiro fornecedor pesquisado"
            },
            {
                "id": "valor_unitario_1",
                "type": "text",
                "label": "Valor Unitário - Fornecedor 1",
                "required": True,
                "placeholder": "Ex: 1.500,00",
                "help_text": "Valor unitário cotado"
            },
            {
                "id": "quantidade_1",
                "type": "number",
                "label": "Quantidade - Fornecedor 1",
                "required": True,
                "placeholder": "Ex: 10",
                "help_text": "Quantidade cotada"
            },
            {
                "id": "valor_total_1",
                "type": "text",
                "label": "Valor Total - Fornecedor 1",
                "required": True,
                "placeholder": "Ex: 15.000,00",
                "help_text": "Valor total da cotação"
            },
            {
                "id": "fornecedor_2",
                "type": "text",
                "label": "Fornecedor 2",
                "required": True,
                "placeholder": "Nome do fornecedor",
                "help_text": "Segundo fornecedor pesquisado"
            },
            {
                "id": "valor_unitario_2",
                "type": "text",
                "label": "Valor Unitário - Fornecedor 2",
                "required": True,
                "placeholder": "Ex: 1.500,00",
                "help_text": "Valor unitário cotado"
            },
            {
                "id": "quantidade_2",
                "type": "number",
                "label": "Quantidade - Fornecedor 2",
                "required": True,
                "placeholder": "Ex: 10",
                "help_text": "Quantidade cotada"
            },
            {
                "id": "valor_total_2",
                "type": "text",
                "label": "Valor Total - Fornecedor 2",
                "required": True,
                "placeholder": "Ex: 15.000,00",
                "help_text": "Valor total da cotação"
            },
            {
                "id": "fornecedor_3",
                "type": "text",
                "label": "Fornecedor 3",
                "required": True,
                "placeholder": "Nome do fornecedor",
                "help_text": "Terceiro fornecedor pesquisado"
            },
            {
                "id": "valor_unitario_3",
                "type": "text",
                "label": "Valor Unitário - Fornecedor 3",
                "required": True,
                "placeholder": "Ex: 1.500,00",
                "help_text": "Valor unitário cotado"
            },
            {
                "id": "quantidade_3",
                "type": "number",
                "label": "Quantidade - Fornecedor 3",
                "required": True,
                "placeholder": "Ex: 10",
                "help_text": "Quantidade cotada"
            },
            {
                "id": "valor_total_3",
                "type": "text",
                "label": "Valor Total - Fornecedor 3",
                "required": True,
                "placeholder": "Ex: 15.000,00",
                "help_text": "Valor total da cotação"
            },
            {
                "id": "analise_propostas",
                "type": "textarea",
                "label": "Análise das Propostas",
                "required": True,
                "placeholder": "Analise comparativa das propostas...",
                "help_text": "Análise técnica e comparação dos orçamentos"
            },

            # Seção 6: Estimativa de Custos
            {
                "id": "descricao_valor_global",
                "type": "text",
                "label": "Descrição do Valor Global",
                "required": True,
                "placeholder": "Ex: Valor total da contratação para 12 meses",
                "help_text": "Detalhamento do valor global"
            },
            {
                "id": "valor_global",
                "type": "text",
                "label": "Valor Global Estimado",
                "required": True,
                "placeholder": "Ex: 180.000,00",
                "help_text": "Valor total estimado da contratação"
            },
            {
                "id": "descricao_custos_treinamento",
                "type": "text",
                "label": "Descrição dos Custos de Treinamento",
                "required": False,
                "placeholder": "Ex: Capacitação de 20 servidores",
                "help_text": "Detalhamento dos custos com treinamento"
            },
            {
                "id": "custos_treinamento",
                "type": "text",
                "label": "Custos com Treinamento",
                "required": False,
                "placeholder": "Ex: 5.000,00",
                "help_text": "Valor estimado para treinamentos"
            },
            {
                "id": "descricao_custos_adicionais",
                "type": "text",
                "label": "Descrição de Custos Adicionais",
                "required": False,
                "placeholder": "Ex: Instalação e configuração",
                "help_text": "Outros custos previstos"
            },
            {
                "id": "custos_adicionais",
                "type": "text",
                "label": "Custos Adicionais",
                "required": False,
                "placeholder": "Ex: 3.000,00",
                "help_text": "Valor de custos extras"
            },
            {
                "id": "valor_total_estimado",
                "type": "text",
                "label": "Valor Total Estimado",
                "required": True,
                "placeholder": "Ex: 188.000,00",
                "help_text": "Soma de todos os custos"
            },
            {
                "id": "fonte_recursos",
                "type": "text",
                "label": "Fonte de Recursos",
                "required": True,
                "placeholder": "Ex: Orçamento próprio",
                "help_text": "De onde virão os recursos financeiros"
            },
            {
                "id": "natureza_despesa",
                "type": "text",
                "label": "Natureza de Despesa",
                "required": True,
                "placeholder": "Ex: 3.3.90.39",
                "help_text": "Classificação da natureza da despesa"
            },
            {
                "id": "rubrica_orcamentaria",
                "type": "text",
                "label": "Rubrica Orçamentária",
                "required": True,
                "placeholder": "Ex: 123456",
                "help_text": "Código da rubrica orçamentária"
            },

            # Seção 7: Descrição da Solução
            {
                "id": "descricao_solucao",
                "type": "textarea",
                "label": "Descrição da Solução como um Todo",
                "required": True,
                "placeholder": "Descreva a solução completa...",
                "help_text": "Visão geral da solução proposta"
            },
            {
                "id": "forma_prestacao",
                "type": "textarea",
                "label": "Forma de Prestação do Serviço/Fornecimento",
                "required": True,
                "placeholder": "Como será prestado o serviço...",
                "help_text": "Detalhamento de como será executado"
            },
            {
                "id": "prazos_execucao",
                "type": "textarea",
                "label": "Prazos de Execução",
                "required": True,
                "placeholder": "Defina os prazos...",
                "help_text": "Cronograma de execução"
            },
            {
                "id": "justificativa_parcelamento",
                "type": "textarea",
                "label": "Justificativa para Parcelamento ou Não",
                "required": True,
                "placeholder": "Justifique se haverá parcelamento...",
                "help_text": "Por que será ou não parcelado?"
            },
            {
                "id": "contratacoes_correlatas",
                "type": "textarea",
                "label": "Contratações Correlatas e/ou Interdependentes",
                "required": True,
                "placeholder": "Liste contratações relacionadas...",
                "help_text": "Outras contratações necessárias ou relacionadas"
            },

            # Seção 8: Conformidade e Impactos
            {
                "id": "alinhamento_planejamento",
                "type": "textarea",
                "label": "Alinhamento com o Planejamento",
                "required": True,
                "placeholder": "Explique o alinhamento...",
                "help_text": "Como se alinha ao planejamento institucional"
            },
            {
                "id": "conformidade_lei_14133",
                "type": "textarea",
                "label": "Conformidade com a Lei nº 14.133/2021",
                "required": True,
                "placeholder": "Cite os artigos aplicáveis...",
                "help_text": "Fundamentação legal na nova lei de licitações"
            },
            {
                "id": "outras_normas",
                "type": "textarea",
                "label": "Outras Normas Aplicáveis",
                "required": False,
                "placeholder": "Liste outras normas...",
                "help_text": "Outras legislações relevantes"
            },
            {
                "id": "impactos_ambientais",
                "type": "textarea",
                "label": "Análise de Impactos Ambientais",
                "required": True,
                "placeholder": "Avalie os possíveis impactos...",
                "help_text": "Impactos ambientais da contratação"
            },
            {
                "id": "beneficios_diretos",
                "type": "textarea",
                "label": "Benefícios Diretos",
                "required": True,
                "placeholder": "Liste os benefícios diretos...",
                "help_text": "Benefícios imediatos da contratação"
            },
            {
                "id": "beneficios_indiretos",
                "type": "textarea",
                "label": "Benefícios Indiretos",
                "required": True,
                "placeholder": "Liste os benefícios indiretos...",
                "help_text": "Benefícios secundários esperados"
            },

            # Seção 9: Gestão de Riscos
            {
                "id": "risco_1",
                "type": "text",
                "label": "Risco Identificado 1",
                "required": True,
                "placeholder": "Ex: Atraso na entrega",
                "help_text": "Primeiro risco identificado"
            },
            {
                "id": "probabilidade_1",
                "type": "select",
                "label": "Probabilidade do Risco 1",
                "required": True,
                "options": ["Baixa", "Média", "Alta"],
                "help_text": "Probabilidade de ocorrência"
            },
            {
                "id": "impacto_1",
                "type": "select",
                "label": "Impacto do Risco 1",
                "required": True,
                "options": ["Baixo", "Médio", "Alto"],
                "help_text": "Impacto se o risco ocorrer"
            },
            {
                "id": "mitigacao_1",
                "type": "textarea",
                "label": "Medidas de Mitigação do Risco 1",
                "required": True,
                "placeholder": "Ações para mitigar o risco...",
                "help_text": "Como reduzir ou evitar o risco"
            },
            {
                "id": "risco_2",
                "type": "text",
                "label": "Risco Identificado 2",
                "required": True,
                "placeholder": "Ex: Problemas de qualidade",
                "help_text": "Segundo risco identificado"
            },
            {
                "id": "probabilidade_2",
                "type": "select",
                "label": "Probabilidade do Risco 2",
                "required": True,
                "options": ["Baixa", "Média", "Alta"],
                "help_text": "Probabilidade de ocorrência"
            },
            {
                "id": "impacto_2",
                "type": "select",
                "label": "Impacto do Risco 2",
                "required": True,
                "options": ["Baixo", "Médio", "Alto"],
                "help_text": "Impacto se o risco ocorrer"
            },
            {
                "id": "mitigacao_2",
                "type": "textarea",
                "label": "Medidas de Mitigação do Risco 2",
                "required": True,
                "placeholder": "Ações para mitigar o risco...",
                "help_text": "Como reduzir ou evitar o risco"
            },
            {
                "id": "risco_3",
                "type": "text",
                "label": "Risco Identificado 3",
                "required": True,
                "placeholder": "Ex: Orçamento insuficiente",
                "help_text": "Terceiro risco identificado"
            },
            {
                "id": "probabilidade_3",
                "type": "select",
                "label": "Probabilidade do Risco 3",
                "required": True,
                "options": ["Baixa", "Média", "Alta"],
                "help_text": "Probabilidade de ocorrência"
            },
            {
                "id": "impacto_3",
                "type": "select",
                "label": "Impacto do Risco 3",
                "required": True,
                "options": ["Baixo", "Médio", "Alto"],
                "help_text": "Impacto se o risco ocorrer"
            },
            {
                "id": "mitigacao_3",
                "type": "textarea",
                "label": "Medidas de Mitigação do Risco 3",
                "required": True,
                "placeholder": "Ações para mitigar o risco...",
                "help_text": "Como reduzir ou evitar o risco"
            },

            # Seção 10: Conclusão e Aprovação
            {
                "id": "providencias",
                "type": "textarea",
                "label": "Providências a Serem Adotadas",
                "required": True,
                "placeholder": "Liste as próximas providências...",
                "help_text": "Próximos passos após aprovação do ETP"
            },
            {
                "id": "conclusao",
                "type": "textarea",
                "label": "Conclusão e Recomendações",
                "required": True,
                "placeholder": "Redija a conclusão...",
                "help_text": "Considerações finais e recomendações"
            },
            {
                "id": "aprovador",
                "type": "text",
                "label": "Nome do Aprovador",
                "required": True,
                "placeholder": "Nome completo",
                "help_text": "Quem irá aprovar o documento"
            },
            {
                "id": "cargo_aprovador",
                "type": "text",
                "label": "Cargo do Aprovador",
                "required": True,
                "placeholder": "Ex: Secretário de Administração",
                "help_text": "Cargo do aprovador"
            },
            {
                "id": "data_geracao",
                "type": "date",
                "label": "Data de Geração do Documento",
                "required": True,
                "help_text": "Data em que o documento foi gerado"
            }
        ]

        # Criar formulário
        form = FormTemplate.objects.create(
            name="Formulário ETP - Estudo Técnico Preliminar",
            description="Formulário completo para criação de ETP com 9 seções e 70+ campos conforme Lei 14.133/2021",
            fields=fields,
            is_active=True,
            created_by=admin_user
        )

        self.stdout.write(self.style.SUCCESS(f'✅ Formulário criado com UUID: {form.id}'))
        self.stdout.write(self.style.SUCCESS(f'✅ Total de campos: {len(fields)}'))
        return form.id
