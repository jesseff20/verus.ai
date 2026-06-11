"""
Constantes centralizadas para o serviço de embeddings (IBM watsonx E5-Large).
"""

# Modelo de embedding via IBM watsonx
EMBEDDING_MODEL_ID = 'intfloat/multilingual-e5-large'
EMBEDDING_DIMENSIONS = 1024
EMBEDDING_MAX_TOKENS = 512

# Prefixos obrigatórios do E5 (assimétricos)
# - query:   usado para BUSCAS (quando o usuário pesquisa)
# - passage: usado para INDEXAÇÃO (quando armazenamos documentos)
E5_QUERY_PREFIX = 'query: '
E5_PASSAGE_PREFIX = 'passage: '

# Limites de batch
EMBEDDING_BATCH_SIZE = 500
EMBEDDING_CONCURRENCY_LIMIT = 5
