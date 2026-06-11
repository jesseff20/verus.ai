/**
 * Validações de Dados Jurídicos Brasileiros
 *
 * Implementa validações para:
 * - Número de processo CNJ (14.133/2021)
 * - OAB (Ordem dos Advogados do Brasil)
 * - CPF (Cadastro de Pessoas Físicas)
 * - CNPJ (Cadastro Nacional da Pessoa Jurídica)
 * - Cálculo de prazos processuais
 */

// ========================================
// NÚMERO DE PROCESSO CNJ
// Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
// ========================================

export interface ProcessoCNJ {
  numero: string;
  sequencial: string;
  digitoVerificador: string;
  ano: string;
  orgao: string;
  tribunal: string;
  origem: string;
  valido: boolean;
  formatado: string;
}

/**
 * Valida e parseia número de processo CNJ
 *
 * @param numero - Número do processo (com ou sem formatação)
 * @returns Objeto com detalhes do processo ou null se inválido
 */
export function validarProcessoCNJ(numero: string): ProcessoCNJ | null {
  // Remove formatação (pontos, traços, espaços)
  const limpo = numero.replace(/[^0-9]/g, '');

  // CNJ tem 20 dígitos
  if (limpo.length !== 20) {
    return null;
  }

  // Parseia componentes
  const sequencial = limpo.substring(0, 7);
  const digitoVerificador = limpo.substring(7, 9);
  const ano = limpo.substring(9, 13);
  const orgao = limpo.substring(13, 14);
  const tribunal = limpo.substring(14, 16);
  const origem = limpo.substring(16, 20);

  // Valida ano (1900-2099)
  const anoNum = parseInt(ano, 10);
  if (anoNum < 1900 || anoNum > 2099) {
    return null;
  }

  // Valida órgão (0-9)
  if (orgao === '0' || parseInt(orgao, 10) > 9) {
    return null;
  }

  // Valida dígito verificador (regra módulo 97)
  const base = `${sequencial}${ano}${orgao}${tribunal}${origem}`;
  const dvCalculado = calcularDVProcesso(base);

  if (dvCalculado !== digitoVerificador) {
    return null;
  }

  // Formata no padrão CNJ
  const formatado = `${sequencial}-${digitoVerificador}.${ano}.${orgao}.${tribunal}.${origem}`;

  return {
    numero: limpo,
    sequencial,
    digitoVerificador,
    ano,
    orgao,
    tribunal,
    origem,
    valido: true,
    formatado,
  };
}

/**
 * Calcula dígito verificador do processo CNJ (módulo 97)
 */
function calcularDVProcesso(base: string): string {
  // Converte para número grande
  const num = BigInt(base);
  const resto = Number(num % 97n);
  const dv = 97 - resto;

  // Retorna com zero à esquerda se necessário
  return dv < 10 ? `0${dv}` : `${dv}`;
}

/**
 * Formata número de processo CNJ
 */
export function formatarProcessoCNJ(numero: string): string {
  const valido = validarProcessoCNJ(numero);
  return valido ? valido.formatado : numero;
}

// ========================================
// OAB (Ordem dos Advogados do Brasil)
// ========================================

export interface OABValida {
  numero: string;
  uf: string;
  valido: boolean;
  formatado: string;
}

const UF_OAB = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

/**
 * Valida número da OAB
 *
 * @param numero - Número da OAB (apenas números)
 * @param uf - UF da OAB
 * @returns Objeto com validação ou null
 */
export function validarOAB(numero: string, uf: string): OABValida | null {
  const ufUpper = uf.toUpperCase().trim();

  // Valida UF
  if (!UF_OAB.includes(ufUpper)) {
    return null;
  }

  // Remove formatação
  const limpo = numero.replace(/[^0-9]/g, '');

  // OAB tem 5-6 dígitos
  if (limpo.length < 5 || limpo.length > 6) {
    return null;
  }

  // Valida dígito verificador (módulo 11)
  const dvCalculado = calcularDVOAB(limpo.substring(0, limpo.length - 1));
  const dvInformado = limpo[limpo.length - 1];

  if (dvCalculado !== dvInformado) {
    return null;
  }

  const formatado = `${parseInt(limpo.substring(0, limpo.length - 1), 10).toString()}/${ufUpper}`;

  return {
    numero: limpo,
    uf: ufUpper,
    valido: true,
    formatado,
  };
}

