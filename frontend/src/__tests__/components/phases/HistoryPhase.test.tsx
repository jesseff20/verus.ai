import React from 'react';
import { HistoryPhase } from '@/components/phases/HistoryPhase';

describe('HistoryPhase Component', () => {
  const baseProps = {
    sessionDetail: null,
    totalSections: 5,
    onLoadDocument: jest.fn().mockResolvedValue(undefined),
    onDeleteDocument: jest.fn(),
    className: '',
  };

  it('shows empty state when no documents', () => {
    const { container } = render(<HistoryPhase {...baseProps} />);
    expect(container.textContent).toContain('Nenhum Documento Gerado');
    expect(container.textContent).toContain('Os documentos gerados nesta sessão aparecerão aqui.');
  });

  it('shows history when documents exist', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato de Prestação',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    expect(container.textContent).toContain('Histórico de Documentos');
    expect(container.textContent).toContain('Contrato de Prestação');
  });

  it('shows "Documento sem título" when no title', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: '',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    expect(container.textContent).toContain('Documento sem título');
  });

  it('shows document type and section count', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    expect(container.textContent).toContain('Tipo: contract');
    expect(container.textContent).toContain('5 seções');
  });

  it('shows status badge', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    // Should show status badge with the label text
    // 'completed' maps to 'Concluído'
    const statusBadge = container.querySelector('[class*="badge"]') || container.querySelector('div[class*="rounded-full"]');
    expect(container.textContent).toContain('Concluído');
  });

  it('shows Visualizar button for each document', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    expect(container.textContent).toContain('Visualizar');
  });

  it('calls onLoadDocument when Visualizar is clicked', () => {
    const onLoadDocument = jest.fn().mockResolvedValue(undefined);
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
      onLoadDocument,
    };
    const { container } = render(<HistoryPhase {...props} />);
    const visualizarBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Visualizar')
    )!;
    fireEvent.click(visualizarBtn);
    expect(onLoadDocument).toHaveBeenCalledTimes(1);
  });

  it('shows delete button for each document', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    const trashIcon = container.querySelector('svg.lucide-trash-2');
    expect(trashIcon).toBeInTheDocument();
  });

  it('calls onDeleteDocument when delete button is clicked', () => {
    const onDeleteDocument = jest.fn();
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
      onDeleteDocument,
    };
    const { container } = render(<HistoryPhase {...props} />);
    const deleteBtn = container.querySelector('svg.lucide-trash-2')?.closest('button')!;
    fireEvent.click(deleteBtn);
    expect(onDeleteDocument).toHaveBeenCalledWith('doc-1');
  });

  it('shows download links when URLs are present', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
            pdf_url: '/media/doc.pdf',
            docx_url: '/media/doc.docx',
            odt_url: '/media/doc.odt',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    expect(container.textContent).toContain('PDF');
    expect(container.textContent).toContain('DOCX');
    expect(container.textContent).toContain('ODT');
    const links = container.querySelectorAll('a');
    expect(links.length).toBe(3);
    expect(links[0]).toHaveAttribute('href', '/media/doc.pdf');
    expect(links[0]).toHaveAttribute('target', '_blank');
  });

  it('does not show download links when URLs are not present', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-1',
            title: 'Contrato',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    const links = container.querySelectorAll('a');
    expect(links.length).toBe(0);
  });

  it('sorts documents by created_at descending', () => {
    const props = {
      ...baseProps,
      sessionDetail: {
        id: 'session-1',
        generated_documents: [
          {
            id: 'doc-2',
            title: 'Older',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-05-01T10:00:00Z',
            updated_at: '2025-05-01T12:00:00Z',
          },
          {
            id: 'doc-1',
            title: 'Newer',
            document_type: 'contract',
            status: 'completed',
            created_at: '2025-06-01T10:00:00Z',
            updated_at: '2025-06-01T12:00:00Z',
          },
        ],
      },
    };
    const { container } = render(<HistoryPhase {...props} />);
    // The "Newer" doc should appear before "Older" in DOM order
    const cards = container.querySelectorAll('[class*="card"]');
    const allText = container.textContent || '';
    const newerIndex = allText.indexOf('Newer');
    const olderIndex = allText.indexOf('Older');
    expect(newerIndex).toBeLessThan(olderIndex);
  });

  it('applies custom className', () => {
    const { container } = render(
      <HistoryPhase {...baseProps} className="custom-phase" />
    );
    const outerDiv = container.firstElementChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-phase');
  });
});
