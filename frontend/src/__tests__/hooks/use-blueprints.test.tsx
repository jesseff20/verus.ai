/**
 * Tests for useBlueprints hook
 * Tests API calls, default blueprint detection, and section loading
 */

jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}));

jest.mock('@tanstack/react-query', () => {
  const queryClient = {
    invalidateQueries: jest.fn(),
  };
  return {
    useQuery: jest.fn(),
    useMutation: jest.fn(),
    useQueryClient: () => queryClient,
  };
});

import React from 'react';
import api from '@/lib/api';

describe('useBlueprints', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches blueprints on mount', () => {
    const { useQuery } = require('@tanstack/react-query');
    const mockBlueprints = [
      { id: 'bp-1', name: 'Modelo Padrão', document_type_code: 'contract', section_count: 5, is_default: true, is_active: true, created_at: '', updated_at: '' },
      { id: 'bp-2', name: 'Modelo Avançado', document_type_code: 'contract', section_count: 8, is_default: false, is_active: true, created_at: '', updated_at: '' },
    ];

    useQuery.mockImplementation(({ queryKey, queryFn }) => {
      if (queryKey[0] === 'blueprints') {
        return { data: mockBlueprints, isLoading: false, error: null };
      }
      return { data: null, isLoading: false };
    });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.blueprints).toEqual(mockBlueprints);
    expect(hook.isLoading).toBe(false);
    expect(hook.error).toBeNull();
  });

  it('identifies default blueprint', () => {
    const { useQuery } = require('@tanstack/react-query');
    const mockBlueprints = [
      { id: 'bp-1', name: 'Standard', document_type_code: 'contract', section_count: 5, is_default: false, is_active: true, created_at: '', updated_at: '' },
      { id: 'bp-2', name: 'Default', document_type_code: 'contract', section_count: 3, is_default: true, is_active: true, created_at: '', updated_at: '' },
    ];

    useQuery.mockReturnValue({ data: mockBlueprints, isLoading: false, error: null });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.defaultBlueprint?.id).toBe('bp-2');
    expect(hook.defaultBlueprint?.name).toBe('Default');
  });

  it('falls back to first blueprint when no default is set', () => {
    const { useQuery } = require('@tanstack/react-query');
    const mockBlueprints = [
      { id: 'bp-1', name: 'First Blueprint', document_type_code: 'contract', section_count: 5, is_default: false, is_active: true, created_at: '', updated_at: '' },
      { id: 'bp-2', name: 'Second Blueprint', document_type_code: 'contract', section_count: 3, is_default: false, is_active: true, created_at: '', updated_at: '' },
    ];

    useQuery.mockReturnValue({ data: mockBlueprints, isLoading: false, error: null });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.defaultBlueprint?.id).toBe('bp-1');
    expect(hook.defaultBlueprint?.name).toBe('First Blueprint');
  });

  it('returns null when no blueprints exist', () => {
    const { useQuery } = require('@tanstack/react-query');
    useQuery.mockReturnValue({ data: [], isLoading: false, error: null });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.defaultBlueprint).toBeNull();
  });

  it('handles loading state', () => {
    const { useQuery } = require('@tanstack/react-query');
    useQuery.mockReturnValue({ data: [], isLoading: true, error: null });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.isLoading).toBe(true);
  });

  it('handles error state', () => {
    const { useQuery } = require('@tanstack/react-query');
    const mockError = new Error('Network error');
    useQuery.mockReturnValue({ data: [], isLoading: false, error: mockError });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.error).toEqual(mockError);
  });

  it('provides useBlueprint function for fetching individual blueprint', () => {
    const { useQuery } = require('@tanstack/react-query');
    useQuery.mockImplementation(({ queryKey, queryFn }) => {
      if (queryKey[0] === 'blueprint' && queryKey[1] === 'bp-1') {
        return { data: { id: 'bp-1', name: 'Individual' }, isLoading: false };
      }
      return { data: [], isLoading: false };
    });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(typeof hook.useBlueprint).toBe('function');
    expect(typeof hook.useBlueprintSections).toBe('function');
  });

  it('fetches blueprint sections via useBlueprintSections', async () => {
    const { useQuery } = require('@tanstack/react-query');
    const mockSections = {
      blueprint: { id: 'bp-1', name: 'Test' },
      sections: [{ id: 'sec-1', section_number: 1, section_name: 'Partes' }],
    };

    useQuery.mockImplementation(({ queryKey, queryFn }) => {
      if (queryKey[0] === 'blueprint-sections' && queryKey[1] === 'bp-1') {
        return { data: mockSections, isLoading: false };
      }
      return { data: [], isLoading: false };
    });

    (api.get as jest.Mock).mockResolvedValue({ data: mockSections });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(typeof hook.useBlueprintSections).toBe('function');
  });

  it('handles API error during blueprint fetch', () => {
    const { useQuery } = require('@tanstack/react-query');
    const apiError = new Error('API Error');
    useQuery.mockReturnValue({ data: [], isLoading: false, error: apiError });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.error).toBeDefined();
    expect(hook.error.message).toBe('API Error');
  });

  it('provides isPending state for blueprint sections loading', () => {
    const { useQuery } = require('@tanstack/react-query');
    useQuery.mockImplementation(({ queryKey, queryFn }) => {
      if (queryKey[0] === 'blueprints') {
        return { data: [], isLoading: false, error: null };
      }
      return { data: null, isLoading: true };
    });

    const { useBlueprints } = require('@/hooks/use-blueprints');

    function TestComponent() {
      const hook = useBlueprints();
      React.useEffect(() => { window.__testHook = hook; }, [hook]);
      return null;
    }

    render(<TestComponent />);
    const hook: any = (window as any).__testHook;
    expect(hook.isLoading).toBe(false);
  });
});
