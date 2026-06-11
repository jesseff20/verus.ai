'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { KanbanColumn, KanbanTask } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { LayoutGrid, MoreHorizontal, ArrowRight, User } from 'lucide-react';
import { toast } from 'sonner';

const prioColors: Record<string, string> = { urgente: 'bg-red-500', alta: 'bg-orange-500', media: 'bg-yellow-500', baixa: 'bg-gray-400' };

export default function KanbanPage() {
  const queryClient = useQueryClient();

  const { data: columns = [], isLoading } = useQuery({
    queryKey: ['tasks-kanban'],
    queryFn: async () => {
      const res = await api.get('/api/v1/processos/kanban/');
      return res.data as KanbanColumn[];
    },
    staleTime: 1 * 60 * 1000,
  });

  const moveTask = useMutation({
    mutationFn: async ({ taskId, status }: { taskId: string; status: string }) => {
      const res = await api.patch(`/api/v1/processos/kanban/${taskId}/mover/`, { status });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks-kanban'] });
      toast.success('Tarefa movida');
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error || 'Erro ao processar');
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><LayoutGrid className="h-6 w-6" /> Kanban de Tarefas</h1>
          <p className="text-muted-foreground">Quadro visual de tarefas por caso</p>
        </div>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4">
        {isLoading ? (
          <div className="text-center py-12 w-full text-muted-foreground">Carregando...</div>
        ) : (
          columns.map((col: KanbanColumn) => {
            const tasks = col.tasks || [];
            return (
              <div key={col.id} className="flex-shrink-0 w-[300px]">
                <div className="rounded-lg border bg-card">
                  <div className="p-3 border-b" style={{ borderTopColor: col.color, borderTopWidth: '3px', borderTopLeftRadius: '0.5rem', borderTopRightRadius: '0.5rem' }}>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm">{col.title}</span>
                      <Badge variant="secondary" className="text-xs">{tasks.length}</Badge>
                    </div>
                  </div>
                  <ScrollArea className="h-[500px]">
                    <div className="p-2 space-y-2">
                      {tasks.map((task: KanbanTask) => (
                        <Card key={task.id} className="hover:shadow-md transition-shadow">
                          <CardContent className="p-3 space-y-2">
                            <div className="flex items-start justify-between">
                              <p className="font-medium text-sm">{task.titulo}</p>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild><Button size="sm" variant="ghost" className="h-6 w-6 p-0" aria-label="Mover tarefa"><MoreHorizontal className="h-3 w-3" /></Button></DropdownMenuTrigger>
                                <DropdownMenuContent>
                                  {columns.filter(c => c.id !== col.id).map(c => (
                                    <DropdownMenuItem key={c.id} onClick={() => moveTask.mutate({ taskId: task.id, status: c.status })}>
                                      <ArrowRight className="h-3 w-3 mr-2" /> {c.title}
                                    </DropdownMenuItem>
                                  ))}
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                            {task.descricao && <p className="text-xs text-muted-foreground line-clamp-2">{task.descricao}</p>}
                            <div className="flex items-center justify-between text-xs">
                              <div className="flex items-center gap-1">
                                <div className={`w-2 h-2 rounded-full ${prioColors[task.prioridade]}`} />
                                <span className="text-muted-foreground capitalize">{task.prioridade}</span>
                              </div>
                              {task.data_limite && <span className="text-muted-foreground">{new Date(task.data_limite).toLocaleDateString('pt-BR')}</span>}
                            </div>
                            {task.caso_titulo && <Badge variant="outline" className="text-xs truncate max-w-full">{task.caso_titulo}</Badge>}
                            {task.responsavel_nome && <div className="flex items-center gap-1 text-xs text-muted-foreground"><User className="h-3 w-3" />{task.responsavel_nome}</div>}
                          </CardContent>
                        </Card>
                      ))}
                      {tasks.length === 0 && <div className="text-center py-8 text-xs text-muted-foreground">Nenhuma tarefa</div>}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
