import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center space-y-6 max-w-md mx-auto px-4">
        <div className="mx-auto w-16 h-16 rounded-full bg-purple-100 dark:bg-purple-900/20 flex items-center justify-center">
          <FileQuestion className="h-8 w-8 text-purple-600" />
        </div>
        <div>
          <h1 className="text-6xl font-bold text-primary">404</h1>
          <h2 className="text-xl font-semibold mt-2">Página não encontrada</h2>
          <p className="text-muted-foreground mt-2">
            A página que você procura não existe ou foi movida.
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          <Button asChild variant="default">
            <Link href="/dashboard">
              <Home className="h-4 w-4 mr-2" />
              Página inicial
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="javascript:history.back()">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
