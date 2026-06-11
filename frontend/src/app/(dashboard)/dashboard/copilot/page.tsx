import { CopilotChat } from './components/CopilotChat';

export const metadata = {
  title: 'Copilot Jurídico | Verus.AI',
  description: 'Assistente jurídico com IA - peças processuais, jurisprudência e orientação legal',
};

interface CopilotPageProps {
  searchParams: Promise<{ prompt?: string }>;
}

export default async function CopilotPage({ searchParams }: CopilotPageProps) {
  const params = await searchParams;
  const initialPrompt = params.prompt || '';

  return (
    <div className="flex h-[calc(100dvh-3.5rem)] sm:h-[calc(100dvh-4rem)] flex-col overflow-hidden">
      <CopilotChat initialPrompt={initialPrompt} />
    </div>
  );
}
