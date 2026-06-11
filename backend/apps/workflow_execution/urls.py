from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import (
    FlowInstanceViewSet, TaskInstanceViewSet,
    MyTasksViewSet, TaskRequestAdminViewSet,
    flow_analytics, suggest_flow,
)

router = SimpleRouter()
router.register(r'executions', FlowInstanceViewSet, basename='flow-instance')
router.register(r'my-tasks', MyTasksViewSet, basename='my-tasks')
router.register(r'task-requests', TaskRequestAdminViewSet, basename='task-requests')

# Rotas nested para tasks dentro de uma instância
task_list = TaskInstanceViewSet.as_view({'get': 'list'})
task_detail = TaskInstanceViewSet.as_view({'get': 'retrieve'})
task_complete = TaskInstanceViewSet.as_view({'post': 'complete'})
task_request = TaskInstanceViewSet.as_view({'post': 'create_request'})

urlpatterns = [
    path('', include(router.urls)),
    # Fase 5 — Analytics e sugestão de IA
    path('analytics/', flow_analytics, name='flow-analytics'),
    path('suggest-flow/', suggest_flow, name='suggest-flow'),
    path(
        'executions/<str:instance_pk>/tasks/',
        task_list,
        name='instance-tasks-list',
    ),
    path(
        'executions/<str:instance_pk>/tasks/<pk>/',
        task_detail,
        name='instance-tasks-detail',
    ),
    path(
        'executions/<str:instance_pk>/tasks/<pk>/complete/',
        task_complete,
        name='instance-tasks-complete',
    ),
    path(
        'executions/<str:instance_pk>/tasks/<pk>/request/',
        task_request,
        name='instance-tasks-request',
    ),
]
