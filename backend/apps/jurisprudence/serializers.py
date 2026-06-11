"""
Serializers de Jurisprudência — Radar de Precedentes.

Serializers:
  - JurisprudenceSearchSerializer
  - JurisprudenceResultSerializer
  - RadarReportSerializer
  - TribunalStatisticsSerializer
  - ThesisStatisticsSerializer
"""
from rest_framework import serializers

from .models import JurisprudenceSearch, JurisprudenceResult


# ---------------------------------------------------------------------------
# Model serializers
# ---------------------------------------------------------------------------

class JurisprudenceSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = JurisprudenceSearch
        fields = [
            'id', 'query', 'specialty', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class JurisprudenceResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = JurisprudenceResult
        fields = [
            'id', 'search', 'tribunal', 'case_number',
            'relator', 'organ', 'summary', 'full_text_url',
            'relevance_score', 'judgment_date',
            'source', 'content', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ---------------------------------------------------------------------------
# Radar Report serializers (for dataclass objects returned by service)
# ---------------------------------------------------------------------------

class PrecedentAnalysisSerializer(serializers.Serializer):
    """Serializer para PrecedentAnalysis dataclass."""
    id = serializers.CharField()
    tribunal = serializers.CharField()
    case_number = serializers.CharField()
    outcome = serializers.CharField()
    weight = serializers.CharField()
    relevance_score = serializers.FloatField()
    summary = serializers.CharField()
    judgment_date = serializers.DateTimeField(allow_null=True)
    relator = serializers.CharField(allow_null=True)
    organ = serializers.CharField(allow_null=True)
    keywords = serializers.ListField(child=serializers.CharField())
    citation = serializers.CharField()


class TribunalStatisticsSerializer(serializers.Serializer):
    """Serializer para TribunalStatistics dataclass."""
    tribunal = serializers.CharField()
    total_cases = serializers.IntegerField()
    favorable_count = serializers.IntegerField()
    unfavorable_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_judgment_time_days = serializers.FloatField(allow_null=True)
    recent_trend = serializers.CharField()


class ThesisStatisticsSerializer(serializers.Serializer):
    """Serializer para ThesisStatistics dataclass."""
    thesis = serializers.CharField()
    total_cases = serializers.IntegerField()
    favorable_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    tribunals = serializers.DictField(child=serializers.IntegerField())
    recent_judgments = PrecedentAnalysisSerializer(many=True)


class RadarReportSerializer(serializers.Serializer):
    """Serializer para RadarReport dataclass."""
    query = serializers.CharField()
    total_analyzed = serializers.IntegerField()
    overall_success_rate = serializers.FloatField()
    tribunal_stats = TribunalStatisticsSerializer(many=True)
    thesis_stats = ThesisStatisticsSerializer(many=True)
    timeline = serializers.ListField(child=serializers.DictField())
    key_precedents = PrecedentAnalysisSerializer(many=True)
    recommendations = serializers.ListField(child=serializers.CharField())
    generated_at = serializers.DateTimeField()
