import React from 'react';
import { UploadPhase } from '@/components/phases/UploadPhase';

describe('UploadPhase Component', () => {
  const defaultProps = {
    sessionDetail: null,
    isUploadingDocuments: false,
    dragActive: false,
    onDrag: jest.fn(),
    onDrop: jest.fn().mockResolvedValue(undefined),
    onFileSelect: jest.fn().mockResolvedValue(undefined),
    onDeleteDocument: jest.fn(),
    onAdvance: jest.fn(),
    formatFileSize: (bytes: number) => `${(bytes / 1024).toFixed(1)} KB`,
  };

  it('renders upload drop zone', () => {
    const { container } = render(<UploadPhase {...defaultProps} />);
    expect(container.textContent).toContain('Arraste arquivos ou clique para enviar');
    expect(container.textContent).toContain('Selecionar Arquivos');
  });

  it('shows supported formats', () => {
    const { container } = render(<UploadPhase {...defaultProps} />);
    expect(container.textContent).toContain('PDF, DOCX, TXT ou ODT');
  });

  it('renders file input with correct accept attributes', () => {
    const { container } = render(<UploadPhase {...defaultProps} />);
    const input = container.querySelector('input[type="file"]');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('accept', '.pdf,.docx,.txt,.odt');
    expect(input).toHaveAttribute('multiple');
    expect(input).toHaveClass('hidden');
  });

  it('shows uploading state when isUploadingDocuments is true', () => {
    const { container } = render(
      <UploadPhase {...defaultProps} isUploadingDocuments={true} />
    );
    expect(container.textContent).toContain('Enviando documentos...');
    const spinner = container.querySelector('svg.lucide-loader-2');
    expect(spinner).toBeInTheDocument();
  });

  it('disables upload button while uploading', () => {
    const { container } = render(
      <UploadPhase {...defaultProps} isUploadingDocuments={true} />
    );
    const selectButton = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Selecionar Arquivos')
    );
    expect(selectButton).toBeDisabled();
  });

  it('applies dragActive styles', () => {
    const { container } = render(
      <UploadPhase {...defaultProps} dragActive={true} />
    );
    const dropZone = container.querySelector('.border-dashed');
    expect(dropZone).toHaveClass('border-primary');
    expect(dropZone).toHaveClass('bg-primary/5');
  });

  it('renders uploaded documents when sessionDetail has documents', () => {
    const props = {
      ...defaultProps,
      sessionDetail: {
        id: 'session-1',
        uploaded_documents: [
          { id: 'doc-1', filename: 'contrato.pdf', size: 1024, status: 'completed', uploaded_at: '2025-01-01T00:00:00Z' },
          { id: 'doc-2', filename: 'anexo.docx', size: 2048, status: 'pending', uploaded_at: '2025-01-01T00:00:00Z' },
        ],
      },
    };
    const { container } = render(<UploadPhase {...props} />);
    expect(container.textContent).toContain('Documentos Enviados (2)');
    expect(container.textContent).toContain('contrato.pdf');
    expect(container.textContent).toContain('anexo.docx');
  });

  it('shows document size formatted', () => {
    const props = {
      ...defaultProps,
      sessionDetail: {
        id: 'session-1',
        uploaded_documents: [
          { id: 'doc-1', filename: 'doc.pdf', size: 2048, status: 'completed', uploaded_at: '2025-01-01T00:00:00Z' },
        ],
      },
    };
    const { container } = render(<UploadPhase {...props} />);
    expect(container.textContent).toContain('2.0 KB');
  });

  it('shows status badge for each document', () => {
    const props = {
      ...defaultProps,
      sessionDetail: {
        id: 'session-1',
        uploaded_documents: [
          { id: 'doc-1', filename: 'doc.pdf', size: 1024, status: 'completed', uploaded_at: '2025-01-01T00:00:00Z' },
        ],
      },
    };
    const { container } = render(<UploadPhase {...props} />);
    expect(container.textContent).toContain('completed');
  });

  it('calls onDeleteDocument when delete button is clicked', () => {
    const onDeleteDocument = jest.fn();
    const props = {
      ...defaultProps,
      sessionDetail: {
        id: 'session-1',
        uploaded_documents: [
          { id: 'doc-1', filename: 'doc.pdf', size: 1024, status: 'completed', uploaded_at: '2025-01-01T00:00:00Z' },
        ],
      },
      onDeleteDocument,
    };
    const { container } = render(<UploadPhase {...props} />);
    const deleteBtn = container.querySelector('svg.lucide-trash-2')?.closest('button')!;
    fireEvent.click(deleteBtn);
    expect(onDeleteDocument).toHaveBeenCalledWith('doc-1');
  });

  it('shows advance button when documents exist', () => {
    const props = {
      ...defaultProps,
      sessionDetail: {
        id: 'session-1',
        uploaded_documents: [
          { id: 'doc-1', filename: 'doc.pdf', size: 1024, status: 'completed', uploaded_at: '2025-01-01T00:00:00Z' },
        ],
      },
    };
    const { container } = render(<UploadPhase {...props} />);
    expect(container.textContent).toContain('Avançar para Geração');
  });

  it('calls onAdvance when advance button is clicked', () => {
    const onAdvance = jest.fn();
    const props = {
      ...defaultProps,
      sessionDetail: {
        id: 'session-1',
        uploaded_documents: [
          { id: 'doc-1', filename: 'doc.pdf', size: 1024, status: 'completed', uploaded_at: '2025-01-01T00:00:00Z' },
        ],
      },
      onAdvance,
    };
    const { container } = render(<UploadPhase {...props} />);
    const advanceBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Avançar para Geração')
    )!;
    fireEvent.click(advanceBtn);
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });

  it('does not show advance button when no documents', () => {
    const { container } = render(<UploadPhase {...defaultProps} />);
    expect(container.textContent).not.toContain('Avançar para Geração');
  });

  it('triggers file input click when select button is clicked', () => {
    const { container } = render(<UploadPhase {...defaultProps} />);
    const fileInput = container.querySelector('input[type="file"]')!;
    const clickSpy = jest.spyOn(fileInput, 'click');
    const selectBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Selecionar Arquivos')
    )!;
    fireEvent.click(selectBtn);
    expect(clickSpy).toHaveBeenCalled();
  });

  it('applies custom className', () => {
    const { container } = render(
      <UploadPhase {...defaultProps} className="custom-phase" />
    );
    const outerDiv = container.firstElementChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-phase');
  });
});
