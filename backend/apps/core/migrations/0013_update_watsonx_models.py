# Data migration: atualiza modelos watsonx para os disponíveis no projeto IBM Cloud
# Modelos antigos foram descontinuados pela IBM, novos incluem Llama 4, Granite 4, etc.

from django.db import migrations


def update_watsonx_models(apps, schema_editor):
    LLMProvider = apps.get_model('core', 'LLMProvider')
    LLMModel = apps.get_model('core', 'LLMModel')

    watsonx = LLMProvider.objects.filter(code='watsonx').first()
    if not watsonx:
        return

    # ── Remover modelos descontinuados ──
    deprecated_models = [
        'ibm/granite-13b-chat-v2',
        'meta-llama/llama-3-1-70b-instruct',
        'meta-llama/llama-3-1-8b-instruct',
        'mistralai/mixtral-8x7b-instruct-v01',
    ]
    LLMModel.objects.filter(
        provider=watsonx,
        model_id__in=deprecated_models,
    ).delete()

    # ── Novos modelos disponíveis (geração de texto) ──
    new_models = [
        # (model_id, display_name, max_tokens, temperature, order)
        ('meta-llama/llama-3-3-70b-instruct', 'Llama 3.3 70B Instruct', 4096, 0.7, 0),
        ('meta-llama/llama-4-maverick-17b-128e-instruct-fp8', 'Llama 4 Maverick 17B', 4096, 0.7, 1),
        ('meta-llama/llama-3-405b-instruct', 'Llama 3 405B Instruct', 4096, 0.7, 2),
        ('ibm/granite-4-h-small', 'Granite 4 H Small', 4096, 0.7, 3),
        ('ibm/granite-3-3-8b-instruct', 'Granite 3.3 8B Instruct', 4096, 0.7, 4),
        ('mistralai/mistral-medium-2505', 'Mistral Medium', 4096, 0.7, 5),
        ('mistralai/mistral-small-3-1-24b-instruct-2503', 'Mistral Small 3.1 24B', 4096, 0.7, 6),
        ('openai/gpt-oss-120b', 'GPT OSS 120B', 4096, 0.7, 7),
    ]

    # ── Modelos de embedding (para futuro uso com RAG) ──
    embedding_models = [
        ('ibm/granite-embedding-278m-multilingual', 'Granite Embedding Multilingual', 512, 0.0, 10),
        ('intfloat/multilingual-e5-large', 'E5 Large Multilingual', 512, 0.0, 11),
    ]

    all_models = new_models + embedding_models

    for model_id, name, max_tokens, temp, order in all_models:
        LLMModel.objects.update_or_create(
            provider=watsonx,
            model_id=model_id,
            defaults={
                'display_name': name,
                'max_tokens_limit': max_tokens,
                'default_temperature': temp,
                'display_order': order,
                'is_active': True,
            },
        )

    # ── Atualizar order do granite-3-8b-instruct (já existia) ──
    LLMModel.objects.filter(
        provider=watsonx,
        model_id='ibm/granite-3-8b-instruct',
    ).update(display_order=5)


def reverse_update(apps, schema_editor):
    LLMModel = apps.get_model('core', 'LLMModel')
    LLMProvider = apps.get_model('core', 'LLMProvider')

    watsonx = LLMProvider.objects.filter(code='watsonx').first()
    if not watsonx:
        return

    # Remover novos modelos adicionados
    new_model_ids = [
        'meta-llama/llama-3-3-70b-instruct',
        'meta-llama/llama-4-maverick-17b-128e-instruct-fp8',
        'meta-llama/llama-3-405b-instruct',
        'ibm/granite-4-h-small',
        'ibm/granite-3-3-8b-instruct',
        'mistralai/mistral-medium-2505',
        'mistralai/mistral-small-3-1-24b-instruct-2503',
        'openai/gpt-oss-120b',
        'ibm/granite-embedding-278m-multilingual',
        'intfloat/multilingual-e5-large',
    ]
    LLMModel.objects.filter(
        provider=watsonx,
        model_id__in=new_model_ids,
    ).delete()

    # Recriar modelos antigos
    old_models = [
        ('ibm/granite-13b-chat-v2', 'Granite 13B Chat v2', 4096, 0.7, 0),
        ('meta-llama/llama-3-1-70b-instruct', 'Llama 3.1 70B Instruct', 4096, 0.7, 2),
        ('meta-llama/llama-3-1-8b-instruct', 'Llama 3.1 8B Instruct', 4096, 0.7, 3),
        ('mistralai/mixtral-8x7b-instruct-v01', 'Mixtral 8x7B Instruct', 4096, 0.7, 4),
    ]
    for model_id, name, max_tokens, temp, order in old_models:
        LLMModel.objects.create(
            provider=watsonx,
            model_id=model_id,
            display_name=name,
            max_tokens_limit=max_tokens,
            default_temperature=temp,
            display_order=order,
            is_active=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_populate_llm_providers"),
    ]

    operations = [
        migrations.RunPython(update_watsonx_models, reverse_update),
    ]
