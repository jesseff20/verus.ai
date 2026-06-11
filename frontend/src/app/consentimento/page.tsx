'use client';

import Link from 'next/link';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  FileSignature,
  ChevronLeft,
  Download,
  Printer,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ClipboardList,
  FileText,
  History,
  UserCheck,
  HelpCircle,
  BookOpen,
  ArrowRight,
  CheckSquare,
  PenTool,
  Scale,
} from 'lucide-react';

export default function ConsentimentoPage() {
  const lastUpdate = '15 de janeiro de 2026';

  const handlePrint = () => window.print();

  const finalidades = [
    {
      id: 'prestacao-servicos',
      titulo: 'Prestação dos serviços contratados',
      descricao:
        'Para viabilizar a utilização da plataforma Verus.AI, incluindo: geração de peças processuais, gestão de casos, comunicação com clientes, armazenamento de documentos jurídicos e integração com sistemas de tribunais e assinatura digital.',
      essencial: true,
    },
    {
      id: 'comunicacao',
      titulo: 'Comunicação e suporte',
      descricao:
        'Para enviar comunicações operacionais (notificações de prazos, atualizações processuais, confirmações de agendamento) e prestar suporte técnico e jurídico.',
      essencial: true,
    },
    {
      id: 'conformidade-legal',
      titulo: 'Cumprimento de obrigações legais',
      descricao:
        'Para atender obrigações fiscais, contábeis, regulatórias e éticas do exercício da advocacia, incluindo obrigações perante a OAB e o Poder Judiciário.',
      essencial: true,
    },
    {
      id: 'melhoria',
      titulo: 'Melhoria dos serviços e treinamento de IA',
      descricao:
        'Para analisar o uso da plataforma, realizar testes A/B, treinar e aprimorar os modelos de inteligência artificial do Verus.AI com dados anonimizados.',
      essencial: false,
    },
    {
      id: 'marketing',
      titulo: 'Marketing e newsletters',
      descricao:
        'Para enviar conteúdo institucional, novidades sobre a plataforma, convites para eventos e webinars, e comunicações promocionais.',
      essencial: false,
    },
    {
      id: 'compartilhamento',
      titulo: 'Compartilhamento com parceiros estratégicos',
      descricao:
        'Para compartilhar dados com parceiros identificados (ex.: IBM, provedores de assinatura digital) para fins de integração e melhoria de serviços.',
      essencial: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-purple-50/30">
      {/* ── Top bar ── */}
      <div className="sticky top-0 z-40 border-b border-purple-100/80 bg-white/90 backdrop-blur-md no-print">
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
              <span className="hidden sm:inline">Download Termo (PDF)</span>
            </Button>
          </div>
        </div>
      </div>

      {/* ── Header ── */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-10 pb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7030A0]/10">
            <FileSignature className="h-5 w-5 text-[#7030A0]" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Termo de Consentimento — LGPD
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Última atualização: {lastUpdate}
            </p>
          </div>
        </div>

        <Card className="mt-6 border-2 border-[#7030A0]/20 bg-gradient-to-r from-[#7030A0]/5 to-purple-50/50">
          <CardContent className="p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-[#7030A0] shrink-0 mt-0.5" />
              <div className="text-sm text-gray-700 leading-relaxed">
                <strong>O que é consentimento?</strong> Nos termos do art. 5º, XII, da LGPD,
                o consentimento é a manifestação livre, informada e inequívoca pela qual o
                titular concorda com o tratamento de seus dados pessoais para uma finalidade
                determinada. Nesta página, explicamos detalhadamente cada finalidade de
                tratamento e solicitamos sua autorização de forma granular.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Content ── */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 pb-16 space-y-6">

        {/* 1. O que é Consentimento */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <HelpCircle className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                1. Definição de Consentimento
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                O consentimento é uma das bases legais para o tratamento de dados pessoais
                previstas no art. 7º da LGPD. Ele deve ser:
              </p>
              <ul className="mt-3 space-y-2">
                <li className="flex items-start gap-2 text-sm text-gray-600">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                  <span>
                    <strong>Livre:</strong> concedido sem coação ou pressão, podendo ser
                    recusado sem qualquer prejuízo para a prestação dos serviços essenciais.
                  </span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-600">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                  <span>
                    <strong>Informado:</strong> o titular conhece exatamente a finalidade do
                    tratamento, os dados envolvidos e as consequências da autorização.
                  </span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-600">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                  <span>
                    <strong>Inequívoco:</strong> manifestado de forma clara, por meio de
                    ação afirmativa (como marcar uma caixa de seleção), não podendo ser
                    presumido por omissão ou inação.
                  </span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-600">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                  <span>
                    <strong>Granular:</strong> o consentimento é solicitado separadamente
                    para cada finalidade, permitindo que o titular aceite umas e recuse
                    outras.
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* 2. Finalidades Específicas */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <CheckSquare className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                2. Finalidades Específicas do Tratamento
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                Abaixo, detalhamos cada finalidade para a qual solicitamos seu consentimento.
                As finalidades marcadas como <strong>"essenciais"</strong> são necessárias
                para o funcionamento da plataforma e têm base legal diversa do consentimento
                (execução de contrato ou obrigação legal). As demais dependem da sua
                autorização expressa.
              </p>

              <div className="space-y-3">
                {finalidades.map((f) => (
                  <div
                    key={f.id}
                    className={`rounded-xl border p-4 ${
                      f.essencial
                        ? 'border-green-200 bg-green-50/40'
                        : 'border-purple-100 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 flex-1 min-w-0">
                        {f.essencial ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                        ) : (
                          <PenTool className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                        )}
                        <div>
                          <p className="text-sm font-medium text-gray-800">
                            {f.titulo}
                            {f.essencial && (
                              <span className="ml-2 text-[10px] font-medium text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full">
                                Essencial
                              </span>
                            )}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">{f.descricao}</p>
                        </div>
                      </div>
                      {f.essencial ? (
                        <span className="text-[10px] font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded-full shrink-0">
                          Base legal: contrato
                        </span>
                      ) : (
                        <span className="text-[10px] font-medium text-[#7030A0] bg-[#7030A0]/10 px-2 py-0.5 rounded-full shrink-0">
                          Requer consentimento
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 3. Revogação */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <XCircle className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                3. Revogação do Consentimento
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Você pode revogar seu consentimento a qualquer momento, de forma gratuita
                e sem necessidade de justificativa. A revogação pode ser feita:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <ArrowRight className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    <strong>Diretamente no portal do cliente</strong> — na seção
                    "Privacidade e Dados Pessoais", você pode visualizar e revogar
                    consentimentos ativos.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ArrowRight className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    <strong>Por e-mail</strong> — enviando solicitação para{' '}
                    <a href="mailto:dpo@verus.ai" className="text-[#7030A0] font-medium hover:underline">
                      dpo@verus.ai
                    </a>
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ArrowRight className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    <strong>Por contato com o DPO</strong> — através dos canais oficiais
                    indicados na{' '}
                    <Link href="/privacidade" className="text-[#7030A0] font-medium hover:underline">
                      Política de Privacidade
                    </Link>.
                  </span>
                </li>
              </ul>
              <div className="mt-4 rounded-xl bg-amber-50 border border-amber-200 p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">Importante</p>
                    <p className="text-xs text-amber-700 mt-1">
                      A revogação do consentimento não afeta a legalidade do tratamento
                      realizado anteriormente com base no consentimento válido (art. 8º,
                      §5º, LGPD). Além disso, finalidades baseadas em outras hipóteses
                      legais (execução de contrato, obrigação legal) continuam sendo
                      realizadas independentemente da revogação.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 4. Consequências da Não Autorização */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <AlertCircle className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                4. Consequências da Não Autorização
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                A não autorização para finalidades não essenciais <strong>não impede</strong>{' '}
                a utilização da plataforma Verus.AI. No entanto, algumas funcionalidades
                podem ser impactadas:
              </p>
              <div className="mt-3 space-y-2">
                <div className="flex items-start gap-3 rounded-lg border border-gray-200 p-3">
                  <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center shrink-0">
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">Serviços essenciais mantidos</p>
                    <p className="text-xs text-gray-500">Geração de peças, gestão de casos, prazos, financeiro e portal do cliente continuam disponíveis integralmente.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-gray-200 p-3">
                  <div className="w-6 h-6 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                    <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">Funcionalidades limitadas</p>
                    <p className="text-xs text-gray-500">Sem consentimento para melhoria de IA, você não contribuirá com dados para o treinamento dos modelos (que usarão apenas dados anonimizados).</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-gray-200 p-3">
                  <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
                    <XCircle className="h-3.5 w-3.5 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">Serviços não disponíveis</p>
                    <p className="text-xs text-gray-500">Sem consentimento para marketing, você não receberá newsletters nem comunicações promocionais.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 5. Assinatura Digital */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <FileSignature className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                5. Assinatura Digital do Consentimento
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Quando você manifesta seu consentimento na plataforma Verus.AI, sua
                aceitação é registrada digitalmente com validade jurídica, conforme a
                Medida Provisória n.º 2.200-2/2001 (ICP-Brasil) e o art. 10, §2º, da LGPD.
              </p>
              <p className="text-sm text-gray-600 leading-relaxed mt-2">
                O processo de assinatura digital do consentimento funciona da seguinte forma:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    O sistema gera um <strong>hash criptográfico</strong> (SHA-256) do termo
                    de consentimento aceito, incluindo a versão, data e hora.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    O hash é <strong>assinado digitalmente</strong> com a chave privada do
                    Verus.AI, garantindo a integridade do documento.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    A assinatura, o hash e o timestamp são <strong>armazenados de forma segura</strong> no
                    banco de dados de auditoria, imutáveis e à prova de adulteração.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    O titular pode <strong>solicitar uma cópia</strong> do termo assinado a
                    qualquer momento, pelo portal ou pelo DPO.
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* 6. Registro de Auditoria */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <History className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                6. Registro de Auditoria do Consentimento
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Cada operação de consentimento (aceitação, revogação, alteração ou
                expiração) é registrada em nosso sistema de auditoria, conforme exige
                o art. 37 da LGPD e a política de boa prática de governança de dados.
              </p>

              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-purple-100">
                      <th className="text-left py-2 pr-3 font-medium text-gray-700">Campo</th>
                      <th className="text-left py-2 font-medium text-gray-700">Descrição</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-50">
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">id_consentimento</td>
                      <td className="py-2 text-gray-600">Identificador único universal (UUID)</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">id_titular</td>
                      <td className="py-2 text-gray-600">Identificador do titular (anonimizado)</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">finalidade</td>
                      <td className="py-2 text-gray-600">Finalidade específica do tratamento</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">acao</td>
                      <td className="py-2 text-gray-600">aceitação | revogação | alteração</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">versao_termo</td>
                      <td className="py-2 text-gray-600">Versão do termo de consentimento</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">timestamp</td>
                      <td className="py-2 text-gray-600">Data/hora com fuso horário (UTC-3)</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">hash_sha256</td>
                      <td className="py-2 text-gray-600">Hash criptográfico do termo aceito</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">ip_origem</td>
                      <td className="py-2 text-gray-600">Endereço IP da solicitação</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 text-gray-600 font-mono text-xs">user_agent</td>
                      <td className="py-2 text-gray-600">Navegador e sistema operacional</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                O registro de auditoria é mantido durante toda a relação contratual e por
                5 anos após o término, para fins de comprovação regulatória.
              </p>
            </div>
          </div>
        </div>

        {/* 7. Checklist Granular */}
        <div className="rounded-2xl border-2 border-[#7030A0]/20 bg-gradient-to-br from-[#7030A0]/5 to-purple-50/50 p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <ClipboardList className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                7. Checklist de Consentimento Granular
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                Conforme a melhor prática de governança e o art. 7º, I, da LGPD, o
                consentimento é solicitado de forma granular — você pode aceitar cada
                finalidade separadamente. Abaixo está o checklist que será apresentado
                no momento da solicitação:
              </p>

              <div className="space-y-2">
                {finalidades.filter((f) => !f.essencial).map((f) => (
                  <div
                    key={f.id}
                    className="flex items-start gap-3 rounded-xl bg-white border border-purple-100 p-4"
                  >
                    <div className="w-5 h-5 rounded border-2 border-[#7030A0]/40 flex items-center justify-center shrink-0 mt-0.5">
                      <div className="w-2.5 h-2.5 rounded-sm bg-transparent" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">{f.titulo}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{f.descricao}</p>
                    </div>
                  </div>
                ))}
                <p className="text-xs text-gray-400 italic mt-2">
                  * As finalidades essenciais (base legal: execução de contrato) não
                  dependem de consentimento, mas estão listadas para sua transparência.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 8. Seus Direitos */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <UserCheck className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                8. Seus Direitos como Titular
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Ao conceder ou recusar o consentimento, você mantém todos os direitos
                previstos no art. 18 da LGPD, incluindo:
              </p>
              <ul className="mt-2 space-y-1 text-sm text-gray-600 list-disc list-inside">
                <li>Solicitar a confirmação da existência de tratamento de dados;</li>
                <li>Acessar seus dados pessoais tratados;</li>
                <li>Solicitar a correção de dados incompletos, inexatos ou desatualizados;</li>
                <li>Solicitar a anonimização, bloqueio ou eliminação de dados desnecessários ou excessivos;</li>
                <li>Solicitar a portabilidade dos dados a outro fornecedor;</li>
                <li>Solicitar a eliminação de dados tratados com base no consentimento;</li>
                <li>Ser informado sobre a possibilidade de não fornecer consentimento e as consequências;</li>
                <li>Revogar o consentimento a qualquer momento.</li>
              </ul>
              <div className="mt-4">
                <Link
                  href="/privacidade"
                  className="inline-flex items-center gap-1.5 text-sm text-[#7030A0] font-medium hover:underline"
                >
                  Ver detalhes na Política de Privacidade
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>

        <Separator className="bg-purple-100" />

        {/* Footer */}
        <div className="text-center space-y-3">
          <p className="text-xs text-gray-400">
            Versão 1.0 — Última atualização: {lastUpdate}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
            <Link href="/privacidade" className="text-[#7030A0] hover:underline font-medium">
              Política de Privacidade
            </Link>
            <span className="text-gray-300">•</span>
            <Link href="/cookies" className="text-[#7030A0] hover:underline font-medium">
              Política de Cookies
            </Link>
            <span className="text-gray-300">•</span>
            <Link href="/" className="text-[#7030A0] hover:underline font-medium">
              Página Inicial
            </Link>
          </div>
        </div>
      </div>

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
