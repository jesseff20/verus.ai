# Generated migration for cover page and typography fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0011_section_feedback'),
    ]

    operations = [
        # ========================================
        # CAMPOS DE PÁGINA DE ROSTO
        # ========================================
        migrations.AddField(
            model_name='documentblueprint',
            name='cover_page_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Se deve gerar página de rosto no PDF',
                verbose_name='Habilitar Página de Rosto'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='cover_logo',
            field=models.ImageField(
                blank=True,
                help_text='Logo específica para a página de rosto (se diferente da logo principal)',
                null=True,
                upload_to='blueprints/covers/',
                verbose_name='Logo da Capa'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='cover_title',
            field=models.CharField(
                blank=True,
                help_text='Título principal da capa (ex: "ESTUDO TÉCNICO PRELIMINAR")',
                max_length=255,
                verbose_name='Título da Capa'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='cover_subtitle',
            field=models.CharField(
                blank=True,
                help_text='Subtítulo da capa (ex: "Lei 14.133/2021")',
                max_length=255,
                verbose_name='Subtítulo da Capa'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='cover_organization_text',
            field=models.TextField(
                blank=True,
                help_text='Texto completo da organização para a capa (pode ter várias linhas)',
                verbose_name='Texto da Organização na Capa'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='cover_footer_text',
            field=models.CharField(
                blank=True,
                help_text='Texto do rodapé da capa (ex: "Rio de Janeiro - 2026")',
                max_length=255,
                verbose_name='Rodapé da Capa'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='cover_background_color',
            field=models.CharField(
                default='#FFFFFF',
                help_text='Cor de fundo da página de rosto (formato hex: #RRGGBB)',
                max_length=7,
                verbose_name='Cor de Fundo da Capa'
            ),
        ),

        # ========================================
        # CAMPOS DE TIPOGRAFIA
        # ========================================
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_font_family',
            field=models.CharField(
                default='Times New Roman',
                help_text='Família de fonte (ex: "Times New Roman", "Arial", "Calibri")',
                max_length=100,
                verbose_name='Fonte do PDF'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_font_size',
            field=models.CharField(
                default='12pt',
                help_text='Tamanho da fonte do corpo (ex: "12pt", "11pt")',
                max_length=10,
                verbose_name='Tamanho da Fonte'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_line_height',
            field=models.CharField(
                default='1.5',
                help_text='Espaçamento entre linhas (ex: "1.5", "1.8", "2.0")',
                max_length=10,
                verbose_name='Altura da Linha'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_text_align',
            field=models.CharField(
                choices=[
                    ('justify', 'Justificado'),
                    ('left', 'Esquerda'),
                    ('right', 'Direita'),
                    ('center', 'Centralizado')
                ],
                default='justify',
                help_text='Alinhamento do texto do corpo',
                max_length=20,
                verbose_name='Alinhamento do Texto'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_paragraph_indent',
            field=models.CharField(
                default='1.5cm',
                help_text='Recuo da primeira linha do parágrafo (ex: "1.5cm", "0")',
                max_length=10,
                verbose_name='Recuo do Parágrafo'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_paragraph_spacing',
            field=models.CharField(
                default='12pt',
                help_text='Espaço entre parágrafos (ex: "12pt", "6pt")',
                max_length=10,
                verbose_name='Espaçamento entre Parágrafos'
            ),
        ),

        # ========================================
        # CAMPOS DE MARGENS
        # ========================================
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_page_margin_top',
            field=models.CharField(
                default='2.5cm',
                help_text='Margem superior da página',
                max_length=10,
                verbose_name='Margem Superior'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_page_margin_bottom',
            field=models.CharField(
                default='2.5cm',
                help_text='Margem inferior da página',
                max_length=10,
                verbose_name='Margem Inferior'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_page_margin_left',
            field=models.CharField(
                default='3cm',
                help_text='Margem esquerda da página',
                max_length=10,
                verbose_name='Margem Esquerda'
            ),
        ),
        migrations.AddField(
            model_name='documentblueprint',
            name='pdf_page_margin_right',
            field=models.CharField(
                default='2cm',
                help_text='Margem direita da página',
                max_length=10,
                verbose_name='Margem Direita'
            ),
        ),
    ]
