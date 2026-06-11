import React from 'react';
import { DocumentHeader } from '@/components/DocumentHeader';

describe('DocumentHeader Component', () => {
  const defaultProps = {
    documentTypeName: 'Contrato',
    objective: 'Criar contrato de prestação de serviços',
    onSaveObjective: jest.fn().mockResolvedValue(undefined),
  };

  it('renders document type name', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    expect(container.textContent).toContain('Contrato');
  });

  it('renders objective text', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    expect(container.textContent).toContain('Criar contrato de prestação de serviços');
  });

  it('renders blueprint name when provided', () => {
    const { container } = render(
      <DocumentHeader {...defaultProps} blueprintName="Modelo Padrão" />
    );
    expect(container.textContent).toContain('Modelo Padrão');
  });

  it('does not render separator when blueprintName is not provided', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    // Should only have one slash from "Objetivo:" label
    expect(container.textContent).not.toContain('//');
  });

  it('shows edit button with pencil icon initially', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    // In non-editing mode, there should be a button to start editing
    const editButton = container.querySelector('button');
    expect(editButton).toBeInTheDocument();
    // The pencil icon has h-3 w-3 classes
    const pencilIcon = container.querySelector('svg.lucide-pencil');
    expect(pencilIcon).toBeInTheDocument();
  });

  it('enters edit mode when clicking the objective', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    const editButton = container.querySelector('button')!;
    fireEvent.click(editButton);

    // Should now show input
    const input = container.querySelector('input');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('Criar contrato de prestação de serviços');
  });

  it('shows save and cancel buttons in edit mode', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    const editButton = container.querySelector('button')!;
    fireEvent.click(editButton);

    const checkIcon = container.querySelector('svg.lucide-check');
    const xIcon = container.querySelector('svg.lucide-x');
    expect(checkIcon).toBeInTheDocument();
    expect(xIcon).toBeInTheDocument();
  });

  it('calls onSaveObjective when saving', () => {
    const onSaveObjective = jest.fn().mockResolvedValue(undefined);
    const { container } = render(
      <DocumentHeader {...defaultProps} onSaveObjective={onSaveObjective} />
    );
    const editButton = container.querySelector('button')!;
    fireEvent.click(editButton);

    const input = container.querySelector('input')!;
    fireEvent.change(input, { target: { value: 'Novo objetivo' } });

    const saveButton = container.querySelector('svg.lucide-check')?.closest('button')!;
    fireEvent.click(saveButton);

    expect(onSaveObjective).toHaveBeenCalledWith('Novo objetivo');
  });

  it('cancels editing when clicking cancel button', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    const editButton = container.querySelector('button')!;
    fireEvent.click(editButton);

    const cancelButton = container.querySelector('svg.lucide-x')?.closest('button')!;
    fireEvent.click(cancelButton);

    // Should go back to display mode with original objective
    expect(container.textContent).toContain('Criar contrato de prestação de serviços');
    expect(container.querySelector('input')).not.toBeInTheDocument();
  });

  it('saves when pressing Enter key', () => {
    const onSaveObjective = jest.fn().mockResolvedValue(undefined);
    const { container } = render(
      <DocumentHeader {...defaultProps} onSaveObjective={onSaveObjective} />
    );
    const editButton = container.querySelector('button')!;
    fireEvent.click(editButton);

    const input = container.querySelector('input')!;
    fireEvent.change(input, { target: { value: 'Enter value' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onSaveObjective).toHaveBeenCalledWith('Enter value');
  });

  it('cancels when pressing Escape key', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    const editButton = container.querySelector('button')!;
    fireEvent.click(editButton);

    const input = container.querySelector('input')!;
    fireEvent.keyDown(input, { key: 'Escape' });

    // Should go back to display mode
    expect(container.querySelector('input')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <DocumentHeader {...defaultProps} className="custom-header" />
    );
    const div = container.firstElementChild as HTMLElement;
    expect(div).toHaveClass('custom-header');
  });

  it('shows FileText icon', () => {
    const { container } = render(<DocumentHeader {...defaultProps} />);
    const fileTextIcon = container.querySelector('svg.lucide-file-text');
    expect(fileTextIcon).toBeInTheDocument();
  });
});
