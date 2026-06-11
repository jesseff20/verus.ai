import React from 'react';
import { SessionSidebar } from '@/components/SessionSidebar';

describe('SessionSidebar Component', () => {
  const baseProps = {
    sessions: [],
    selectedSessionId: null,
    sessionDetail: null,
    isLoadingSessions: false,
    documentTypes: [{ code: 'contract', name: 'Contrato', description: 'Contrato legal' }],
    isLoadingDocumentTypes: false,
    documentTypeLabels: {} as Record<string, string>,
    allBlueprints: [],
    blueprints: [],
    wizardStep: 0,
    selectedDocumentType: '',
    selectedBlueprintId: '',
    newObjective: '',
    isCreatingSession: false,
    statusLabels: {} as Record<string, { label: string; variant: string }>,
    lucideIcons: {} as Record<string, React.ComponentType<any>>,
    documentDependencies: {} as Record<string, { code: string; label: string }[]>,
    parentSessionId: null,
    onParentSessionSelect: jest.fn(),
    onSelectSession: jest.fn(),
    onDeselectSession: jest.fn(),
    onSetWizardStep: jest.fn(),
    onSelectDocumentType: jest.fn(),
    onSelectBlueprint: jest.fn(),
    onObjectiveChange: jest.fn(),
    onCreateSession: jest.fn().mockResolvedValue(undefined),
    onDeleteSession: jest.fn(),
    formatDate: (date: string) => new Date(date).toLocaleDateString('pt-BR'),
  };

  it('renders "Nova Sessão" when no session selected', () => {
    const { container } = render(<SessionSidebar {...baseProps} />);
    expect(container.textContent).toContain('Nova Sessão');
  });

  it('renders "Sessão Ativa" when a session is selected', () => {
    const props = {
      ...baseProps,
      selectedSessionId: 'session-1',
      sessionDetail: {
        id: 'session-1',
        objective: 'Test objective',
        status: 'initialized',
        created_at: '2025-01-01T00:00:00Z',
        uploaded_documents: [],
      },
    };
    const { container } = render(<SessionSidebar {...props} />);
    expect(container.textContent).toContain('Sessão Ativa');
  });

  it('shows wizard step 0 (document types) by default', () => {
    const { container } = render(<SessionSidebar {...baseProps} />);
    expect(container.textContent).toContain('Tipo de Documento');
    expect(container.textContent).toContain('Contrato');
  });

  it('shows loading spinner when isLoadingDocumentTypes is true', () => {
    const { container } = render(
      <SessionSidebar {...baseProps} isLoadingDocumentTypes={true} />
    );
    const spinner = container.querySelector('svg.lucide-loader-2');
    expect(spinner).toBeInTheDocument();
  });

  it('shows wizard step 1 (blueprints) when wizardStep >= 1', () => {
    const props = {
      ...baseProps,
      wizardStep: 1,
      blueprints: [
        { id: 'bp-1', name: 'Modelo Padrão', document_type_code: 'contract', section_count: 5, is_default: true },
      ],
    };
    const { container } = render(<SessionSidebar {...props} />);
    expect(container.textContent).toContain('Modelo (Blueprint)');
    expect(container.textContent).toContain('Modelo Padrão');
  });

  it('shows empty state when no blueprints available', () => {
    const props = {
      ...baseProps,
      wizardStep: 1,
      blueprints: [],
    };
    const { container } = render(<SessionSidebar {...props} />);
    expect(container.textContent).toContain('Nenhum blueprint disponível');
  });

  it('shows wizard step 2 (objective) when wizardStep >= 2', () => {
    const props = {
      ...baseProps,
      wizardStep: 2,
    };
    const { container } = render(<SessionSidebar {...props} />);
    expect(container.textContent).toContain('Objetivo');
    const textarea = container.querySelector('textarea');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveAttribute('placeholder', 'Descreva o objetivo do documento...');
  });

  it('shows create session button with objective textarea', () => {
    const props = {
      ...baseProps,
      wizardStep: 2,
      newObjective: 'My document objective',
    };
    const { container } = render(<SessionSidebar {...props} />);
    expect(container.textContent).toContain('Criar Sessão');
  });

  it('disables create button when objective is empty', () => {
    const props = {
      ...baseProps,
      wizardStep: 2,
      newObjective: '',
    };
    const { container } = render(<SessionSidebar {...props} />);
    const createBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Criar Sessão')
    );
    expect(createBtn).toBeDisabled();
  });

  it('enables create button when objective is not empty', () => {
    const props = {
      ...baseProps,
      wizardStep: 2,
      newObjective: 'Create a contract',
    };
    const { container } = render(<SessionSidebar {...props} />);
    const createBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Criar Sessão')
    );
    expect(createBtn).toBeEnabled();
  });

  it('calls onCreateSession when create button is clicked', () => {
    const onCreateSession = jest.fn().mockResolvedValue(undefined);
    const props = {
      ...baseProps,
      wizardStep: 2,
      newObjective: 'Create a contract',
      onCreateSession,
    };
    const { container } = render(<SessionSidebar {...props} />);
    const createBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Criar Sessão')
    )!;
    fireEvent.click(createBtn);
    expect(onCreateSession).toHaveBeenCalledTimes(1);
  });

  it('shows loading spinner when isCreatingSession is true', () => {
    const props = {
      ...baseProps,
      wizardStep: 2,
      newObjective: 'Test',
      isCreatingSession: true,
    };
    const { container } = render(<SessionSidebar {...props} />);
    const spinner = container.querySelector('svg.lucide-loader-2');
    expect(spinner).toBeInTheDocument();
  });

  it('calls onSelectDocumentType when a document type is clicked', () => {
    const onSelectDocumentType = jest.fn();
    const props = {
      ...baseProps,
      onSelectDocumentType,
    };
    const { container } = render(<SessionSidebar {...props} />);
    const docTypeBtn = container.querySelector('button')!;
    fireEvent.click(docTypeBtn);
    expect(onSelectDocumentType).toHaveBeenCalledWith('contract');
  });

  it('highlights selected document type', () => {
    const props = {
      ...baseProps,
      selectedDocumentType: 'contract',
    };
    const { container } = render(<SessionSidebar {...props} />);
    const docTypeBtn = container.querySelector('button')!;
    expect(docTypeBtn).toHaveClass('border-primary');
  });

  it('shows "Voltar" button when session is selected', () => {
    const onDeselectSession = jest.fn();
    const props = {
      ...baseProps,
      selectedSessionId: 'session-1',
      sessionDetail: {
        id: 'session-1',
        objective: 'Test',
        status: 'initialized',
        created_at: '2025-01-01T00:00:00Z',
        uploaded_documents: [],
      },
      onDeselectSession,
    };
    const { container } = render(<SessionSidebar {...props} />);
    expect(container.textContent).toContain('Voltar');
  });

  it('calls onDeselectSession when Voltar is clicked', () => {
    const onDeselectSession = jest.fn();
    const props = {
      ...baseProps,
      selectedSessionId: 'session-1',
      sessionDetail: {
        id: 'session-1',
        objective: 'Test',
        status: 'initialized',
        created_at: '2025-01-01T00:00:00Z',
        uploaded_documents: [],
      },
      onDeselectSession,
    };
    const { container } = render(<SessionSidebar {...props} />);
    const voltarBtn = Array.from(container.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Voltar')
    )!;
    fireEvent.click(voltarBtn);
    expect(onDeselectSession).toHaveBeenCalledTimes(1);
  });

  it('shows delete button when session is selected', () => {
    const props = {
      ...baseProps,
      selectedSessionId: 'session-1',
      sessionDetail: {
        id: 'session-1',
        objective: 'Test',
        status: 'initialized',
        created_at: '2025-01-01T00:00:00Z',
        uploaded_documents: [],
      },
    };
    const { container } = render(<SessionSidebar {...props} />);
    expect(container.textContent).toContain('Excluir Sessão');
  });

  it('applies custom className', () => {
    const { container } = render(
      <SessionSidebar {...baseProps} className="custom-sidebar" />
    );
    const outerDiv = container.firstElementChild as HTMLElement;
    expect(outerDiv).toHaveClass('custom-sidebar');
  });
});
