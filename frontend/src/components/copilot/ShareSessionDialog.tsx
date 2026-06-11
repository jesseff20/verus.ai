'use client';

import * as React from 'react';
import { Share2, Copy, Link, Mail, Clock, Users, Trash2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useCopilotShare } from '@/hooks/use-copilot-share';
import { cn } from '@/lib/utils';

interface ShareSessionDialogProps {
  sessionId: string;
  trigger?: React.ReactNode;
}

/**
 * Dialog para compartilhar sessão do Copilot
 */
export function ShareSessionDialog({ sessionId, trigger }: ShareSessionDialogProps) {
  const [open, setOpen] = React.useState(false);
  const [isPublic, setIsPublic] = React.useState(false);
  const [expiresDays, setExpiresDays] = React.useState<number>(7);
  const [emails, setEmails] = React.useState<string[]>([]);
  const [emailInput, setEmailInput] = React.useState('');

  const { createShare, isCreating, shareData } = useCopilotShare();
  const [shareUrl, setShareUrl] = React.useState<string | null>(null);

  const handleCreateShare = () => {
    createShare({
      session_id: sessionId,
      shared_with_emails: isPublic ? [] : emails,
      is_public: isPublic,
      expires_days: expiresDays,
    });
  };

  // Quando o compartilhamento é criado, gerar URL
  React.useEffect(() => {
    if (shareData) {
      const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
      setShareUrl(`${baseUrl}/copilot/shared/${shareData.session_id}`);
    }
  }, [shareData]);

  const handleAddEmail = () => {
    if (emailInput.trim() && !emails.includes(emailInput.trim())) {
      setEmails([...emails, emailInput.trim()]);
      setEmailInput('');
    }
  };

  const handleRemoveEmail = (email: string) => {
    setEmails(emails.filter((e) => e !== email));
  };

  const handleCopyLink = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
    }
  };

  const handleShareCodeCopy = () => {
    if (shareData?.session_id) {
      navigator.clipboard.writeText(shareData.session_id);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm" className="gap-2">
            <Share2 className="h-4 w-4" />
            Compartilhar
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Compartilhar Conversa
          </DialogTitle>
          <DialogDescription>
            Compartilhe esta conversa com outras pessoas
          </DialogDescription>
        </DialogHeader>

        {!shareUrl ? (
          <div className="space-y-4">
            {/* Tipo de compartilhamento */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Compartilhamento público</Label>
                <p className="text-xs text-muted-foreground">
                  Qualquer pessoa com o link pode acessar
                </p>
              </div>
              <Switch
                checked={isPublic}
                onCheckedChange={setIsPublic}
              />
            </div>

            {/* Expiração */}
            {!isPublic && (
              <div className="space-y-2">
                <Label>Expiração (dias)</Label>
                <Input
                  type="number"
                  min={1}
                  max={30}
                  value={expiresDays}
                  onChange={(e) => setExpiresDays(parseInt(e.target.value) || 7)}
                />
              </div>
            )}

            {/* Emails */}
            {!isPublic && (
              <div className="space-y-2">
                <Label>Adicionar pessoas por email</Label>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="colega@verus.ai"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddEmail())}
                  />
                  <Button type="button" onClick={handleAddEmail} variant="outline">
                    <Mail className="h-4 w-4" />
                  </Button>
                </div>

                {/* Lista de emails */}
                {emails.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {emails.map((email) => (
                      <Badge
                        key={email}
                        variant="secondary"
                        className="gap-1 pr-1"
                      >
                        {email}
                        <button
                          onClick={() => handleRemoveEmail(email)}
                          className="hover:text-destructive"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}

            <Button
              className="w-full"
              onClick={handleCreateShare}
              disabled={isCreating || (!isPublic && emails.length === 0)}
            >
              {isCreating ? 'Criando...' : 'Criar Link de Compartilhamento'}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Link gerado */}
            <div className="space-y-2">
              <Label>Link de compartilhamento</Label>
              <div className="flex gap-2">
                <Input value={shareUrl} readOnly className="font-mono text-xs" />
                <Button onClick={handleCopyLink} variant="outline">
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Código */}
            <div className="space-y-2">
              <Label>Código de compartilhamento</Label>
              <div className="flex gap-2">
                <Input
                  value={shareData?.session_id?.slice(-8)?.toUpperCase()}
                  readOnly
                  className="font-mono text-center text-lg tracking-widest"
                />
                <Button onClick={handleShareCodeCopy} variant="outline">
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Informações */}
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                Expira em {expiresDays} dias
              </span>
              {isPublic && (
                <span className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  Público
                </span>
              )}
            </div>

            {/* Emails compartilhados */}
            {!isPublic && emails.length > 0 && (
              <div className="space-y-2">
                <Label>Compartilhado com</Label>
                <ScrollArea className="h-20">
                  <div className="flex flex-wrap gap-1">
                    {emails.map((email) => (
                      <Badge key={email} variant="outline" className="gap-1">
                        <Check className="h-3 w-3 text-green-500" />
                        {email}
                      </Badge>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setOpen(false)}>
                Fechar
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
