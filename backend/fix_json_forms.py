#!/usr/bin/env python3
"""
Script para corrigir JSONs de formulários para o formato esperado pelo sistema.

Converte:
- Remove wrapper "form_schema"
- field_id → id
- field_name → label
- field_type → type
"""
import json
import os
from pathlib import Path

def fix_field(field):
    """Corrige um campo individual."""
    fixed = {}

    # Mapear field_id → id
    if 'field_id' in field:
        fixed['id'] = field['field_id']
    elif 'id' in field:
        fixed['id'] = field['id']

    # Mapear field_type → type
    if 'field_type' in field:
        fixed['type'] = field['field_type']
    elif 'type' in field:
        fixed['type'] = field['type']

    # Mapear field_name → label
    if 'field_name' in field:
        fixed['label'] = field['field_name']
    elif 'label' in field:
        fixed['label'] = field['label']

    # Copiar outros campos mantendo o nome original
    for key, value in field.items():
        if key not in ['field_id', 'field_name', 'field_type', 'id', 'label', 'type']:
            fixed[key] = value

    return fixed

def fix_json_file(file_path):
    """Corrige um arquivo JSON."""
    print(f"\n📄 Processando: {file_path.name}")

    try:
        # Ler JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Remover wrapper form_schema se existir
        if isinstance(data, dict) and 'form_schema' in data:
            print("   ✓ Removendo wrapper 'form_schema'")
            data = data['form_schema']

        # Processar sections e fields
        fixed_data = {}
        fields_fixed = 0

        if 'sections' in data:
            fixed_data['sections'] = []
            for section in data['sections']:
                fixed_section = {}

                # Copiar metadados da section (exceto fields)
                for key, value in section.items():
                    if key != 'fields':
                        fixed_section[key] = value

                # Processar fields
                if 'fields' in section:
                    fixed_section['fields'] = []
                    for field in section['fields']:
                        fixed_field = fix_field(field)
                        fixed_section['fields'].append(fixed_field)
                        fields_fixed += 1

                fixed_data['sections'].append(fixed_section)

        elif 'fields' in data:
            fixed_data['fields'] = []
            for field in data['fields']:
                fixed_field = fix_field(field)
                fixed_data['fields'].append(fixed_field)
                fields_fixed += 1

        print(f"   ✓ {fields_fixed} campos corrigidos")

        # Sobrescrever arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)

        print(f"   ✅ Arquivo salvo")
        return True

    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False

def main():
    """Função principal."""
    print("="*80)
    print("🔧 CORREÇÃO DE JSONs DE FORMULÁRIOS")
    print("="*80)

    # Caminho para a pasta de formulários
    forms_dir = Path(__file__).parent.parent / 'documents' / 'forms'

    if not forms_dir.exists():
        print(f"\n❌ Pasta não encontrada: {forms_dir}")
        return

    print(f"\n📁 Pasta: {forms_dir}")

    # Encontrar todos os JSONs
    json_files = list(forms_dir.glob('*.json'))

    if not json_files:
        print("\n⚠️  Nenhum arquivo JSON encontrado")
        return

    print(f"\n📋 Encontrados {len(json_files)} arquivos JSON")

    # Processar cada arquivo
    success_count = 0
    for json_file in json_files:
        if fix_json_file(json_file):
            success_count += 1

    # Relatório final
    print("\n" + "="*80)
    print("📊 RESULTADO")
    print("="*80)
    print(f"✅ Arquivos corrigidos: {success_count}/{len(json_files)}")

    if success_count == len(json_files):
        print("\n🎉 Todos os arquivos foram corrigidos com sucesso!")
    elif success_count > 0:
        print(f"\n⚠️  {len(json_files) - success_count} arquivo(s) com erro")
    else:
        print("\n❌ Nenhum arquivo foi corrigido")

    print("\n" + "="*80)

if __name__ == '__main__':
    main()
