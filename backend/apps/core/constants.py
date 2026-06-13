"""
Constantes centralizadas — Single Source of Truth (SSoT)
Todas as definições de choices que são compartilhadas entre múltiplos models
devem ser definidas aqui para evitar duplicação.
"""

LLM_PROVIDER_CHOICES = [
    ('openai', 'OpenAI'),
    ('watsonx', 'IBM WatsonX'),
    ('anthropic', 'Anthropic (legado)'),
]

DEFAULT_LLM_PROVIDER = 'watsonx'
DEFAULT_LLM_MODEL = 'mistralai/mistral-medium-2505'
