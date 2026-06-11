'use client';

import { useRef, useState, KeyboardEvent, useEffect, useCallback } from 'react';
import { Paperclip, Send, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { FileAttachment } from './FileAttachment';
import { AgentMentionDropdown, AgentMentionOption } from './AgentMentionDropdown';
import { toast } from 'sonner';

const MAX_ATTACH_SIZE = 50 * 1024 * 1024; // 50 MB

interface ChatInputProps {
  onSend: (message: string) => void;
  onAttach: (file: File | null) => void;
  onStop: () => void;
  isStreaming: boolean;
  attachedFile: File | null;
  disabled?: boolean;
  agents?: AgentMentionOption[];
}

export function ChatInput({
  onSend,
  onAttach,
  onStop,
  isStreaming,
  attachedFile,
  disabled,
  agents = [],
}: ChatInputProps) {
  const [text, setText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // @ mention state
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionOpen, setMentionOpen] = useState(false);
  const [mentionIndex, setMentionIndex] = useState(0);
  // cursor position where '@' was typed
  const mentionStartRef = useRef<number>(-1);

  // Detect @ in text and manage dropdown
  const handleTextChange = useCallback(
    (value: string, cursorPos: number) => {
      setText(value);

      // Scan backwards from cursor to find '@'
      const textBefore = value.slice(0, cursorPos);
      const atIndex = textBefore.lastIndexOf('@');

      if (atIndex !== -1) {
        // Only trigger if '@' is at start or after space/newline
        const charBefore = atIndex > 0 ? textBefore[atIndex - 1] : ' ';
        const isWordBoundary = /\s/.test(charBefore) || atIndex === 0;

        if (isWordBoundary) {
          const query = textBefore.slice(atIndex + 1);
          // If query contains space, close menu
          if (!query.includes(' ') && !query.includes('\n')) {
            setMentionQuery(query);
            mentionStartRef.current = atIndex;
            setMentionOpen(true);
            setMentionIndex(0);
            return;
          }
        }
      }

      setMentionOpen(false);
      mentionStartRef.current = -1;
    },
    []
  );

  const handleSelectAgent = useCallback(
    (agent: AgentMentionOption) => {
      const start = mentionStartRef.current;
      if (start === -1) return;

      // Replace @query with @AgentName and space
      const before = text.slice(0, start);
      const after = text.slice(start + 1 + mentionQuery.length);
      const mention = `@${agent.name} `;
      const newText = before + mention + after;
      setText(newText);
      setMentionOpen(false);
      mentionStartRef.current = -1;

      // Restore focus + move cursor to end of mention
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          const pos = before.length + mention.length;
          textareaRef.current.setSelectionRange(pos, pos);
        }
      });
    },
    [text, mentionQuery]
  );

  const filteredAgents = agents.filter((a) =>
    a.name.toLowerCase().includes(mentionQuery.toLowerCase()) ||
    a.agent_type.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  const handleSend = () => {
    if (isStreaming) {
      onStop();
      return;
    }
    if (!text.trim() && !attachedFile) return;
    onSend(text.trim());
    setText('');
    setMentionOpen(false);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Handle mention navigation
    if (mentionOpen && filteredAgents.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setMentionIndex((i) => (i + 1) % filteredAgents.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setMentionIndex((i) => (i - 1 + filteredAgents.length) % filteredAgents.length);
        return;
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSelectAgent(filteredAgents[mentionIndex]);
        return;
      }
      if (e.key === 'Escape') {
        setMentionOpen(false);
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file && file.size > MAX_ATTACH_SIZE) {
      toast.error(`Arquivo muito grande (${Math.round(file.size / (1024 * 1024))} MB). Limite: 50 MB.`);
      e.target.value = '';
      return;
    }
    onAttach(file);
    e.target.value = '';
  };

  // Cast ref to satisfy AgentMentionDropdown's prop type
  const anchorRef = wrapperRef as React.RefObject<HTMLElement | null>;

  return (
    <div className="border-t bg-background px-3 sm:px-4 py-2 sm:py-3">
      {attachedFile && (
        <div className="mb-2">
          <FileAttachment file={attachedFile} onRemove={() => onAttach(null)} />
        </div>
      )}

      {/* Relative wrapper so dropdown positions correctly */}
      <div ref={wrapperRef} className="relative flex items-end gap-2">
        {/* @ mention dropdown */}
        {mentionOpen && agents.length > 0 && (
          <AgentMentionDropdown
            agents={agents}
            query={mentionQuery}
            selectedIndex={mentionIndex}
            onSelect={handleSelectAgent}
            onClose={() => setMentionOpen(false)}
            anchorRef={anchorRef}
          />
        )}

        {/* Botão de anexo */}
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 shrink-0 text-muted-foreground hover:text-foreground"
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming || disabled}
          type="button"
          title="Anexar documento (PDF, DOCX, ODT, TXT)"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.odt,.txt"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Textarea */}
        <Textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            const el = e.target;
            handleTextChange(el.value, el.selectionStart ?? el.value.length);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Pergunte sobre direito, jurisprudência ou peças processuais... (use @ para mencionar um agente)"
          className="min-h-[40px] max-h-[200px] resize-y flex-1 py-2"
          disabled={isStreaming || disabled}
          rows={1}
        />

        {/* Botão enviar / parar - prominent, touch-friendly */}
        <Button
          size="icon"
          className="h-10 w-10 sm:h-9 sm:w-9 shrink-0 rounded-full sm:rounded-md"
          onClick={handleSend}
          disabled={disabled || (!isStreaming && !text.trim() && !attachedFile)}
          type="button"
          title={isStreaming ? 'Parar geração' : 'Enviar mensagem'}
        >
          {isStreaming ? <Square className="h-4 w-4 fill-current" /> : <Send className="h-4 w-4" />}
        </Button>
      </div>

      <p className="mt-1.5 text-center text-[10px] text-muted-foreground">
        Enter para enviar · Shift+Enter para nova linha · @ para mencionar agente · @blueprint para listar peças · Anexe documentos com o clipe
      </p>
    </div>
  );
}
