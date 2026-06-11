from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Organ, Unit
from .serializers import OrganSerializer, UnitSerializer, OrganMinimalSerializer


class OrganViewSet(viewsets.ModelViewSet):
    """CRUD de órgãos. Apenas superadmin pode criar/deletar."""
    queryset = Organ.objects.filter(is_active=True).prefetch_related('units')
    serializer_class = OrganSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def units(self, request, pk=None):
        organ = self.get_object()
        units = organ.units.filter(is_active=True)
        return Response(UnitSerializer(units, many=True).data)


class UnitViewSet(viewsets.ModelViewSet):
    """CRUD de unidades. Filtrado pelo órgão do usuário logado."""
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Unit.objects.filter(is_active=True)
        # Superadmin vê tudo; demais veem apenas seu órgão
        if not user.is_staff and hasattr(user, 'organ') and user.organ:
            qs = qs.filter(organ=user.organ)
        organ_id = self.request.query_params.get('organ')
        if organ_id:
            qs = qs.filter(organ_id=organ_id)
        return qs
