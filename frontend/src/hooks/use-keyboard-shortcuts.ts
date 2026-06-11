'use client';

import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface KeyboardShortcutConfig {
  // Callbacks para ações
  onNew?: () => void;
  onSave?: () => void;
  onPrint?: () => void;
  onSaveAndClose?: () => void;
  onSearch?: () => void;
  onHelp?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onDelete?: () => void;
  onEdit?: () => void;

  // Habilitar/desabilitar atalhos específicos
  enableGlobalShortcuts?: boolean;
  enableFormShortcuts?: boolean;
  enableNavigationShortcuts?: boolean;
}

/**
 * Hook para atalhos de teclado globais do Verus.AI
 *
 * Atalhos implementados:
 * - N: Novo documento/caso
 * - Ctrl+S / Cmd+S: Salvar
 * - Ctrl+P / Cmd+P: Imprimir
 * - Ctrl+Shift+S / Cmd+Shift+S: Salvar e fechar
 * - Ctrl+/ / Cmd+/: Ajuda
 * - Ctrl+K / Cmd+K: Buscar (search palette)
 * - Esc: Fechar modal/drawer
 * - Ctrl+Z / Cmd+Z: Desfazer
 * - Ctrl+Y / Cmd+Y: Refazer
 * - Delete: Deletar (com confirmação)
 * - E: Editar
 */
export function useKeyboardShortcuts(config: KeyboardShortcutConfig = {}) {
  const router = useRouter();

  const {
    onNew,
    onSave,
    onPrint,
    onSaveAndClose,
    onSearch,
    onHelp,
    onUndo,
    onRedo,
    onDelete,
    onEdit,
    enableGlobalShortcuts = true,
    enableFormShortcuts = true,
    enableNavigationShortcuts = true,
  } = config;

  // Handler principal de teclado
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const { key, ctrlKey, metaKey, shiftKey, altKey } = event;
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const modKey = isMac ? metaKey : ctrlKey;

    // Ignorar se estiver em input/textarea
    const target = event.target as HTMLElement;
    const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

    // Atalhos globais (funcionam mesmo em inputs)
    if (enableGlobalShortcuts) {
      // Ctrl+P / Cmd+P: Imprimir
      if (modKey && key === 'p' && !shiftKey && !altKey) {
        event.preventDefault();
        onPrint?.();
        window.print();
        return;
      }

      // Ctrl+/ / Cmd+/: Ajuda
      if (modKey && key === '/' && !shiftKey && !altKey) {
        event.preventDefault();
        onHelp?.();
        return;
      }

      // Ctrl+K / Cmd+K: Search palette
      if (modKey && key === 'k' && !shiftKey && !altKey) {
        event.preventDefault();
        onSearch?.();
        return;
      }

      // Esc: Fechar modal (nativo do browser, mas podemos interceptar)
      if (key === 'Escape') {
        // Deixar o browser lidar nativamente
        return;
      }
    }

    // Atalhos de formulário (não funcionam em inputs)
    if (enableFormShortcuts && !isInput) {
      // Ctrl+S / Cmd+S: Salvar
      if (modKey && key === 's' && !shiftKey && !altKey) {
        event.preventDefault();
        onSave?.();
        return;
      }

      // Ctrl+Shift+S / Cmd+Shift+S: Salvar e fechar
      if (modKey && shiftKey && key === 's') {
        event.preventDefault();
        onSaveAndClose?.();
        return;
      }

      // Ctrl+Z / Cmd+Z: Desfazer
      if (modKey && key === 'z' && !shiftKey && !altKey) {
        event.preventDefault();
        onUndo?.();
        return;
      }

      // Ctrl+Y / Cmd+Y: Refazer
      if (modKey && key === 'y' && !shiftKey && !altKey) {
        event.preventDefault();
        onRedo?.();
        return;
      }

      // Ctrl+Shift+Y / Cmd+Shift+Y: Refazer (alternativo)
      if (modKey && shiftKey && key === 'z') {
        event.preventDefault();
        onRedo?.();
        return;
      }
    }

    // Atalhos de navegação e ação (não funcionam em inputs)
    if (enableNavigationShortcuts && !isInput) {
      // N: Novo
      if (key === 'n' && !modKey && !shiftKey && !altKey) {
        event.preventDefault();
        onNew?.();
        return;
      }

      // Delete: Deletar
      if (key === 'Delete' && !modKey && !shiftKey && !altKey) {
        event.preventDefault();
        onDelete?.();
        return;
      }

      // E: Editar
      if (key === 'e' && !modKey && !shiftKey && !altKey) {
        event.preventDefault();
        onEdit?.();
        return;
      }
    }
  }, [
    enableGlobalShortcuts,
    enableFormShortcuts,
    enableNavigationShortcuts,
    onNew,
    onSave,
    onPrint,
    onSaveAndClose,
    onSearch,
    onHelp,
    onUndo,
    onRedo,
    onDelete,
    onEdit,
  ]);

  // Registrar listener
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // Função utilitária para mostrar atalhos no UI
  const getShortcutLabel = useCallback((action: string) => {
    const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const mod = isMac ? '⌘' : 'Ctrl';

    const shortcuts: Record<string, string> = {
      new: 'N',
      save: `${mod}+S`,
      print: `${mod}+P`,
      saveAndClose: `${mod}+⇧+S`,
      search: `${mod}+K`,
      help: `${mod}+/`,
      undo: `${mod}+Z`,
      redo: `${mod}+Y`,
      delete: 'Del',
      edit: 'E',
    };

    return shortcuts[action] || '';
  }, []);

  return {
    getShortcutLabel,
  };
}

/**
 * Hook para registrar atalhos de teclado condicionais
 * Só ativa quando uma condição é verdadeira
 */
export function useConditionalShortcut(
  condition: boolean,
  shortcut: string,
  handler: () => void,
  options: { preventDefault?: boolean; allowInInput?: boolean } = {}
) {
  const { preventDefault = true, allowInInput = false } = options;

  useEffect(() => {
    if (!condition) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

      if (!allowInInput && isInput) return;

      // Parse shortcut (ex: "Ctrl+S", "N", "Shift+Delete")
      const parts = shortcut.toLowerCase().split('+');
      const key = parts[parts.length - 1];

      const needsCtrl = parts.includes('ctrl') || parts.includes('cmd');
      const needsShift = parts.includes('shift');
      const needsAlt = parts.includes('alt');

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? event.metaKey : event.ctrlKey;

      if (
        event.key.toLowerCase() === key &&
        (needsCtrl ? modKey : true) &&
        (needsShift ? event.shiftKey : !event.shiftKey) &&
        (needsAlt ? event.altKey : !event.altKey)
      ) {
        if (preventDefault) event.preventDefault();
        handler();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [condition, shortcut, handler, preventDefault, allowInInput]);
}
