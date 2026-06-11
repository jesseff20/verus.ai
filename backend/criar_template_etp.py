#!/usr/bin/env python
"""
Script para criar Template e Formulário de ETP via API
"""
import requests
import json
import os

# Configurações
API_BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def get_auth_token():
    """Obtém token de autenticação"""
    print("🔐 Autenticando...")
    response = requests.post(
        f"{API_BASE_URL}/auth/auth/login/",
        json={"username": USERNAME, "password": PASSWORD}
    )

    if response.status_code == 200:
        token = response.json()["tokens"]["access"]
        print("✅ Autenticado com sucesso!")
        return token
    else:
        print(f"❌ Erro na autenticação: {response.status_code}")
        print(response.text)
        return None

def criar_template_documento(token):
    """Cria template de documento HTML"""
    print("\n📄 Criando Template de Documento...")

    # Ler o arquivo HTML
    html_path = "../frontend/template_exemplo_etp.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    data = {
        "name": "Template ETP - Estudo Técnico Preliminar",
        "description": "Template completo de ETP conforme Lei 14.133/2021 com 15 seções",
        "content": html_content,
        "is_active": True
    }

    response = requests.post(
        f"{API_BASE_URL}/templates/",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )

    if response.status_code == 201:
        resp_json = response.json()
        print(f"📋 Resposta completa: {json.dumps(resp_json, indent=2)}")
        template_id = resp_json.get("id") or resp_json.get("uuid")
        print(f"✅ Template criado com ID: {template_id}")
        return template_id
    else:
        print(f"❌ Erro ao criar template: {response.status_code}")
        print(response.text)
        return None

def criar_formulario(token):
    """Cria formulário JSON"""
    print("\n📝 Criando Formulário...")

    # Ler o arquivo JSON
    json_path = "../frontend/formulario_exemplo_etp.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        form_fields = json.load(f)

    data = {
        "name": "Formulário ETP - Estudo Técnico Preliminar",
        "description": "Formulário completo para criação de ETP com 9 seções e 90+ campos",
        "fields": form_fields,
        "is_active": True
    }

    response = requests.post(
        f"{API_BASE_URL}/forms/",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )

    if response.status_code == 201:
        resp_json = response.json()
        print(f"📋 Resposta completa: {json.dumps(resp_json, indent=2)}")
        form_id = resp_json.get("id") or resp_json.get("uuid")
        print(f"✅ Formulário criado com ID: {form_id}")
        return form_id
    else:
        print(f"❌ Erro ao criar formulário: {response.status_code}")
        print(response.text)
        return None

def main():
    print("=" * 60)
    print("🚀 SCRIPT DE CRIAÇÃO DE TEMPLATE E FORMULÁRIO ETP")
    print("=" * 60)

    # Autenticar
    token = get_auth_token()
    if not token:
        print("\n❌ Não foi possível autenticar. Verifique as credenciais.")
        return

    # Criar template
    template_id = criar_template_documento(token)

    # Criar formulário
    form_id = criar_formulario(token)

    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)

    if template_id and form_id:
        print(f"✅ Template ID: {template_id}")
        print(f"✅ Formulário ID: {form_id}")
        print("\n🎉 Tudo criado com sucesso!")
        print("\n📝 Próximos passos:")
        print("1. Acesse /criar-documento no frontend")
        print("2. Selecione o Template e Formulário criados")
        print("3. Comece a preencher!")
    else:
        print("\n❌ Houve erros na criação. Verifique os logs acima.")

if __name__ == "__main__":
    main()
