"""
Simulations — Simulação de Júri e Simulação de Sentença do Juiz.

Permite simular julgamentos com júri popular (deliberação, quesitos, veredicto)
e prever sentenças com base no perfil de juízes reais.
"""
from django.db import models
from django.conf import settings
import uuid


class Simulation(models.Model):
    """Base para todas as simulações"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    SIMULATION_TYPES = [
        ('jury', 'Simulação de Júri'),
        ('judge', 'Simulação de Sentença'),
        ('stf', 'Simulação STF'),
        ('acordao_2inst', 'Acórdão 2a Instância'),
        ('stj', 'Simulação STJ'),
        ('jec', 'Juizado Especial Cível'),
        ('jecrim', 'Juizado Especial Criminal'),
        ('jef', 'Juizado Especial Federal'),
        ('turma_recursal', 'Turma Recursal'),
        ('trabalho', 'Vara do Trabalho'),
        ('trt', 'TRT'),
        ('tst', 'TST'),
        ('eleitoral', 'Justiça Eleitoral'),
        ('tre', 'TRE'),
        ('tse', 'TSE'),
        ('militar', 'Justiça Militar'),
        ('stm', 'STM'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey(
        'cases.LegalCase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='simulations',
        verbose_name='Caso Jurídico',
        help_text='Caso jurídico associado a esta simulação',
    )
    simulation_type = models.CharField(max_length=30, choices=SIMULATION_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Rascunho'),
        ('configuring', 'Configurando'),
        ('running', 'Em Execução'),
        ('deliberating', 'Deliberando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ], default='draft')
    config = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    is_deleted = models.BooleanField(default=False, help_text='Soft delete flag')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Simulação'
        verbose_name_plural = 'Simulações'

    def __str__(self):
        return f'{self.get_simulation_type_display()}: {self.title}'


class SimulationDocument(models.Model):
    """Documentos anexados à simulação (peças do processo)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='simulations/documents/')
    extracted_text = models.TextField(blank=True)
    document_type = models.CharField(max_length=50, choices=[
        ('denuncia', 'Denúncia'),
        ('defesa', 'Defesa/Contestação'),
        ('prova', 'Prova Documental'),
        ('pericia', 'Laudo Pericial'),
        ('testemunho', 'Depoimento/Testemunho'),
        ('sentenca', 'Sentença de 1ª Instância'),
        ('recurso', 'Recurso'),
        ('outros', 'Outros'),
    ], default='outros')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento da Simulação'
        verbose_name_plural = 'Documentos da Simulação'

    def __str__(self):
        return f'{self.title} ({self.get_document_type_display()})'


