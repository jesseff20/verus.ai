from django.contrib import admin
from .models import (
    Simulation, SimulationDocument, JuryMember,
    JuryDebateMessage, JudgeProfile, Court,
    MinisterProfile, CourtVote,
)


class SimulationDocumentInline(admin.TabularInline):
    model = SimulationDocument
    extra = 0
    readonly_fields = ['id', 'uploaded_at']


class JuryMemberInline(admin.TabularInline):
    model = JuryMember
    extra = 0
    readonly_fields = ['id']


@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ['title', 'simulation_type', 'user', 'status', 'created_at']
    list_filter = ['simulation_type', 'status', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [SimulationDocumentInline, JuryMemberInline]


@admin.register(SimulationDocument)
class SimulationDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'simulation', 'document_type', 'uploaded_at']
    list_filter = ['document_type']
    search_fields = ['title']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(JuryMember)
class JuryMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'simulation', 'profession', 'education', 'vote']
    list_filter = ['vote', 'education', 'gender']
    search_fields = ['name', 'profession']
    readonly_fields = ['id']


@admin.register(JuryDebateMessage)
class JuryDebateMessageAdmin(admin.ModelAdmin):
    list_display = ['simulation', 'role', 'phase', 'created_at']
    list_filter = ['role', 'phase']
    readonly_fields = ['id', 'created_at']


@admin.register(JudgeProfile)
class JudgeProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'court', 'comarca', 'state', 'specialization', 'is_active']
    list_filter = ['state', 'court', 'is_active']
    search_fields = ['name', 'comarca']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ['name', 'court_type', 'state', 'is_active']
    list_filter = ['court_type', 'state', 'is_active']
    search_fields = ['name']
    readonly_fields = ['id']


@admin.register(MinisterProfile)
class MinisterProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'court_type', 'turma', 'judicial_philosophy', 'is_active']
    list_filter = ['court_type', 'turma', 'judicial_philosophy', 'is_active']
    search_fields = ['name', 'full_name']
    readonly_fields = ['id', 'created_at']


@admin.register(CourtVote)
class CourtVoteAdmin(admin.ModelAdmin):
    list_display = ['voter_name', 'simulation', 'vote', 'is_relator', 'is_dissent', 'created_at']
    list_filter = ['vote', 'is_relator', 'is_dissent']
    search_fields = ['voter_name']
    readonly_fields = ['id', 'created_at']