/**
 * Calcula dígito verificador da OAB (módulo 11)
 */
function calcularDVOAB(base: string): string {
  const pesos = [8, 7, 6, 5, 4, 3, 2];
  let soma = 0;

  for (let i = 0; i < base.length; i++) {
    soma += parseInt(base[i], 10) * pesos[pesos.length - base.length + i];
  }

  const resto = soma % 11;
  const dv = resto < 2 ? 0 : 11 - resto;

  return dv.toString();
}

/**
 * Formata número da OAB
 */
export function formatarOAB(numero: string, uf: string): string {
  const valido = validarOAB(numero, uf);
  return valido ? valido.formatado : `${numero}/${uf.toUpperCase()}`;
}

// ========================================
// CPF (Cadastro de Pessoas Físicas)
// ========================================

/**
 * Valida CPF
 *
 * @param cpf - CPF (com ou sem formatação)
 * @returns true se válido
 */
export function validarCPF(cpf: string): boolean {
  const limpo = cpf.replace(/[^0-9]/g, '');

  // CPF tem 11 dígitos
  if (limpo.length !== 11) {
    return false;
  }

  // Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
  if (/^(\d)\1+$/.test(limpo)) {
    return false;
  }

  // Valida primeiro dígito verificador
  const dv1 = calcularDVCPF(limpo.substring(0, 9));
  if (dv1 !== limpo[9]) {
    return false;
  }

  // Valida segundo dígito verificador
  const dv2 = calcularDVCPF(limpo.substring(0, 10));
  if (dv2 !== limpo[10]) {
    return false;
  }

  return true;
}

/**
 * Calcula dígito verificador do CPF (módulo 11)
 */
function calcularDVCPF(base: string): string {
  let soma = 0;
  let peso = base.length + 1;

  for (let i = 0; i < base.length; i++) {
    soma += parseInt(base[i], 10) * peso;
    peso--;
  }

  const resto = soma % 11;
  const dv = resto < 2 ? 0 : 11 - resto;

  return dv.toString();
}

/**
 * Formata CPF
 */
export function formatarCPF(cpf: string): string {
  const limpo = cpf.replace(/[^0-9]/g, '');

  if (limpo.length !== 11) {
    return cpf;
  }

  return `${limpo.substring(0, 3)}.${limpo.substring(3, 6)}.${limpo.substring(6, 9)}-${limpo.substring(9)}`;
}

// ========================================
// CNPJ (Cadastro Nacional da Pessoa Jurídica)
// ========================================

/**
 * Valida CNPJ
 *
 * @param cnpj - CNPJ (com ou sem formatação)
 * @returns true se válido
 */
export function validarCNPJ(cnpj: string): boolean {
  const limpo = cnpj.replace(/[^0-9]/g, '');

  // CNPJ tem 14 dígitos
  if (limpo.length !== 14) {
    return false;
  }

  // Verifica se todos os dígitos são iguais
  if (/^(\d)\1+$/.test(limpo)) {
    return false;
  }

  // Valida primeiro dígito verificador
  const dv1 = calcularDVCNPJ(limpo.substring(0, 12), 5);
  if (dv1 !== limpo[12]) {
    return false;
  }

  // Valida segundo dígito verificador
  const dv2 = calcularDVCNPJ(limpo.substring(0, 13), 6);
  if (dv2 !== limpo[13]) {
    return false;
  }

  return true;
}

/**
 * Calcula dígito verificador do CNPJ (módulo 11)
 */
function calcularDVCNPJ(base: string, pesoInicial: number): string {
  let soma = 0;
  let peso = pesoInicial;

  for (let i = 0; i < base.length; i++) {
    soma += parseInt(base[i], 10) * peso;
    peso = peso === 2 ? 9 : peso - 1;
  }

  const resto = soma % 11;
  const dv = resto < 2 ? 0 : 11 - resto;

  return dv.toString();
}

/**
 * Formata CNPJ
 */
