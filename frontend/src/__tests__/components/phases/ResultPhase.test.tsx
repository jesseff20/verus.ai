import React from 'react';
import { ResultPhase } from '@/components/phases/ResultPhase';

describe('ResultPhase Component', () => {
  const baseProps = {
    generatedContent: {
      section_01: 'Conteúdo da parte 1',
      section_02: 'Conteúdo do objeto',
    },
    sectionNames: { 1: 'Partes', 2: 'Objeto' },
    approvalStatus: { 1: 'approved', 2: 'improved' } as Record<number, any>,
    generationMetadata: {
      total_tokens_used: 1500,
      valid_sections: 2,
      average_score: 82,
      generation_time: 30,
      document_id: 'doc-1',
      generation_session_id: 'gen-1',
    },
    documentTypeName: 'Contrato',
    sessionObjective: 'Criar contrato de prestação de serviços advocatícios',
    pdfStatus: 'none' as const,
    onGeneratePdf: jest.fn().mockResolvedValue(undefined),
    docxStatus: 'none' as const,
    onGenerateDocx: jest.fn().mockResolvedValue(undefined),
    odtStatus: 'none' as const,
    onGenerateOdt: jest.fn().mockResolvedValue(undefined),
    onCopyToClipboard: jest.fn().mockResolvedValue(undefined),
    sessionId: 'session-1',
    documentTypeCode: 'contract',
    className: '',
  };

  it('renders document generated header', () => {
    const { container } = render(<ResultPhase {...baseProps} />);
    expect(container.textContent).toContain('Documento Gerado');
  });

  it('shows document type name and objective', () => {
    const { container } = render(<ResultPhase {...baseProps} />);
    expect(container.textContent).toContain('Contrato');
    expect(container.textContent).toContain('Criar contrato de prestação de serviços advocatícios');
  });

  it('renders summary stats', () => {
    const { container } = render(<ResultPhase {...baseProps} />);
    expect(container.textContent).toContain('1'); // approved
    expect(container.textContent).toContain('Aprovadas');
    expect(container.textContent).toContain('1'); // improved
    expect(container.textContent).toContain('Melhoradas');
    expect(container.textContent).toContain('2'); // total sections
    expect(container.textContent).toContain('Seções Totais');
    expect(container.textContent).toContain('82%');
    expect(container.textContent).toContain('Score Geral');
  });

  it('renders export section', () => {
    const { container } = render(<ResultPhase {...baseProps} />);
    expect(container.textContent).toContain('Exportar Documento');
  });

  it('renders format buttons: PDF, DOCX, ODT, Copiar', () => {
    const { container } = render(<ResultPhase {...baseProps} />);
    expect(container.textContent).toContain('PDF');
    expect(container.textContent).toContain('DOCX');
    expect(container.textContent).toContain('ODT');
    expect(container.textContent).toContain('Copiar');
  });

  it('calls onGeneratePdf when PDF button is clicked', () => {
    const onGeneratePdf = jest.fn().mockResolvedValue(undefined);
    const { container } = render(
      <ResultPhase {...baseProps} onGeneratePdf={onGeneratePdf} />
    );
    const pdfBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'PDF'
    )!;
    fireEvent.click(pdfBtn);
    expect(onGeneratePdf).toHaveBeenCalledTimes(1);
  });

  it('calls onGenerateDocx when DOCX button is clicked', () => {
    const onGenerateDocx = jest.fn().mockResolvedValue(undefined);
    const { container } = render(
      <ResultPhase {...baseProps} onGenerateDocx={onGenerateDocx} />
    );
    const docxBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'DOCX'
    )!;
    fireEvent.click(docxBtn);
    expect(onGenerateDocx).toHaveBeenCalledTimes(1);
  });

  it('calls onGenerateOdt when ODT button is clicked', () => {
    const onGenerateOdt = jest.fn().mockResolvedValue(undefined);
    const { container } = render(
      <ResultPhase {...baseProps} onGenerateOdt={onGenerateOdt} />
    );
    const odtBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'ODT'
    )!;
    fireEvent.click(odtBtn);
    expect(onGenerateOdt).toHaveBeenCalledTimes(1);
  });

  it('calls onCopyToClipboard when Copiar button is clicked', () => {
    const onCopyToClipboard = jest.fn().mockResolvedValue(undefined);
    const { container } = render(
      <ResultPhase {...baseProps} onCopyToClipboard={onCopyToClipboard} />
    );
    const copyBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Copiar')
    )!;
    fireEvent.click(copyBtn);
    expect(onCopyToClipboard).toHaveBeenCalledTimes(1);
  });

  it('shows "Gerando..." when pdfStatus is generating', () => {
    const props = {
      ...baseProps,
      pdfStatus: 'generating' as const,
    };
    const { container } = render(<ResultPhase {...props} />);
    expect(container.textContent).toContain('Gerando...');
  });

  it('shows "Baixar" when pdfStatus is ready', () => {
    const props = {
      ...baseProps,
      pdfStatus: 'ready' as const,
    };
    const { container } = render(<ResultPhase {...props} />);
    expect(container.textContent).toContain('Baixar');
  });

  it('renders document preview section', () => {
    const { container } = render(<ResultPhase {...baseProps} />);
    expect(container.textContent).toContain('Pré-visualização');
    expect(container.textContent).toContain('1. Partes');
    expect(container.textContent).toContain('2. Objeto');
  });

  it('shows section content in preview', () => {
    const { container } = render(<ResultPhase {...baseProps} />);
    expect(container.textContent).toContain('Conteúdo da parte 1');
    expect(container.textContent).toContain('Conteúdo do objeto');
  });

  it('shows "Sem conteúdo." for empty section content', () => {
    const props = {
      ...baseProps,
      generatedContent: {
        section_01: '',
      },
      sectionNames: { 1: 'Partes' },
    };
    const { container } = render(<ResultPhase {...props} />);
    expect(container.textContent).toContain('Sem conteúdo.');
  });

  it('disables export buttons when generating', () => {
    const props = {
      ...baseProps,
      pdfStatus: 'generating' as const,
    };
    const { container } = render(<ResultPhase {...props} />);
    const pdfBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('PDF') || b.textContent?.includes('Gerando...')
    );
    expect(pdfBtn).toBeDisabled();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ResultPhase {...baseProps} className="custom-phase" />
    );
    const outerDiv = container.firstElementChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-phase');
  });
});
