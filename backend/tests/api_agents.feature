# language: pt

Funcionalidade: Gerenciamento de Agentes de IA
  Como um administrador do sistema
  Eu quero gerenciar diferentes tipos de agentes de IA
  Para que os usuários possam utilizar assistência inteligente em diferentes contextos

  Contexto:
    Dado que estou autenticado como administrador
    E o sistema possui os seguintes tipos de agentes:
      | Tipo                | API Base                          | Tabela                       |
      | AgentPrompt         | /api/v1/agents/                   | agents_agentprompt           |
      | FormAssistant       | /api/v1/forms/assistants/         | forms_formassistant          |

  # ==========================================
  # AGENTPROMPT - Assistentes de Chat
  # ==========================================

  Cenário: Listar todos os AgentPrompts
    Dado que existem 1 AgentPrompt cadastrados no sistema
    Quando faço uma requisição GET para "/api/v1/agents/"
    Então o status code deve ser 200
    E o JSON de resposta deve conter:
      | campo   | valor |
      | count   | 1     |
    E a lista "results" deve ter 1 item
    E cada item deve conter os campos:
      | id | name | description | category | agent_type | llm_provider | model_name | is_active | is_default |

  Cenário: Filtrar AgentPrompts por categoria chat_assistant
    Dado que existem AgentPrompts com category "chat_assistant"
    Quando faço uma requisição GET para "/api/v1/agents/?category=chat_assistant"
    Então o status code deve ser 200
    E todos os resultados devem ter "category" igual a "chat_assistant"

  Cenário: Buscar AgentPrompt por ID
    Dado que existe um AgentPrompt com ID "508f44f6-ebc3-4cb8-b4f1-51b2b8d0310f"
    Quando faço uma requisição GET para "/api/v1/agents/508f44f6-ebc3-4cb8-b4f1-51b2b8d0310f/"
    Então o status code deve ser 200
    E o JSON de resposta deve conter:
      | campo         | valor                              |
      | id            | 508f44f6-ebc3-4cb8-b4f1-51b2b8d0310f |
      | category      | chat_assistant                      |
      | agent_type    | chat_assistant                      |

  Cenário: Obter estatísticas de AgentPrompts
    Dado que existem AgentPrompts cadastrados
    Quando faço uma requisição GET para "/api/v1/agents/stats/"
    Então o status code deve ser 200
    E o JSON de resposta deve conter:
      | campo | tipo   |
      | total | number |
      | active | number |
      | by_category | object |
      | by_provider | object |
    E "by_category.chat_assistant" deve existir
    E "by_category.chat_assistant.count" deve ser maior ou igual a 0

  Cenário: Criar um novo AgentPrompt
    Dado que tenho os seguintes dados de AgentPrompt:
      """
      {
        "name": "Assistente de Teste",
        "description": "Assistente criado para testes",
        "category": "chat_assistant",
        "agent_type": "chat_assistant",
        "system_prompt": "Você é um assistente de teste",
        "user_prompt_template": "Responda: {{message}}",
        "llm_provider": "openai",
        "model_name": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
        "use_rag": false,
        "is_active": true,
        "is_default": false
      }
      """
    Quando faço uma requisição POST para "/api/v1/agents/" com os dados acima
    Então o status code deve ser 201
    E o JSON de resposta deve conter um "id"
    E o campo "name" deve ser "Assistente de Teste"

  Cenário: Atualizar um AgentPrompt existente
    Dado que existe um AgentPrompt com ID "508f44f6-ebc3-4cb8-b4f1-51b2b8d0310f"
    Quando faço uma requisição PATCH para "/api/v1/agents/508f44f6-ebc3-4cb8-b4f1-51b2b8d0310f/" com:
      """
      {
        "description": "Descrição atualizada via teste BDD"
      }
      """
    Então o status code deve ser 200
    E o campo "description" deve ser "Descrição atualizada via teste BDD"

  Cenário: Duplicar um AgentPrompt
    Dado que existe um AgentPrompt com ID "508f44f6-ebc3-4cb8-b4f1-51b2b8d0310f"
    Quando faço uma requisição POST para "/api/v1/agents/508f44f6-ebc3-4cb8-b4f1-51b2b8d0310f/duplicate/"
    Então o status code deve ser 201
    E o JSON de resposta deve conter um novo "id" diferente do original
    E o campo "name" deve conter "(cópia)"
    E o campo "is_active" deve ser false

  Cenário: Deletar um AgentPrompt
    Dado que existe um AgentPrompt com ID "abc-123"
    Quando faço uma requisição DELETE para "/api/v1/agents/abc-123/"
    Então o status code deve ser 204

  Cenário: Tentar buscar AgentPrompt inexistente
    Quando faço uma requisição GET para "/api/v1/agents/00000000-0000-0000-0000-000000000000/"
    Então o status code deve ser 404

  # ==========================================
  # FORMASSISTANT - Assistentes de Campo
  # ==========================================

  Cenário: Listar todos os FormAssistants
    Dado que existem 8 FormAssistants cadastrados no sistema
    Quando faço uma requisição GET para "/api/v1/forms/assistants/"
    Então o status code deve ser 200
    E o JSON de resposta deve conter:
      | campo   | valor |
      | count   | 8     |
    E a lista "results" deve ter 8 itens
    E cada item deve conter os campos:
      | id | name | description | assistant_type | llm_provider | model_name | is_active | is_default |

  Cenário: Filtrar FormAssistants por tipo
    Dado que existem FormAssistants com assistant_type "corretor"
    Quando faço uma requisição GET para "/api/v1/forms/assistants/?assistant_type=corretor"
    Então o status code deve ser 200
    E todos os resultados devem ter "assistant_type" igual a "corretor"

  Cenário: Validar tipos de FormAssistant disponíveis
    Dado que existem FormAssistants cadastrados
    Quando faço uma requisição GET para "/api/v1/forms/assistants/"
    Então o status code deve ser 200
    E os assistant_type devem incluir:
      | tipo           |
      | analise        |
      | corretor       |
      | exemplo        |
      | expansao       |
      | resumo         |
      | simplificacao  |
      | sugestao       |
      | tradutor       |

  Cenário: Obter estatísticas de FormAssistants
    Dado que existem FormAssistants cadastrados
    Quando faço uma requisição GET para "/api/v1/forms/assistants/stats/"
    Então o status code deve ser 200
    E o JSON de resposta deve conter:
      | campo       | tipo   |
      | total       | number |
      | active      | number |
      | by_provider | object |

  Cenário: Buscar FormAssistant padrão para corretor
    Dado que existem FormAssistants com assistant_type "corretor"
    Quando faço uma requisição GET para "/api/v1/forms/assistants/?assistant_type=corretor&is_default=true"
    Então o status code deve ser 200
    E deve existir pelo menos 1 resultado
    E o primeiro resultado deve ter "is_default" igual a true

  Cenário: Criar um novo FormAssistant
    Dado que tenho os seguintes dados de FormAssistant:
      """
      {
        "name": "Validador de CPF/CNPJ",
        "description": "Valida e formata CPF/CNPJ",
        "assistant_type": "validacao",
        "system_prompt": "Você valida CPF e CNPJ",
        "user_prompt_template": "Validar: {{value}}",
        "llm_provider": "openai",
        "model_name": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 500,
        "use_rag": false,
        "is_active": true,
        "is_default": false
      }
      """
    Quando faço uma requisição POST para "/api/v1/forms/assistants/" com os dados acima
    Então o status code deve ser 201
    E o campo "name" deve ser "Validador de CPF/CNPJ"
    E o campo "assistant_type" deve ser "validacao"

  Cenário: Duplicar um FormAssistant
    Dado que existe um FormAssistant com assistant_type "corretor"
    E o FormAssistant tem ID "{form_assistant_id}"
    Quando faço uma requisição POST para "/api/v1/forms/assistants/{form_assistant_id}/duplicate/"
    Então o status code deve ser 201
    E o campo "name" deve conter "(cópia)"
    E o campo "is_default" deve ser false

  # ==========================================
  # TESTES DE INTEGRAÇÃO
  # ==========================================

  Cenário: Verificar separação de responsabilidades entre modelos
    Dado que consulto todas as APIs
    Quando faço requisições para:
      | API                                  |
      | /api/v1/agents/                      |
      | /api/v1/forms/assistants/            |
    Então cada API deve retornar dados exclusivos do seu modelo
    E não deve haver sobreposição de registros

  Cenário: Validar estrutura de resposta paginada
    Quando faço uma requisição GET para qualquer listagem com "?page=1&page_size=10"
    Então o JSON de resposta deve conter:
      | campo    | tipo   |
      | count    | number |
      | next     | string ou null |
      | previous | string ou null |
      | results  | array  |

  Cenário: Validar campos obrigatórios em todas as APIs
    Dado que vou criar um registro em qualquer API
    Quando envio uma requisição POST sem os campos obrigatórios:
      | name |
      | system_prompt |
      | user_prompt_template |
      | llm_provider |
      | model_name |
    Então o status code deve ser 400
    E o JSON de resposta deve conter mensagens de erro para cada campo faltante

  Cenário: Validar autenticação nas APIs
    Dado que não estou autenticado
    Quando faço uma requisição GET para "/api/v1/agents/"
    Então o status code deve ser 401
    E o JSON de resposta deve conter "detail" com mensagem de autenticação necessária

  # ==========================================
  # TESTES DE EDGE CASES
  # ==========================================

  Cenário: Tentar criar AgentPrompt com category inválida
    Dado que tenho dados com category "invalid_category"
    Quando faço uma requisição POST para "/api/v1/agents/" com os dados
    Então o status code deve ser 400

  Cenário: Tentar criar FormAssistant com assistant_type vazio
    Dado que tenho dados com assistant_type ""
    Quando faço uma requisição POST para "/api/v1/forms/assistants/" com os dados
    Então o status code deve ser 400

  Cenário: Validar campos somente leitura
    Dado que existe um AgentPrompt
    Quando tento atualizar campos somente leitura como "created_at", "updated_at", "created_by_name"
    Então esses campos não devem ser alterados
    E o status code deve ser 200