export function formatarCNPJ(cnpj: string): string {
  const limpo = cnpj.replace(/[^0-9]/g, '');

  if (limpo.length !== 14) {
    return cnpj;
  }

  return `${limpo.substring(0, 2)}.${limpo.substring(2, 5)}.${limpo.substring(5, 8)}/${limpo.substring(8, 12)}-${limpo.substring(12)}`;
}

// ========================================
// PRAZOS PROCESSUAIS
// ========================================

export interface PrazoProcessual {
  dataInicio: Date;
  diasUteis: number;
  dataFinal: Date;
  diasCorridos: number;
  feriadosNoPeriodo: Date[];
}

/**
 * Calcula prazo processual em dias úteis
 *
 * @param dataInicio - Data de início (inclusive)
 * @param diasUteis - Número de dias úteis
 * @param feriados - Lista de feriados (opcional)
 * @returns Objeto com datas do prazo
 */
export function calcularPrazoProcessual(
  dataInicio: Date,
  diasUteis: number,
  feriados: Date[] = []
): PrazoProcessual {
  let dataAtual = new Date(dataInicio);
  let diasContados = 0;
  const feriadosNoPeriodo: Date[] = [];

  while (diasContados < diasUteis) {
    // Avança um dia
    dataAtual.setDate(dataAtual.getDate() + 1);

    const diaSemana = dataAtual.getDay();

    // Verifica se é fim de semana (0 = domingo, 6 = sábado)
    if (diaSemana !== 0 && diaSemana !== 6) {
      // Verifica se é feriado
      const ehFeriado = feriados.some(
        feriado => feriado.toDateString() === dataAtual.toDateString()
      );

      if (ehFeriado) {
        feriadosNoPeriodo.push(new Date(dataAtual));
      } else {
        diasContados++;
      }
    }
  }

  // Calcula dias corridos
  const diasCorridos = Math.floor(
    (dataAtual.getTime() - dataInicio.getTime()) / (1000 * 60 * 60 * 24)
  );

  return {
    dataInicio,
    diasUteis,
    dataFinal: dataAtual,
    diasCorridos,
    feriadosNoPeriodo,
  };
}

/**
 * Verifica se uma data é dia útil
 */
export function isDiaUtil(data: Date): boolean {
  const diaSemana = data.getDay();
  return diaSemana !== 0 && diaSemana !== 6;
}

/**
 * Formata data para padrão brasileiro
 */
export function formatarDataBR(data: Date): string {
  return data.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/**
 * Formata data com hora para padrão brasileiro
 */
export function formatarDataHoraBR(data: Date): string {
  return data.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ========================================
// HOOKS REACT (para uso em componentes)
// ========================================

/**
 * Validação em tempo real para inputs
 *
 * @example
 * const validation = useLegalValidation('0001234-56.2025.8.26.0001', 'processo');
 * if (!validation.valid) { /* mostrar erro *\/ }
 */
export interface LegalValidationResult {
  valido: boolean;
  formatado: string;
  erro?: string;
}

export function validateLegalValue(
  value: string,
  type: 'processo' | 'cpf' | 'cnpj' | 'oab',
  uf?: string
): LegalValidationResult {
  switch (type) {
    case 'processo':
      const processo = validarProcessoCNJ(value);
      return {
        valido: !!processo,
        formatado: processo?.formatado || value,
        erro: processo ? undefined : 'Número de processo CNJ inválido',
      };

    case 'cpf':
      const cpfValido = validarCPF(value);
      return {
        valido: cpfValido,
        formatado: formatarCPF(value),
        erro: cpfValido ? undefined : 'CPF inválido',
      };

    case 'cnpj':
      const cnpjValido = validarCNPJ(value);
      return {
        valido: cnpjValido,
        formatado: formatarCNPJ(value),
        erro: cnpjValido ? undefined : 'CNPJ inválido',
      };

    case 'oab':
      if (!uf) {
        return { valido: false, formatado: value, erro: 'UF da OAB é obrigatória' };
      }
      const oab = validarOAB(value, uf);
      return {
        valido: !!oab,
        formatado: oab?.formatado || value,
        erro: oab ? undefined : `OAB/${uf} inválida`,
      };

    default:
      return { valido: false, formatado: value, erro: 'Tipo de validação desconhecido' };
  }
}
