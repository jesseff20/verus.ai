"""
Data migration: copia dados do app kb (Document + DocumentChunk) para o sistema unificado
(KnowledgeBase global + KBSourceFile + KnowledgeBaseEmbedding).

Os vetores de embedding são copiados diretamente (mesmo modelo: text-embedding-3-small, 1536d).
"""
import uuid
from django.db import migrations


def migrate_kb_data(apps, schema_editor):
    """Migra kb.Document → KBSourceFile + KnowledgeBaseEmbedding"""
    Document = apps.get_model('kb', 'Document')
    DocumentChunk = apps.get_model('kb', 'DocumentChunk')
    KnowledgeBase = apps.get_model('intelligent_assistant', 'KnowledgeBase')
    KnowledgeBaseEmbedding = apps.get_model('intelligent_assistant', 'KnowledgeBaseEmbedding')
    KBSourceFile = apps.get_model('intelligent_assistant', 'KBSourceFile')

    documents = Document.objects.filter(status__in=['completed', 'ready', 'uploading'])
    if not documents.exists():
        print("  Nenhum documento para migrar.")
        return

    # 1. Criar ou buscar KB Global
    kb_global, created = KnowledgeBase.objects.get_or_create(
        kb_layer='global',
        name='KB Global',
        defaults={
            'id': uuid.uuid4(),
            'description': 'Base de conhecimento global (migrada do app kb)',
            'is_active': True,
        }
    )
    action = "Criada" if created else "Já existia"
    print(f"  {action}: KnowledgeBase '{kb_global.name}' (layer=global, id={kb_global.id})")

    total_files = 0
    total_embeddings = 0

    for doc in documents:
        chunks = DocumentChunk.objects.filter(
            document=doc,
            embedding__isnull=False,
        )
        chunk_count = chunks.count()

        if chunk_count == 0:
            print(f"  Pulando '{doc.title}' — 0 chunks com embedding")
            continue

        # 2. Criar KBSourceFile
        source_file = KBSourceFile.objects.create(
            id=uuid.uuid4(),
            knowledge_base=kb_global,
            file_name=doc.title,
            file_size=doc.file_size or 0,
            file_type=doc.file_type or '',
            category=doc.category or '',
            tags=doc.tags or [],
            chunk_count=chunk_count,
            status='completed',
            uploaded_by=doc.uploaded_by,
        )
        # Copiar referência do arquivo R2 se existir
        if doc.file:
            source_file.file = doc.file
            source_file.save()

        total_files += 1
        print(f"  KBSourceFile: '{doc.title}' ({chunk_count} chunks)")

        # 3. Copiar DocumentChunk → KnowledgeBaseEmbedding
        embeddings_to_create = []
        for chunk in chunks:
            embeddings_to_create.append(
                KnowledgeBaseEmbedding(
                    id=uuid.uuid4(),
                    knowledge_base=kb_global,
                    source_name=doc.title,
                    source_type=doc.file_type or 'pdf',
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.content,
                    chunk_size=len(chunk.content),
                    embedding=chunk.embedding,
                    embedding_model='text-embedding-3-small',
                    metadata={
                        'migrated_from': 'kb.DocumentChunk',
                        'original_document_id': str(doc.id),
                        'original_chunk_id': str(chunk.id),
                        'category': doc.category or '',
                        'tags': doc.tags or [],
                    },
                )
            )

        # Bulk create em lotes de 500
        batch_size = 500
        for i in range(0, len(embeddings_to_create), batch_size):
            batch = embeddings_to_create[i:i + batch_size]
            KnowledgeBaseEmbedding.objects.bulk_create(batch)

        total_embeddings += len(embeddings_to_create)

    print(f"  === Migração concluída: {total_files} arquivos, {total_embeddings} embeddings ===")


def reverse_migration(apps, schema_editor):
    """Remove dados migrados (KBSourceFiles + embeddings com metadata migrated_from)"""
    KnowledgeBaseEmbedding = apps.get_model('intelligent_assistant', 'KnowledgeBaseEmbedding')
    KBSourceFile = apps.get_model('intelligent_assistant', 'KBSourceFile')
    KnowledgeBase = apps.get_model('intelligent_assistant', 'KnowledgeBase')

    # Remover embeddings migrados
    deleted_emb = KnowledgeBaseEmbedding.objects.filter(
        metadata__contains={'migrated_from': 'kb.DocumentChunk'}
    ).delete()
    print(f"  Removidos {deleted_emb[0]} embeddings migrados")

    # Remover source files da KB Global
    kb_global = KnowledgeBase.objects.filter(kb_layer='global', name='KB Global').first()
    if kb_global:
        deleted_files = KBSourceFile.objects.filter(knowledge_base=kb_global).delete()
        print(f"  Removidos {deleted_files[0]} source files")

        # Remover KB Global se vazia
        if kb_global.embeddings.count() == 0:
            kb_global.delete()
            print("  KB Global removida")


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0026_add_kb_source_file_model'),
        ('kb', '0004_add_uploading_ready_status'),  # última migration do app kb
    ]

    operations = [
        migrations.RunPython(migrate_kb_data, reverse_migration),
    ]
