# Bravonix — Assets de imagem

Este diretório contém as variações oficiais do logotipo Bravonix e marcas
relacionadas. Consulte a referência completa em
`01_identidade_visual/DESIGN_SYSTEM_BRAVONIX.md` (seção 5.5).

---

## Uso rápido

| Arquivo | Usar quando |
|---|---|
| `logo.png` | Avatar, header, favicon, welcome — qualquer ícone de marca em interfaces web (funciona em claro e escuro) |
| `favicon.png` | Tag `<link rel="icon">` — idêntico a `logo.png` |
| `bravonix-logo.png` | Logotipo completo com wordmark — fundo escuro (`#0A0A0A`, `#1A1A1A`) |
| `bravonix-logo-light.png` | Logotipo completo com wordmark — fundo claro (`#FFFFFF`, `#F8F7F5`) |
| `bravonix-dark.png` | Pré-visualização da marca compacta sobre fundo escuro |
| `bravonix-light.png` | Pré-visualização da marca compacta sobre fundo claro |
| `bravonix-purple-on-light.png` | Marca roxa sobre fundo claro — contexto editorial ou institucional |
| `orchestrate.png` | Exclusivo do produto Bravonix Orchestrate |

## Regras

1. **Avatar e header de app:** sempre `logo.png`.
2. **Logotipo completo em landing page dark:** `bravonix-logo.png`.
3. **Logotipo completo em landing page light:** `bravonix-logo-light.png`.
4. **Alternância de tema:** trocar o logotipo completo dinamicamente.
   O `logo.png` compacto não precisa de troca.
5. **Orchestrate:** usar apenas em interfaces do produto Orchestrate.

## Exemplo HTML

```html
<!-- Favicon -->
<link rel="icon" type="image/png" href="assets/favicon.png">

<!-- Ícone compacto (qualquer tema) -->
<img src="assets/logo.png" alt="Bravonix" width="32" height="32">

<!-- Logotipo completo em fundo escuro -->
<img src="assets/bravonix-logo.png" alt="Bravonix" style="height:40px">
```