class JuryMember(models.Model):
    """Membro do júri simulado"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name='jury_members')
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=20, choices=[
        ('masculino', 'Masculino'),
        ('feminino', 'Feminino'),
        ('outro', 'Outro'),
    ])
    profession = models.CharField(max_length=100)
    education = models.CharField(max_length=50, choices=[
        ('fundamental', 'Ensino Fundamental'),
        ('medio', 'Ensino Médio'),
        ('superior', 'Ensino Superior'),
        ('pos_graduacao', 'Pós-Graduação'),
    ])
    personality_traits = models.JSONField(default=list)
    background = models.TextField(blank=True)
    vote = models.CharField(max_length=20, blank=True, choices=[
        ('absolvicao', 'Absolvição'),
        ('condenacao', 'Condenação'),
        ('desclassificacao', 'Desclassificação'),
        ('pendente', 'Pendente'),
    ], default='pendente')
    reasoning = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Jurado'
        verbose_name_plural = 'Jurados'

    def __str__(self):
        return f'{self.name} - {self.profession}'


class JuryDebateMessage(models.Model):
    """Mensagem no debate do júri"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name='debate_messages')
    jury_member = models.ForeignKey(JuryMember, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=[
        ('jurado', 'Jurado'),
        ('promotor', 'Promotor'),
        ('defensor', 'Defensor'),
        ('juiz', 'Juiz Presidente'),
        ('sistema', 'Sistema'),
    ])
    content = models.TextField()
    phase = models.CharField(max_length=30, choices=[
        ('abertura', 'Abertura'),
        ('acusacao', 'Sustentação da Acusação'),
        ('defesa', 'Sustentação da Defesa'),
        ('replicas', 'Réplicas'),
        ('treplicas', 'Tréplicas'),
        ('deliberacao', 'Deliberação do Conselho'),
        ('quesitos', 'Votação dos Quesitos'),
        ('veredicto', 'Veredicto'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensagem de Debate'
        verbose_name_plural = 'Mensagens de Debate'

    def __str__(self):
        return f'[{self.get_phase_display()}] {self.get_role_display()}: {self.content[:50]}'


class JudgeProfile(models.Model):
    """Perfil de juiz para simulação de sentença"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    state = models.CharField(max_length=2)
    court = models.CharField(max_length=200)
    comarca = models.CharField(max_length=200)
    vara = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    profile_data = models.JSONField(default=dict)
    decision_patterns = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['state', 'comarca', 'name']
        unique_together = ['name', 'court', 'comarca']
        verbose_name = 'Perfil de Juiz'
        verbose_name_plural = 'Perfis de Juízes'

    def __str__(self):
        return f'{self.name} - {self.court} ({self.comarca})'


class Court(models.Model):
    """Tribunal/Comarca cadastrado"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    COURT_TYPES = [
        ('STF', 'Supremo Tribunal Federal'),
        ('STJ', 'Superior Tribunal de Justiça'),
        ('TST', 'Tribunal Superior do Trabalho'),
        ('TJ', 'Tribunal de Justiça'),
        ('TRF', 'Tribunal Regional Federal'),
        ('TRT', 'Tribunal Regional do Trabalho'),
        ('JF', 'Justiça Federal'),
        ('JE', 'Justiça Estadual'),
    ]
    name = models.CharField(max_length=200)
    court_type = models.CharField(max_length=5, choices=COURT_TYPES)
    state = models.CharField(max_length=2)
    comarcas = models.JSONField(default=list)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['state', 'name']
        verbose_name = 'Tribunal'
        verbose_name_plural = 'Tribunais'

    def __str__(self):
        return f'{self.name} ({self.state})'


class MinisterProfile(models.Model):
    """Perfil de ministro do STF/STJ para simulação de julgamento colegiado."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    court_type = models.CharField(max_length=10, choices=[('STF', 'STF'), ('STJ', 'STJ'), ('TJ', 'TJ/TRF'), ('TRT', 'TRT'), ('TST', 'TST'), ('TSE', 'TSE'), ('STM', 'STM'), ('TRE', 'TRE')])
    name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=300, blank=True)
    appointed_by = models.CharField(max_length=100, blank=True)
    appointment_date = models.DateField(null=True, blank=True)
    turma = models.CharField(max_length=50, blank=True)
    judicial_philosophy = models.CharField(
        max_length=20,
        choices=[
            ('progressista', 'Progressista'),
            ('conservador', 'Conservador'),
            ('centrista', 'Centrista'),
            ('pragmatico', 'Pragmático'),
        ],
        default='centrista',
    )
    specialty_areas = models.JSONField(default=list, blank=True)
    notable_positions = models.JSONField(default=list, blank=True)
    profile_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['court_type', 'turma', 'name']
        verbose_name = 'Perfil de Ministro'
        verbose_name_plural = 'Perfis de Ministros'

    def __str__(self):
        return f"Min. {self.name} ({self.court_type})"


class CourtVote(models.Model):
    """Voto individual de ministro em simulação colegiada (STF/STJ)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name='court_votes')
    voter_name = models.CharField(max_length=200)
    voter_role = models.CharField(max_length=20, default='ministro')
    minister_profile = models.ForeignKey(MinisterProfile, on_delete=models.SET_NULL, null=True, blank=True)
    vote = models.CharField(max_length=30)
    vote_text = models.TextField(blank=True)
    is_relator = models.BooleanField(default=False)
    is_dissent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Voto de Ministro'
        verbose_name_plural = 'Votos de Ministros'

    def __str__(self):
        return f"{self.voter_name}: {self.vote} ({self.simulation})"
