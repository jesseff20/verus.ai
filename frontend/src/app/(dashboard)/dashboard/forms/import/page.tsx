'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, Upload, FileJson, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';

export default function ImportFormPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('peticao_inicial');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setError(null);
    setPreviewData(null);

    // Preview do JSON
    if (selectedFile.name.endsWith('.json')) {
      try {
        const text = await selectedFile.text();
        const json = JSON.parse(text);
        setPreviewData(json);

        // Preencher nome e descrição se existirem no JSON
        if (json.name && !name) setName(json.name);
        if (json.description && !description) setDescription(json.description);
        if (json.category && category === 'peticao_inicial') setCategory(json.category);
      } catch (err) {
        setError('Erro ao ler o arquivo JSON. Verifique se é um JSON válido.');
      }
    } else {
      setError('Por favor, selecione um arquivo .json');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('Por favor, selecione um arquivo JSON.');
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (name) formData.append('name', name);
      if (description) formData.append('description', description);
      if (category) formData.append('category', category);

      const response = await api.post('/api/v1/forms/import-json/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess(true);

      // Redirecionar após 2 segundos
      setTimeout(() => {
        router.push('/dashboard/forms');
      }, 2000);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao importar formulário';
      setError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const getFieldCount = () => {
    if (!previewData) return 0;

    if (Array.isArray(previewData)) {
      return previewData.length;
    }

    if (previewData.fields && Array.isArray(previewData.fields)) {
      return previewData.fields.length;
    }

    if (previewData.sections && Array.isArray(previewData.sections)) {
      return previewData.sections.reduce((total: number, section: any) => {
        return total + (section.fields?.length || 0);
      }, 0);
    }

    return 0;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/forms">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Importar Formulário</h1>
          <p className="text-muted-foreground">
            Importe um formulário completo a partir de um arquivo JSON
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Formulário de Upload */}
        <Card>
          <CardHeader>
            <CardTitle>Upload do Arquivo JSON</CardTitle>
            <CardDescription>
              Selecione um arquivo JSON contendo a estrutura do formulário
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Upload do arquivo */}
              <div className="space-y-2">
                <Label htmlFor="file">
                  Arquivo JSON <span className="text-red-500">*</span>
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="file"
                    type="file"
                    accept=".json,application/json"
                    onChange={handleFileChange}
                    disabled={isUploading}
                  />
                  {file && (
                    <FileJson className="h-5 w-5 text-primary" />
                  )}
                </div>
                {file && (
                  <p className="text-sm text-muted-foreground">
                    Arquivo: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                  </p>
                )}
              </div>

              {/* Nome do formulário */}
              <div className="space-y-2">
                <Label htmlFor="name">Nome do Formulário</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Será usado o nome do JSON se não informado"
                  disabled={isUploading}
                />
                <p className="text-sm text-muted-foreground">
                  Opcional - deixe vazio para usar o nome do JSON
                </p>
              </div>

              {/* Descrição */}
              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <div className="relative">
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Descreva o formulário..."
                    rows={3}
                    disabled={isUploading}
                    className="pr-32"
                  />
                  <div className="absolute top-1 right-1">
                    <AIEnhanceButton
                      value={description}
                      onEnhance={setDescription}
                      context="descrição de formulário jurídico"
                      disabled={isUploading}
                    />
                  </div>
                </div>
              </div>

              {/* Categoria */}
              <div className="space-y-2">
                <Label htmlFor="category">Categoria</Label>
                <Select
                  value={category}
                  onValueChange={setCategory}
                  disabled={isUploading}
                >
                  <SelectTrigger id="category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="peticao_inicial">Petição Inicial</SelectItem>
                    <SelectItem value="contestacao">Contestação</SelectItem>
                    <SelectItem value="recurso">Recurso</SelectItem>
                    <SelectItem value="parecer">Parecer Jurídico</SelectItem>
                    <SelectItem value="contrato">Contrato</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Mensagens de erro/sucesso */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="bg-green-50 border-green-200">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">
                    Formulário importado com sucesso! Redirecionando...
                  </AlertDescription>
                </Alert>
              )}

              {/* Botões */}
              <div className="flex gap-2">
                <Button type="submit" disabled={isUploading || !file}>
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Importando...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Importar Formulário
                    </>
                  )}
                </Button>
                <Link href="/dashboard/forms">
                  <Button type="button" variant="outline" disabled={isUploading}>
                    Cancelar
                  </Button>
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Preview do JSON */}
        <Card>
          <CardHeader>
            <CardTitle>Pré-visualização</CardTitle>
            <CardDescription>
              Informações extraídas do arquivo JSON
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!previewData ? (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <FileJson className="h-16 w-16 mb-4 opacity-50" />
                <p className="text-center">
                  Selecione um arquivo JSON para visualizar seu conteúdo
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Nome</p>
                    <p className="text-sm font-mono">
                      {previewData.name || name || 'Sem nome'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Categoria</p>
                    <p className="text-sm font-mono">
                      {previewData.category || category}
                    </p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Descrição</p>
                  <p className="text-sm">
                    {previewData.description || description || 'Sem descrição'}
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Estrutura</p>
                  <div className="bg-muted p-3 rounded-md space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Total de campos:</span>
                      <span className="text-sm font-bold">{getFieldCount()}</span>
                    </div>
                    {previewData.sections && (
                      <div className="flex justify-between">
                        <span className="text-sm">Seções:</span>
                        <span className="text-sm font-bold">{previewData.sections.length}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    JSON Compacto
                  </p>
                  <div className="bg-black text-green-400 p-3 rounded-md text-xs font-mono overflow-x-auto max-h-60">
                    <pre>{JSON.stringify(previewData, null, 2)}</pre>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Card de ajuda */}
      <Card>
        <CardHeader>
          <CardTitle>Formatos Suportados</CardTitle>
          <CardDescription>
            O sistema aceita dois formatos de JSON
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">1. Array Flat (Recomendado)</h4>
            <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`[
  {
    "id": "campo_1",
    "type": "text",
    "label": "Nome do Campo",
    "required": true,
    "placeholder": "Digite aqui...",
    "help_text": "Texto de ajuda"
  },
  ...
]`}
            </pre>
          </div>

          <div>
            <h4 className="font-medium mb-2">2. Com Seções (Será convertido)</h4>
            <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
{`{
  "name": "Meu Formulário",
  "description": "Descrição do formulário",
  "category": "acoes_peticoes",
  "sections": [
    {
      "title": "Seção 1",
      "fields": [
        {
          "id": "campo_1",
          "type": "text",
          "label": "Nome do Campo"
        }
      ]
    }
  ]
}`}
            </pre>
          </div>

          <Alert>
            <AlertDescription>
              <strong>Dica:</strong> Se você usar o formato com seções, o sistema irá
              converter automaticamente para o formato flat, mantendo todos os campos.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
}
