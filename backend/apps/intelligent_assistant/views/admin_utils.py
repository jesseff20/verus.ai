"""Admin utility views for data maintenance."""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fix_etp_references_api(request):
    """Fix ETP references in database. Admin only."""
    if not (request.user.is_staff or request.user.is_superuser or
            getattr(request.user, 'role', '') in ('superadmin', 'admin')):
        return Response({'error': 'Acesso negado'}, status=403)

    from ..models import GeneratedDocument, IntelligentSession
    from apps.cases.models import CaseDocument

    results = {'updated': [], 'errors': []}

    # Fix GeneratedDocument titles
    for doc in GeneratedDocument.objects.filter(title__startswith='ETP'):
        old = doc.title
        doc.title = doc.title.replace('ETP - ', '').replace('ETP ', '')
        if old != doc.title:
            doc.save(update_fields=['title'])
            results['updated'].append({'type': 'GeneratedDocument', 'id': str(doc.id), 'old': old[:60], 'new': doc.title[:60]})

    # Fix IntelligentSession objectives
    for sess in IntelligentSession.objects.filter(objective__startswith='ETP'):
        old = sess.objective
        sess.objective = sess.objective.replace('ETP - ', '').replace('ETP ', '')
        if old != sess.objective:
            sess.save(update_fields=['objective'])
            results['updated'].append({'type': 'IntelligentSession', 'id': str(sess.id), 'old': old[:60], 'new': sess.objective[:60]})

    # Fix CaseDocument titles
    for cd in CaseDocument.objects.filter(titulo__startswith='ETP'):
        old = cd.titulo
        cd.titulo = cd.titulo.replace('ETP - ', '').replace('ETP ', '')
        if old != cd.titulo:
            cd.save(update_fields=['titulo'])
            results['updated'].append({'type': 'CaseDocument', 'id': str(cd.id), 'old': old[:60], 'new': cd.titulo[:60]})

    # Also fix "Estudo Técnico Preliminar" standalone (should have the context)
    for doc in GeneratedDocument.objects.filter(title='Estudo Técnico Preliminar'):
        if doc.session and doc.session.objective:
            doc.title = doc.session.objective[:200]
            doc.save(update_fields=['title'])
            results['updated'].append({'type': 'GeneratedDocument', 'id': str(doc.id), 'old': 'Estudo Técnico Preliminar', 'new': doc.title[:60]})

    results['total_updated'] = len(results['updated'])
    logger.info(f"fix_etp_references: {results['total_updated']} records updated")
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fix_pmjp_references_api(request):
    """Remove all PMJP references from production database. Admin only."""
    if not (request.user.is_staff or request.user.is_superuser or
            getattr(request.user, 'role', '') in ('superadmin', 'admin')):
        return Response({'error': 'Acesso negado'}, status=403)

    from ..models import DocumentBlueprint, GeneratedDocument, IntelligentSession
    from ..models.blueprint import BlueprintSection

    results = {'updated': [], 'errors': []}

    # 1. Rename blueprints with "PMJP" in the name
    for bp in DocumentBlueprint.objects.filter(name__icontains='PMJP'):
        old_name = bp.name
        bp.name = bp.name.replace('PMJP', '').replace('  ', ' ').strip(' -')
        if old_name != bp.name:
            bp.save(update_fields=['name'])
            results['updated'].append({
                'type': 'DocumentBlueprint.name',
                'id': str(bp.id),
                'old': old_name[:60],
                'new': bp.name[:60],
            })

    # 2. Clean organization_name fields with PMJP references
    for bp in DocumentBlueprint.objects.filter(organization_name__icontains='PMJP'):
        old = bp.organization_name
        bp.organization_name = bp.organization_name.replace('PMJP', '').strip()
        bp.save(update_fields=['organization_name'])
        results['updated'].append({
            'type': 'DocumentBlueprint.organization_name',
            'id': str(bp.id),
            'old': old[:60],
            'new': bp.organization_name[:60],
        })

    # 3. Clean organization_acronym with PMJP
    for bp in DocumentBlueprint.objects.filter(organization_acronym='PMJP'):
        bp.organization_acronym = ''
        bp.save(update_fields=['organization_acronym'])
        results['updated'].append({
            'type': 'DocumentBlueprint.organization_acronym',
            'id': str(bp.id),
            'old': 'PMJP',
            'new': '',
        })

    # 4. Clean organization_name with "João Pessoa" or "Prefeitura Municipal de João Pessoa"
    for bp in DocumentBlueprint.objects.filter(organization_name__icontains='João Pessoa'):
        old = bp.organization_name
        bp.organization_name = ''
        bp.save(update_fields=['organization_name'])
        results['updated'].append({
            'type': 'DocumentBlueprint.organization_name',
            'id': str(bp.id),
            'old': old[:60],
            'new': '',
        })

    # 5. Clean blueprint descriptions with PMJP
    for bp in DocumentBlueprint.objects.filter(description__icontains='PMJP'):
        old = bp.description
        bp.description = bp.description.replace('PMJP', '').replace('  ', ' ').strip()
        bp.save(update_fields=['description'])
        results['updated'].append({
            'type': 'DocumentBlueprint.description',
            'id': str(bp.id),
            'old': old[:60],
            'new': bp.description[:60],
        })

    # 6. Clean section agent prompts with PMJP
    try:
        from ..models.blueprint import SectionAgentConfig
        for agent in SectionAgentConfig.objects.filter(system_prompt__icontains='PMJP'):
            old = agent.system_prompt[:60]
            agent.system_prompt = agent.system_prompt.replace(
                'PMJP', ''
            ).replace(
                'Prefeitura Municipal de João Pessoa', 'órgão contratante'
            ).replace(
                'João Pessoa', ''
            ).replace('  ', ' ')
            agent.save(update_fields=['system_prompt'])
            results['updated'].append({
                'type': 'SectionAgentConfig.system_prompt',
                'id': str(agent.id),
                'old': old,
                'new': agent.system_prompt[:60],
            })
    except Exception as e:
        results['errors'].append(f'SectionAgentConfig: {str(e)}')

    # 7. Clean generated document titles with PMJP
    for doc in GeneratedDocument.objects.filter(title__icontains='PMJP'):
        old = doc.title
        doc.title = doc.title.replace('PMJP', '').replace('  ', ' ').strip(' -')
        doc.save(update_fields=['title'])
        results['updated'].append({
            'type': 'GeneratedDocument.title',
            'id': str(doc.id),
            'old': old[:60],
            'new': doc.title[:60],
        })

    # 8. Clean intelligent sessions with PMJP in objective
    for sess in IntelligentSession.objects.filter(objective__icontains='PMJP'):
        old = sess.objective
        sess.objective = sess.objective.replace('PMJP', '').replace('  ', ' ').strip(' -')
        sess.save(update_fields=['objective'])
        results['updated'].append({
            'type': 'IntelligentSession.objective',
            'id': str(sess.id),
            'old': old[:60],
            'new': sess.objective[:60],
        })

    # 9. Clean blueprint legal_basis with PMJP
    for bp in DocumentBlueprint.objects.filter(legal_basis__icontains='PMJP'):
        old = bp.legal_basis
        bp.legal_basis = bp.legal_basis.replace('PMJP', '').replace('  ', ' ').strip()
        bp.save(update_fields=['legal_basis'])
        results['updated'].append({
            'type': 'DocumentBlueprint.legal_basis',
            'id': str(bp.id),
            'old': old[:60],
            'new': bp.legal_basis[:60],
        })

    results['total_updated'] = len(results['updated'])
    results['total_errors'] = len(results['errors'])
    logger.info(f"fix_pmjp_references: {results['total_updated']} records updated, {results['total_errors']} errors")
    return Response(results)
