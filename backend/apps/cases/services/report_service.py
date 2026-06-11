"""
ReportService - Gera relatorios de andamento processual e portfolio para o Verus.AI.
"""
import io
import logging
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone

logger = logging.getLogger(__name__)


class ReportService:
    """Servico de relatorios de casos juridicos."""

    @staticmethod
    def _user_cases_qs(user):
        """Retorna queryset de LegalCase filtrado pelo usuario."""
        from apps.cases.models import LegalCase

        qs = LegalCase.objects.all()
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(
                Q(advogado_responsavel=user) | Q(created_by=user)
            )
        return qs

    @classmethod
    def generate_case_progress_report(cls, case_id, user) -> dict:
        """
        Gera relatorio completo de andamento de um caso.
        Inclui: info do caso, fases, prazos, documentos, notificacoes, atividades.
        """
        from apps.cases.models import (
            LegalCase, LegalDeadline, CaseTask, CaseDocument,
            CasePhase, Audiencia, LegalNotification, MovimentacaoFinanceira,
        )
        from apps.core.models import AuditLog

        try:
            caso = LegalCase.objects.select_related(
                'advogado_responsavel', 'client', 'created_by'
            ).get(id=case_id)
        except LegalCase.DoesNotExist:
            return None

        today = timezone.now().date()

        # Info basica
        case_info = {
            'id': str(caso.id),
            'numero_processo': caso.numero_processo,
            'titulo': caso.titulo,
            'especialidade': caso.get_especialidade_display(),
            'status': caso.get_status_display(),
            'fase': caso.get_fase_display(),
            'cliente_nome': caso.cliente_nome,
            'parte_contraria': caso.parte_contraria,
            'tribunal': caso.tribunal,
            'vara_juizo': caso.vara_juizo,
            'comarca': caso.comarca,
            'valor_causa': str(caso.valor_causa or 0),
            'advogado': (
                caso.advogado_responsavel.get_full_name()
                if caso.advogado_responsavel else ''
            ),
            'data_distribuicao': (
                caso.data_distribuicao.isoformat()
                if caso.data_distribuicao else None
            ),
            'data_encerramento': (
                caso.data_encerramento.isoformat()
                if caso.data_encerramento else None
            ),
            'descricao': caso.descricao,
            'created_at': caso.created_at.isoformat(),
        }

        # Fases processuais
        phases = list(
            CasePhase.objects.filter(caso=caso).order_by('order').values(
                'id', 'order', 'name', 'status', 'estimated_date',
                'actual_date', 'notes',
            )
        )
        for p in phases:
            p['id'] = str(p['id'])
            if p['estimated_date']:
                p['estimated_date'] = p['estimated_date'].isoformat()
            if p['actual_date']:
                p['actual_date'] = p['actual_date'].isoformat()

        # Prazos
        deadlines_qs = LegalDeadline.objects.filter(caso=caso).order_by('data_prazo')
        deadlines = []
        for d in deadlines_qs:
            is_overdue = d.status in ('pendente', 'em_andamento') and d.data_prazo < today
            deadlines.append({
                'id': str(d.id),
                'titulo': d.titulo,
                'tipo': d.get_tipo_display(),
                'status': d.get_status_display(),
                'prioridade': d.get_prioridade_display(),
                'data_prazo': d.data_prazo.isoformat(),
                'is_overdue': is_overdue,
            })

        # Documentos
        documents = list(
            CaseDocument.objects.filter(caso=caso).order_by('-created_at').values(
                'id', 'titulo', 'tipo', 'data_documento', 'created_at',
            )
        )
        for doc in documents:
            doc['id'] = str(doc['id'])
            if doc['data_documento']:
                doc['data_documento'] = doc['data_documento'].isoformat()
            doc['created_at'] = doc['created_at'].isoformat()

        # Notificacoes
        notifications = list(
            LegalNotification.objects.filter(caso=caso).order_by('-created_at').values(
                'id', 'tipo', 'direcao', 'status', 'prazo_vencimento', 'created_at',
            )
        )
        for n in notifications:
            n['id'] = str(n['id'])
            if n['prazo_vencimento']:
                n['prazo_vencimento'] = n['prazo_vencimento'].isoformat()
            n['created_at'] = n['created_at'].isoformat()

        # Audiencias
        hearings = list(
            Audiencia.objects.filter(caso=caso).order_by('data_hora').values(
                'id', 'tipo', 'status', 'data_hora', 'local',
            )
        )
        for h in hearings:
            h['id'] = str(h['id'])
            h['data_hora'] = h['data_hora'].isoformat()

        # Atividades recentes
        activities = list(
            AuditLog.objects.filter(entity_id=str(case_id))
            .order_by('-created_at')[:30]
            .values('action', 'description', 'user_email', 'created_at')
        )
        for a in activities:
            a['created_at'] = a['created_at'].isoformat()

        return {
            'report_type': 'case_progress',
            'generated_at': timezone.now().isoformat(),
            'case_info': case_info,
            'phases': phases,
            'deadlines': deadlines,
            'documents': documents,
            'notifications': notifications,
            'hearings': hearings,
            'activities': activities,
        }

    @classmethod
    def generate_portfolio_report(cls, user, filters=None) -> dict:
        """
        Gera relatorio do portfolio de casos do usuario.
        Inclui: distribuicao por status, area, compliance de prazos, etc.
        """
        from apps.cases.models import LegalCase, LegalDeadline, MovimentacaoFinanceira

        filters = filters or {}
        casos_qs = cls._user_cases_qs(user)

        today = timezone.now().date()
        total = casos_qs.count()

        # Casos por status
        by_status_raw = (
            casos_qs.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        by_status = [
            {'status': r['status'], 'count': r['count']}
            for r in by_status_raw
        ]

        # Casos por especialidade
        by_area_raw = (
            casos_qs.values('especialidade')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        by_area = [
            {'area': r['especialidade'], 'count': r['count']}
            for r in by_area_raw
        ]

        # Prazos: compliance rate
        prazos_qs = LegalDeadline.objects.all()
        if not (user.is_staff or user.is_superuser):
            prazos_qs = prazos_qs.filter(
                Q(caso__advogado_responsavel=user) |
                Q(caso__created_by=user) |
                Q(responsavel=user)
            ).distinct()

        total_prazos = prazos_qs.count()
        prazos_concluidos = prazos_qs.filter(status='concluido').count()
        prazos_atrasados = prazos_qs.filter(
            status__in=['pendente', 'em_andamento'],
            data_prazo__lt=today,
        ).count()
        compliance_rate = (
            round((prazos_concluidos / total_prazos) * 100, 1)
            if total_prazos > 0 else 100.0
        )

        # Duracao media dos casos encerrados
        encerrados = casos_qs.filter(
            data_encerramento__isnull=False,
            data_distribuicao__isnull=False,
        )
        if encerrados.exists():
            durations = [
                (c.data_encerramento - c.data_distribuicao).days
                for c in encerrados
            ]
            avg_duration = round(sum(durations) / len(durations))
        else:
            avg_duration = 0

        # Financeiro resumido
        movs = MovimentacaoFinanceira.objects.all()
        if not (user.is_staff or user.is_superuser):
            movs = movs.filter(
                Q(caso__advogado_responsavel=user) | Q(caso__created_by=user)
            )

        receita = movs.filter(
            tipo='honorario', status='pago'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
        despesa = movs.filter(
            tipo__in=['despesa', 'custas', 'pericia'], status='pago'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')

        # Casos novos por mes (ultimos 6 meses)
        monthly_new = []
        for i in range(5, -1, -1):
            month_start = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
            if i > 0:
                next_month = (month_start + timedelta(days=32)).replace(day=1)
            else:
                next_month = (today + timedelta(days=1))
            count = casos_qs.filter(
                created_at__date__gte=month_start,
                created_at__date__lt=next_month,
            ).count()
            monthly_new.append({
                'month': month_start.strftime('%Y-%m'),
                'label': month_start.strftime('%b/%Y'),
                'count': count,
            })

        return {
            'report_type': 'portfolio',
            'generated_at': timezone.now().isoformat(),
            'total_cases': total,
            'by_status': by_status,
            'by_area': by_area,
            'deadline_compliance': {
                'total': total_prazos,
                'completed': prazos_concluidos,
                'overdue': prazos_atrasados,
                'rate': compliance_rate,
            },
            'avg_duration_days': avg_duration,
            'financial': {
                'receita': str(receita),
                'despesa': str(despesa),
                'saldo': str(receita - despesa),
            },
            'monthly_new_cases': monthly_new,
        }

    @classmethod
    def get_kpi_metrics(cls, user) -> dict:
        """Retorna KPIs do usuario."""
        from apps.cases.models import LegalCase, LegalDeadline

        casos_qs = cls._user_cases_qs(user)
        today = timezone.now().date()
        month_start = today.replace(day=1)

        total_ativos = casos_qs.filter(status='ativo').count()
        novos_mes = casos_qs.filter(created_at__date__gte=month_start).count()

        # Ganhos vs perdidos
        ganhos = casos_qs.filter(status='ganho').count()
        perdidos = casos_qs.filter(status='perdido').count()
        acordos = casos_qs.filter(status='acordo').count()

        # Deadline compliance
        prazos_qs = LegalDeadline.objects.all()
        if not (user.is_staff or user.is_superuser):
            prazos_qs = prazos_qs.filter(
                Q(caso__advogado_responsavel=user) |
                Q(caso__created_by=user) |
                Q(responsavel=user)
            ).distinct()

        total_prazos = prazos_qs.count()
        prazos_concluidos = prazos_qs.filter(status='concluido').count()
        prazos_pendentes = prazos_qs.filter(status='pendente').count()
        prazos_atrasados = prazos_qs.filter(
            status__in=['pendente', 'em_andamento'],
            data_prazo__lt=today,
        ).count()
        compliance = (
            round((prazos_concluidos / total_prazos) * 100, 1)
            if total_prazos > 0 else 100.0
        )

        # Duracao media
        encerrados = casos_qs.filter(
            data_encerramento__isnull=False,
            data_distribuicao__isnull=False,
        )
        if encerrados.exists():
            durations = [
                (c.data_encerramento - c.data_distribuicao).days
                for c in encerrados
            ]
            avg_resolution = round(sum(durations) / len(durations))
        else:
            avg_resolution = 0

        return {
            'active_cases': total_ativos,
            'new_cases_month': novos_mes,
            'cases_won': ganhos,
            'cases_lost': perdidos,
            'cases_settled': acordos,
            'avg_resolution_days': avg_resolution,
            'deadline_compliance_pct': compliance,
            'deadlines_pending': prazos_pendentes,
            'deadlines_overdue': prazos_atrasados,
            'deadlines_completed': prazos_concluidos,
            'total_deadlines': total_prazos,
        }

    @classmethod
    def generate_report_pdf(cls, report_data: dict, report_type: str) -> bytes:
        """
        Gera PDF a partir dos dados do relatorio usando WeasyPrint.
        Retorna bytes do PDF.
        """
        try:
            from weasyprint import HTML
        except ImportError:
            logger.warning("WeasyPrint nao instalado. Retornando PDF vazio.")
            return cls._generate_simple_pdf(report_data, report_type)

        html_content = cls._render_report_html(report_data, report_type)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes

    @classmethod
    def _generate_simple_pdf(cls, report_data, report_type):
        """Fallback: gera PDF simples sem WeasyPrint."""
        import json
        content = json.dumps(report_data, indent=2, ensure_ascii=False, default=str)
        # Retorna texto simples como fallback
        return content.encode('utf-8')

    @classmethod
    def _render_report_html(cls, report_data, report_type):
        """Renderiza HTML para geracao de PDF."""
        if report_type == 'case_progress':
            return cls._render_case_progress_html(report_data)
        return cls._render_portfolio_html(report_data)

    @classmethod
    def _render_case_progress_html(cls, data):
        ci = data.get('case_info', {})
        phases = data.get('phases', [])
        deadlines = data.get('deadlines', [])

        phases_html = ''
        for p in phases:
            status_color = '#10b981' if p['status'] == 'completed' else '#f59e0b' if p['status'] == 'in_progress' else '#6b7280'
            phases_html += f'<tr><td>{p["order"]}</td><td>{p["name"]}</td><td style="color:{status_color}">{p["status"]}</td><td>{p.get("estimated_date","")}</td></tr>'

        deadlines_html = ''
        for d in deadlines:
            row_style = 'color:#ef4444;font-weight:bold' if d.get('is_overdue') else ''
            deadlines_html += f'<tr style="{row_style}"><td>{d["titulo"]}</td><td>{d["tipo"]}</td><td>{d["status"]}</td><td>{d["data_prazo"]}</td></tr>'

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; font-size: 12px; }}
h1 {{ color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 8px; }}
h2 {{ color: #374151; margin-top: 24px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; text-align: left; }}
th {{ background: #f3f4f6; font-weight: bold; }}
.info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.info-item {{ margin: 4px 0; }}
.label {{ color: #6b7280; font-size: 11px; }}
</style></head>
<body>
<h1>Relatorio de Andamento Processual</h1>
<div class="info-grid">
<div class="info-item"><span class="label">Processo:</span> {ci.get('numero_processo','')}</div>
<div class="info-item"><span class="label">Titulo:</span> {ci.get('titulo','')}</div>
<div class="info-item"><span class="label">Cliente:</span> {ci.get('cliente_nome','')}</div>
<div class="info-item"><span class="label">Parte Contraria:</span> {ci.get('parte_contraria','')}</div>
<div class="info-item"><span class="label">Tribunal:</span> {ci.get('tribunal','')}</div>
<div class="info-item"><span class="label">Status:</span> {ci.get('status','')}</div>
<div class="info-item"><span class="label">Especialidade:</span> {ci.get('especialidade','')}</div>
<div class="info-item"><span class="label">Valor:</span> R$ {ci.get('valor_causa','0')}</div>
</div>

<h2>Fases Processuais</h2>
<table><tr><th>#</th><th>Fase</th><th>Status</th><th>Data Estimada</th></tr>
{phases_html}</table>

<h2>Prazos</h2>
<table><tr><th>Titulo</th><th>Tipo</th><th>Status</th><th>Data</th></tr>
{deadlines_html}</table>

<p style="color:#9ca3af;font-size:10px;margin-top:32px;">Gerado em: {data.get('generated_at','')}</p>
</body></html>"""

    @classmethod
    def _render_portfolio_html(cls, data):
        by_status = data.get('by_status', [])
        by_area = data.get('by_area', [])
        compliance = data.get('deadline_compliance', {})
        financial = data.get('financial', {})

        status_html = ''.join(f'<tr><td>{s["status"]}</td><td>{s["count"]}</td></tr>' for s in by_status)
        area_html = ''.join(f'<tr><td>{a["area"]}</td><td>{a["count"]}</td></tr>' for a in by_area)

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; font-size: 12px; }}
h1 {{ color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 8px; }}
h2 {{ color: #374151; margin-top: 24px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; text-align: left; }}
th {{ background: #f3f4f6; }}
.kpi {{ display: inline-block; margin: 8px 16px 8px 0; padding: 12px; background: #f3f4f6; border-radius: 8px; }}
.kpi-value {{ font-size: 24px; font-weight: bold; color: #1e40af; }}
.kpi-label {{ font-size: 11px; color: #6b7280; }}
</style></head>
<body>
<h1>Relatorio de Portfolio</h1>

<div>
<div class="kpi"><div class="kpi-value">{data.get('total_cases',0)}</div><div class="kpi-label">Total de Casos</div></div>
<div class="kpi"><div class="kpi-value">{compliance.get('rate',0)}%</div><div class="kpi-label">Compliance de Prazos</div></div>
<div class="kpi"><div class="kpi-value">{data.get('avg_duration_days',0)} dias</div><div class="kpi-label">Duracao Media</div></div>
</div>

<h2>Casos por Status</h2>
<table><tr><th>Status</th><th>Quantidade</th></tr>{status_html}</table>

<h2>Casos por Area</h2>
<table><tr><th>Area</th><th>Quantidade</th></tr>{area_html}</table>

<h2>Financeiro</h2>
<table>
<tr><th>Receita</th><td>R$ {financial.get('receita','0')}</td></tr>
<tr><th>Despesa</th><td>R$ {financial.get('despesa','0')}</td></tr>
<tr><th>Saldo</th><td>R$ {financial.get('saldo','0')}</td></tr>
</table>

<p style="color:#9ca3af;font-size:10px;margin-top:32px;">Gerado em: {data.get('generated_at','')}</p>
</body></html>"""
