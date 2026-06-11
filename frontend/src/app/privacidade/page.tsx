'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Shield,
  ChevronLeft,
  Download,
  Printer,
  Mail,
  Lock,
  UserCheck,
  RefreshCcw,
  Share2,
  Eye,
  FileEdit,
  Trash2,
  FileOutput,
  Cookie,
  Server,
  KeyRound,
  Scale,
  Clock,
  Building2,
  AlertTriangle,
  CheckCircle2,
  Database,
  FileSearch,
} from 'lucide-react';

export default function PrivacidadePage() {
  const [showPrint, setShowPrint] = useState(false);

  const lastUpdate = '15 de janeiro de 2026';

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-purple-50/30">
      {/* ── Top bar ── */}
      <div className="sticky top-0 z-40 border-b border-purple-100/80 bg-white/90 backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-[#7030A0] transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            Voltar ao início
          </Link>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handlePrint} className="text-xs gap-1.5">
              <Printer className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Imprimir</span>
            </Button>
            <Button variant="outline" size="sm" className="text-xs gap-1.5">
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Download PDF</span>
            </Button>
          </div>
        </div>
      </div>

      {/* ── Header ── */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-10 pb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7030A0]/10">
            <Shield className="h-5 w-5 text-[#7030A0]" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Política de Privacidade
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Última atualização: {lastUpdate}
            </p>
          </div>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed mt-4 max-w-3xl">
          O Verus.AI, plataforma jurídica da{' '}
          <strong className="text-gray-900">Bravonix Tecnologia Ltda.</strong>, está
          comprometido com a proteção da sua privacidade. Esta Política de Privacidade
          descreve como coletamos, usamos, armazenamos e protegemos os dados pessoais
          dos nossos usuários, em conformidade com a{' '}
          <strong className="text-gray-900">
            Lei Geral de Proteção de Dados Pessoais (Lei n.º 13.709/2018 — LGPD)
          </strong>
          , o Marco Civil da Internet (Lei n.º 12.965/2014) e demais normas aplicáveis.
        </p>
      </div>

      {/* ── Content ── */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 pb-16 space-y-6">

        {/* 1. Controlador */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Building2 className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                1. Quem é o Controlador dos Dados?
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                A <strong>Bravonix Tecnologia Ltda.</strong>, inscrita no CNPJ sob o n.º
                00.000.000/0001-00, com sede na [endereço completo], é a controladora
                responsável pelo tratamento dos dados pessoais coletados por meio da
                plataforma Verus.AI, conforme definido no art. 5º, VI, da LGPD.
              </p>
              <p className="text-sm text-gray-600 leading-relaxed mt-2">
                Como controladora, a Bravonix define as finalidades e os meios de tratamento
                dos dados pessoais, e se compromete a atuar em conformidade com os princípios
                previstos no art. 6º da LGPD: finalidade, adequação, necessidade, livre
                acesso, qualidade dos dados, transparência, segurança, prevenção,
                não discriminação e responsabilização e prestação de contas.
              </p>
            </div>
          </div>
        </div>

        {/* 2. Dados Coletados */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Database className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                2. Quais Dados Coletamos e Como?
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-3">
                Coletamos apenas os dados estritamente necessários para a prestação dos
                serviços jurídicos da plataforma. A coleta ocorre por meio do fornecimento
                direto pelo usuário, coleta automatizada durante a navegação e integração
                com sistemas terceiros autorizados.
              </p>

              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="cadastro" className="border-purple-100">
                  <AccordionTrigger className="text-sm font-medium text-gray-800 hover:text-[#7030A0]">
                    Dados de cadastro e identificação
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-gray-600 space-y-1">
                    <p>Nome completo, CPF/CNPJ, OAB (para advogados), e-mail, telefone,
                    endereço profissional e dados de faturamento.</p>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="processuais" className="border-purple-100">
                  <AccordionTrigger className="text-sm font-medium text-gray-800 hover:text-[#7030A0]">
                    Dados processuais e jurídicos
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-gray-600 space-y-1">
                    <p>Informações de processos judiciais, petições, contratos, dados de
                    clientes dos escritórios, movimentações processuais e documentos
                    jurídicos armazenados na plataforma.</p>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="navegacao" className="border-purple-100">
                  <AccordionTrigger className="text-sm font-medium text-gray-800 hover:text-[#7030A0]">
                    Dados de navegação e uso
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-gray-600 space-y-1">
                    <p>Endereço IP, tipo de navegador, sistema operacional, páginas
                    acessadas, tempo de sessão, interações com a plataforma e logs de
                    uso. Coletados por cookies essenciais e ferramentas de analytics.</p>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="comunicacao" className="border-purple-100">
                  <AccordionTrigger className="text-sm font-medium text-gray-800 hover:text-[#7030A0]">
                    Dados de comunicação
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-gray-600 space-y-1">
                    <p>Registros de mensagens trocadas por meio do sistema de mensageria
                    da plataforma, tickets de suporte e comunicações com o DPO.</p>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          </div>
        </div>

        {/* 3. Finalidade e Base Legal */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Scale className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                3. Finalidades e Bases Legais para o Tratamento
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-3">
                Cada operação de tratamento de dados pessoais no Verus.AI está
                fundamentada em uma base legal específica, conforme exige o art. 7º da LGPD.
              </p>

              <div className="space-y-3">
                <div className="rounded-xl border border-purple-100 bg-purple-50/50 p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        Execução de contrato (art. 7º, V, LGPD)
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Para a prestação dos serviços contratados, incluindo geração de peças
                        processuais, gestão de casos e comunicação com clientes.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 bg-purple-50/50 p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        Cumprimento de obrigação legal ou regulatória (art. 7º, II, LGPD)
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Para atender obrigações fiscais, contábeis, previdenciárias e
                        regulatórias do exercício da advocacia (Estatuto da OAB, Provimentos
                        do CNJ, Código de Ética).
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 bg-purple-50/50 p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        Consentimento (art. 7º, I, LGPD)
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Para finalidades não essenciais, como envio de newsletters
                        marketing, cookies não essenciais e compartilhamento de dados com
                        terceiros para fins promocionais.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 bg-purple-50/50 p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        Exercício regular de direitos (art. 7º, VI, LGPD)
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Para o exercício de direitos em processos judiciais, administrativos
                        ou arbitrais, incluindo a defesa dos interesses dos clientes do escritório.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 4. Anonimização */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <FileSearch className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                4. Anonimização de Dados Sensíveis
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Dados sensíveis (art. 5º, II, LGPD) — como informações sobre convicções
                religiosas, políticas, dados genéticos, biométricos ou de saúde —
                <strong> não são coletados intencionalmente</strong> pelo Verus.AI. Caso
                tais dados estejam contidos em documentos jurídicos submetidos pelos
                usuários, aplicamos as seguintes técnicas de anonimização:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    <strong>Tokenização:</strong> substituição de identificadores pessoais
                    (nomes, CPFs, RG) por tokens únicos não reversíveis sem chave de
                    decodificação.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    <strong>Mascaramento:</strong> ocultação parcial de dados (ex.: CPF
                    000.000.000-00 → 000.xxx.xxx-00) em visualizações e relatórios.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    <strong>Generalização:</strong> substituição de valores precisos por
                    faixas ou categorias (ex.: idade 37 → faixa 30–40 anos).
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    <strong>Perturbação:</strong> adição controlada de ruído estatístico
                    para análise de dados agregados, impossibilitando reidentificação.
                  </span>
                </li>
              </ul>
              <p className="text-sm text-gray-500 italic mt-3">
                Dados anonimizados não são considerados dados pessoais para fins da LGPD
                (art. 12), podendo ser utilizados para treinamento de modelos de IA e
                análise estatística.
              </p>
            </div>
          </div>
        </div>

        {/* 5. Período de Retenção */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Clock className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                5. Período de Retenção de Dados
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Mantemos seus dados pessoais pelo tempo necessário para cumprir as
                finalidades para as quais foram coletados, respeitando os prazos legais
                e regulatórios aplicáveis:
              </p>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-purple-100">
                      <th className="text-left py-2 pr-4 font-medium text-gray-700">Tipo de Dado</th>
                      <th className="text-left py-2 pr-4 font-medium text-gray-700">Período de Retenção</th>
                      <th className="text-left py-2 font-medium text-gray-700">Fundamento Legal</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50">
                    <tr>
                      <td className="py-2.5 pr-4 text-gray-600">Dados cadastrais</td>
                      <td className="py-2.5 pr-4 text-gray-600">Durante a vigência do contrato + 5 anos</td>
                      <td className="py-2.5 text-gray-600">Art. 1.203 CC / art. 12 LGPD</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-4 text-gray-600">Dados processuais</td>
                      <td className="py-2.5 pr-4 text-gray-600">Durante a vigência do contrato</td>
                      <td className="py-2.5 text-gray-600">Execução de contrato</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-4 text-gray-600">Dados fiscais</td>
                      <td className="py-2.5 pr-4 text-gray-600">5 anos após o exercício fiscal</td>
                      <td className="py-2.5 text-gray-600">Art. 195 CTN / RIR</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-4 text-gray-600">Logs de acesso</td>
                      <td className="py-2.5 pr-4 text-gray-600">6 meses (mínimo legal)</td>
                      <td className="py-2.5 text-gray-600">Art. 10, §3º, Marco Civil</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-4 text-gray-600">Consentimentos</td>
                      <td className="py-2.5 pr-4 text-gray-600">Durante a relação contratual</td>
                      <td className="py-2.5 text-gray-600">Art. 7º, I, LGPD</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Após o término do prazo de retenção, os dados são eliminados de forma segura
                ou anonimizados.
              </p>
            </div>
          </div>
        </div>

        {/* 6. Compartilhamento */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Share2 className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                6. Compartilhamento com Terceiros
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-3">
                Podemos compartilhar seus dados pessoais com terceiros nas seguintes
                hipóteses, sempre em conformidade com a LGPD e mediante a celebração de
                contratos com cláusulas de proteção de dados:
              </p>

              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="operadores" className="border-purple-100">
                  <AccordionTrigger className="text-sm font-medium text-gray-800 hover:text-[#7030A0]">
                    Prestadores de serviço (operadores)
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-gray-600 space-y-1">
                    <p>Serviços de cloud computing (IBM Cloud, AWS), processamento de
                    pagamentos (Stripe, Asaas), envio de e-mails (AWS SES, SendGrid),
                    analytics e monitoramento (Sentry, Plausible).</p>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="integracoes" className="border-purple-100">
                  <AccordionTrigger className="text-sm font-medium text-gray-800 hover:text-[#7030A0]">
                    Integrações com sistemas jurídicos
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-gray-600 space-y-1">
                    <p>Integração com tribunais (PJe, e-SAJ, PROJUDI), plataformas de
                    assinatura digital (D4Sign, DocuSign), sistemas de protocolo e
                    emissão de NFS-e, conforme autorização do usuário.</p>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="obrigacao" className="border-purple-100">
                  <AccordionTrigger className="text-sm font-medium text-gray-800 hover:text-[#7030A0]">
                    Obrigação legal ou ordem judicial
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-gray-600 space-y-1">
                    <p>Compartilhamento com autoridades públicas, órgãos de fiscalização
                    (OAB, Receita Federal, CADE) ou por determinação judicial, sempre
                    limitado ao estritamente exigido.</p>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              <p className="text-xs text-gray-400 mt-3">
                O Verus.AI não vende dados pessoais a terceiros. Todos os operadores são
                contratualmente obrigados a respeitar os mesmos padrões de proteção.
              </p>
            </div>
          </div>
        </div>

        {/* 7. Medidas de Segurança */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Lock className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                7. Medidas de Segurança Adotadas
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-3">
                Empregamos medidas técnicas e administrativas para proteger os dados
                pessoais contra acessos não autorizados, destruição, perda, alteração
                ou qualquer forma de tratamento inadequado:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="rounded-xl border border-purple-100 bg-white p-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <KeyRound className="h-4 w-4 text-[#7030A0]" />
                    <span className="text-sm font-medium text-gray-800">Criptografia</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    Dados em trânsito: TLS 1.3 (HTTPS). Dados em repouso: AES-256.
                    Senhas armazenadas com bcrypt + salt.
                  </p>
                </div>

                <div className="rounded-xl border border-purple-100 bg-white p-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <UserCheck className="h-4 w-4 text-[#7030A0]" />
                    <span className="text-sm font-medium text-gray-800">Controle de Acesso</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    RBAC (Role-Based Access Control), autenticação 2FA, sessões com JWT
                    e política de privilégio mínimo.
                  </p>
                </div>

                <div className="rounded-xl border border-purple-100 bg-white p-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <Server className="h-4 w-4 text-[#7030A0]" />
                    <span className="text-sm font-medium text-gray-800">Infraestrutura</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    IBM Cloud com certificações SOC 2, ISO 27001. Backups diários com
                    retenção de 30 dias. Disaster recovery testado.
                  </p>
                </div>

                <div className="rounded-xl border border-purple-100 bg-white p-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <AlertTriangle className="h-4 w-4 text-[#7030A0]" />
                    <span className="text-sm font-medium text-gray-800">Monitoramento</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    WAF, IDS/IPS, detecção de anomalias, rate limiting e logging
                    centralizado com auditoria de acessos.
                  </p>
                </div>

                <div className="rounded-xl border border-purple-100 bg-white p-4 sm:col-span-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <RefreshCcw className="h-4 w-4 text-[#7030A0]" />
                    <span className="text-sm font-medium text-gray-800">Gestão de Incidentes</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    Plano de resposta a incidentes com notificação à ANPD e aos titulares
                    em até 72 horas, conforme art. 48 da LGPD. Testes de penetração
                    semestrais e análise de vulnerabilidades contínua.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 8. Direitos do Titular */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <UserCheck className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                8. Direitos do Titular (LGPD, Art. 18)
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-3">
                A LGPD garante a você, titular dos dados pessoais, os seguintes direitos,
                que podem ser exercidos a qualquer momento:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="rounded-xl border border-purple-100 p-4 flex items-start gap-3">
                  <Eye className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">Confirmação e Acesso</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Confirmar se tratamos seus dados e solicitar cópia completa.
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 p-4 flex items-start gap-3">
                  <FileEdit className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">Correção</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Solicitar a correção de dados incompletos, inexatos ou desatualizados.
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 p-4 flex items-start gap-3">
                  <Trash2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">Exclusão</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Solicitar a eliminação dos dados desnecessários ou tratados em
                      desconformidade com a lei.
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 p-4 flex items-start gap-3">
                  <FileOutput className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">Portabilidade</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Solicitar a transferência dos dados a outro fornecedor de serviço.
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 p-4 flex items-start gap-3">
                  <RefreshCcw className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">Revogação do Consentimento</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Revogar o consentimento a qualquer tempo, sem prejuízo da legalidade
                      do tratamento anterior.
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-purple-100 p-4 flex items-start gap-3">
                  <AlertTriangle className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">Oposição</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Opor-se ao tratamento com base em outras hipóteses legais, em caso
                      de descumprimento da lei.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-xl bg-[#7030A0]/5 border border-[#7030A0]/20 p-4">
                <p className="text-sm text-gray-700">
                  <strong>Para exercer seus direitos,</strong> entre em contato com nosso
                  Encarregado de Dados (DPO) pelo e-mail{' '}
                  <a href="mailto:dpo@verus.ai" className="text-[#7030A0] font-medium hover:underline">
                    dpo@verus.ai
                  </a>. Responderemos em até{' '}
                  <strong>15 dias</strong>, conforme o art. 43 da LGPD e o Decreto n.º
                  8.771/2016.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 9. Cookies */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Cookie className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                9. Cookies e Tecnologias de Rastreamento
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Utilizamos cookies e tecnologias similares para melhorar sua experiência
                na plataforma. Consulte nossa{' '}
                <Link href="/cookies" className="text-[#7030A0] font-medium hover:underline">
                  Política de Cookies
                </Link>{' '}
                para informações detalhadas sobre cada cookie utilizado, suas finalidades
                e como gerenciar suas preferências.
              </p>
            </div>
          </div>
        </div>

        {/* 10. DPO */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Mail className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                10. Encarregado de Dados (DPO)
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                A Bravonix designou um Encarregado de Dados (DPO) para atuar como canal
                de comunicação com os titulares, a ANPD e demais partes interessadas,
                conforme o art. 41 da LGPD.
              </p>
              <div className="mt-3 rounded-xl bg-gray-50 border border-gray-200 p-4 space-y-2">
                <p className="text-sm text-gray-700">
                  <strong>Encarregado:</strong> [Nome do DPO]
                </p>
                <p className="text-sm text-gray-700">
                  <strong>E-mail:</strong>{' '}
                  <a href="mailto:dpo@verus.ai" className="text-[#7030A0] font-medium hover:underline">
                    dpo@verus.ai
                  </a>
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Telefone:</strong> (XX) XXXX-XXXX
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Endereço:</strong> [Endereço comercial completo]
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 11. Atualizações */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <RefreshCcw className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                11. Atualizações desta Política
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Esta Política de Privacidade pode ser atualizada periodicamente para
                refletir mudanças nas práticas de tratamento de dados ou na legislação
                aplicável. Notificaremos os usuários sobre alterações significativas por
                meio de:
              </p>
              <ul className="mt-2 space-y-1 text-sm text-gray-600 list-disc list-inside">
                <li>Comunicação por e-mail para o endereço cadastrado;</li>
                <li>Aviso no painel da plataforma;</li>
                <li>Atualização da data de última modificação no topo desta página.</li>
              </ul>
              <p className="text-sm text-gray-500 mt-2">
                Recomendamos a revisão periódica desta página. O uso continuado da
                plataforma após a publicação de alterações constitui aceitação das
                novas disposições.
              </p>
            </div>
          </div>
        </div>

        <Separator className="bg-purple-100" />

        {/* Footer links */}
        <div className="text-center space-y-3">
          <p className="text-xs text-gray-400">
            Versão 1.0 — Última atualização: {lastUpdate}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
            <Link href="/cookies" className="text-[#7030A0] hover:underline font-medium">
              Política de Cookies
            </Link>
            <span className="text-gray-300">•</span>
            <Link href="/consentimento" className="text-[#7030A0] hover:underline font-medium">
              Termo de Consentimento
            </Link>
            <span className="text-gray-300">•</span>
            <Link href="/" className="text-[#7030A0] hover:underline font-medium">
              Página Inicial
            </Link>
          </div>
        </div>
      </div>

      {/* Print styles */}
      <style jsx global>{`
        @media print {
          .sticky { display: none !important; }
          .no-print { display: none !important; }
          body { font-size: 11pt; color: #000; background: #fff; }
          .rounded-2xl { border: 1px solid #ddd; box-shadow: none; break-inside: avoid; }
        }
      `}</style>
    </div>
  );
}
