import { cn, formatDate, formatDateTime, formatCPF, formatCNPJ, formatOAB, formatProcessNumber, formatCurrency, formatPhone, slugify, truncate } from '@/lib/utils';

describe('cn()', () => {
  it('merges Tailwind classes correctly', () => {
    expect(cn('px-4', 'px-2')).toBe('px-2');
  });

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible');
  });

  it('returns empty string for no inputs', () => {
    expect(cn()).toBe('');
  });

  it('handles undefined values', () => {
    expect(cn('text-sm', undefined, 'text-lg')).toBe('text-lg');
  });

  it('handles null values', () => {
    expect(cn('p-4', null, 'm-4')).toBe('p-4 m-4');
  });

  it('merges conflicting padding classes', () => {
    expect(cn('p-4', 'p-6')).toBe('p-6');
  });

  it('handles multiple class names', () => {
    expect(cn('flex', 'items-center', 'justify-between')).toBe('flex items-center justify-between');
  });
});

describe('formatDate()', () => {
  it('formats Date object to Brazilian locale', () => {
    const date = new Date(2025, 0, 15); // Jan 15, 2025
    expect(formatDate(date)).toBe('15/01/2025');
  });

  it('formats ISO string to Brazilian locale', () => {
    expect(formatDate('2025-06-01T10:00:00Z')).toBe('01/06/2025');
  });

  it('returns empty string for null', () => {
    expect(formatDate(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(formatDate(undefined)).toBe('');
  });

  it('handles date string without time', () => {
    expect(formatDate('2025-12-25')).toBe('25/12/2025');
  });
});

describe('formatDateTime()', () => {
  it('formats date with time', () => {
    const date = new Date(2025, 5, 1, 14, 30, 0);
    expect(formatDateTime(date)).toMatch(/\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}/);
  });

  it('formats ISO string with time', () => {
    const result = formatDateTime('2025-06-01T14:30:00Z');
    expect(result).toMatch(/\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}/);
  });

  it('returns empty string for null', () => {
    expect(formatDateTime(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(formatDateTime(undefined)).toBe('');
  });
});

describe('formatCPF()', () => {
  it('formats 11 digits to CPF pattern', () => {
    expect(formatCPF('12345678901')).toBe('123.456.789-01');
  });

  it('returns original value if not 11 digits', () => {
    expect(formatCPF('1234567890')).toBe('1234567890');
  });

  it('strips non-digit characters and formats', () => {
    expect(formatCPF('123.456.789-01')).toBe('123.456.789-01');
  });

  it('returns empty string for empty input', () => {
    expect(formatCPF('')).toBe('');
  });

  it('handles input with letters', () => {
    expect(formatCPF('abc12345678901def')).toBe('123.456.789-01');
  });
});

describe('formatCNPJ()', () => {
  it('formats 14 digits to CNPJ pattern', () => {
    expect(formatCNPJ('12345678000199')).toBe('12.345.678/0001-99');
  });

  it('returns original value if not 14 digits', () => {
    expect(formatCNPJ('12345678')).toBe('12345678');
  });

  it('strips non-digit characters', () => {
    expect(formatCNPJ('12.345.678/0001-99')).toBe('12.345.678/0001-99');
  });

  it('returns empty string for empty input', () => {
    expect(formatCNPJ('')).toBe('');
  });
});

describe('formatOAB()', () => {
  it('formats OAB number with UF', () => {
    expect(formatOAB('123456', 'SP')).toBe('123456/SP');
  });

  it('formats OAB number without UF', () => {
    expect(formatOAB('123456')).toBe('123456');
  });

  it('strips non-digit characters from number', () => {
    expect(formatOAB('123abc456', 'RJ')).toBe('123456/RJ');
  });

  it('converts UF to uppercase', () => {
    expect(formatOAB('123456', 'sp')).toBe('123456/SP');
  });

  it('returns digits only when no UF provided', () => {
    expect(formatOAB('abc123def456')).toBe('123456');
  });
});

describe('formatProcessNumber()', () => {
  it('formats 20 digits to CNJ pattern', () => {
    expect(formatProcessNumber('12345678920234016001')).toBe('1234567-89.2023.4.01.6001');
  });

  it('returns original value if not 20 digits', () => {
    expect(formatProcessNumber('1234567')).toBe('1234567');
  });

  it('strips non-digit characters', () => {
    expect(formatProcessNumber('1234567-89.2023.4.01.6001')).toBe('1234567-89.2023.4.01.6001');
  });

  it('returns empty string for empty input', () => {
    expect(formatProcessNumber('')).toBe('');
  });
});

describe('formatCurrency()', () => {
  it('formats number to BRL currency', () => {
    expect(formatCurrency(1500.50)).toBe('R$ 1.500,50');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('R$ 0,00');
  });

  it('formats null as R$ 0,00', () => {
    expect(formatCurrency(null)).toBe('R$ 0,00');
  });

  it('formats undefined as R$ 0,00', () => {
    expect(formatCurrency(undefined)).toBe('R$ 0,00');
  });

  it('parses string numbers', () => {
    expect(formatCurrency('2500')).toBe('R$ 2.500,00');
  });

  it('handles NaN strings', () => {
    expect(formatCurrency('abc')).toBe('R$ 0,00');
  });

  it('formats large numbers with thousands separator', () => {
    expect(formatCurrency(1000000)).toBe('R$ 1.000.000,00');
  });
});

describe('formatPhone()', () => {
  it('formats mobile phone (11 digits)', () => {
    expect(formatPhone('11987654321')).toBe('(11) 98765-4321');
  });

  it('formats landline phone (10 digits)', () => {
    expect(formatPhone('1134567890')).toBe('(11) 3456-7890');
  });

  it('returns original value for invalid length', () => {
    expect(formatPhone('12345')).toBe('12345');
  });

  it('strips non-digit characters', () => {
    expect(formatPhone('(11) 98765-4321')).toBe('(11) 98765-4321');
  });

  it('returns empty string for empty input', () => {
    expect(formatPhone('')).toBe('');
  });
});

describe('slugify()', () => {
  it('converts text to URL-friendly slug', () => {
    expect(slugify('Hello World')).toBe('hello-world');
  });

  it('removes accents', () => {
    expect(slugify('Criação de Contrato')).toBe('criacao-de-contrato');
  });

  it('handles multiple spaces and special chars', () => {
    expect(slugify('Teste   &   Especial!')).toBe('teste-especial');
  });

  it('removes leading and trailing hyphens', () => {
    expect(slugify('  hello world  ')).toBe('hello-world');
  });

  it('returns empty string for empty input', () => {
    expect(slugify('')).toBe('');
  });

  it('handles single word', () => {
    expect(slugify('Contrato')).toBe('contrato');
  });

  it('removes special characters', () => {
    expect(slugify('Preço: R$ 1.500,00')).toBe('preco-r-150000');
  });
});

describe('truncate()', () => {
  it('truncates text longer than maxLength', () => {
    expect(truncate('Hello World This Is Long', 10)).toBe('Hello Worl…');
  });

  it('returns full text if within maxLength', () => {
    expect(truncate('Short', 10)).toBe('Short');
  });

  it('returns empty string for empty input', () => {
    expect(truncate('', 10)).toBe('');
  });

  it('trims trailing spaces before ellipsis', () => {
    expect(truncate('Hello World    ', 10)).toBe('Hello Worl…');
  });

  it('handles exact length', () => {
    expect(truncate('Exactly 10', 10)).toBe('Exactly 10');
  });

  it('uses ellipsis character', () => {
    const result = truncate('This is a very long string that should be truncated', 20);
    expect(result).toMatch(/…$/);
    expect(result.length).toBeLessThanOrEqual(21); // 20 chars + ellipsis
  });
});
