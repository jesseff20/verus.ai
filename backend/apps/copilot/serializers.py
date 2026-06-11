from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    message = serializers.CharField(max_length=10_000)


class ExportRequestSerializer(serializers.Serializer):
    FORMAT_CHOICES = ['docx', 'pdf', 'odt']

    text = serializers.CharField()
    format = serializers.ChoiceField(choices=FORMAT_CHOICES)
    title = serializers.CharField(max_length=255, default='Resposta Copilot')
