'use client';

import { useState, useCallback, useRef, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { useSimulationDetail } from '@/hooks/use-simulations';
import api from '@/lib/api';
import type { JuryMember } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Users, ChevronLeft, ChevronRight, Upload, Shuffle,
  Play, Loader2, CheckCircle2, X, Plus, Trash2,
  MessageCircle, MessageSquare, Vote, FileDown, RotateCcw,
  Gavel, Shield, Scale, UserCircle, Award, AlertCircle,
  Send, HelpCircle, Briefcase, WifiOff, History,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import SimulationHistoryList from '@/components/SimulationHistoryList';
// Multi-simulation already implemented natively in this page

// ─── Constants ───

const CRIME_TYPES = [
  'Homicídio doloso',
  'Homicídio culposo',
  'Latrocínio',
  'Infanticídio',
  'Aborto provocado',
  'Instigação ao suicídio',
  'Tentativa de homicídio',
];

const PERSONALITY_TRAITS = [
  'Conservador', 'Liberal', 'Empático', 'Racional', 'Analítico',
  'Emotivo', 'Rigoroso', 'Flexível', 'Cético', 'Religioso',
  'Técnico', 'Humanista', 'Pragmático', 'Idealista',
  'Reservado', 'Comunicativo', 'Metódico', 'Espontâneo',
  'Paciente', 'Otimista', 'Realista', 'Independente',
  'Colaborativo', 'Persistente', 'Justo', 'Crítico',
  'Tolerante', 'Exigente', 'Cauteloso', 'Decidido',
  'Observador', 'Detalhista',
];

const EDUCATION_LEVELS = [
  'Ensino Fundamental', 'Ensino Médio', 'Superior Incompleto',
  'Superior Completo', 'Pós-graduação', 'Mestrado', 'Doutorado',
];

const GENDERS = ['Masculino', 'Feminino'];

const PROFESSIONS = [
  'Professor(a)', 'Engenheiro(a)', 'Médico(a)', 'Advogado(a)',
  'Comerciante', 'Funcionário(a) Público(a)', 'Aposentado(a)',
  'Empresário(a)', 'Autônomo(a)', 'Estudante', 'Agricultor(a)',
  'Técnico(a)', 'Enfermeiro(a)', 'Contador(a)', 'Motorista',
  'Dona de casa', 'Cabeleireiro(a)', 'Pedreiro', 'Cozinheiro(a)',
  'Eletricista', 'Mecânico(a)', 'Segurança', 'Recepcionista',
  'Vendedor(a)', 'Farmacêutico(a)', 'Psicólogo(a)', 'Jornalista',
  'Dentista', 'Assistente Social', 'Bombeiro(a)', 'Policial',
  'Fisioterapeuta', 'Nutricionista', 'Veterinário(a)', 'Arquiteto(a)',
  'Designer', 'Programador(a)', 'Bancário(a)', 'Vigilante',
  'Porteiro(a)', 'Taxista', 'Padeiro(a)', 'Barbeiro(a)',
  'Pedagogo(a)', 'Economista', 'Administrador(a)',
];

const DEFAULT_QUESITOS = [
  { id: 'autoria', label: 'O réu é autor do fato?', checked: true },
  { id: 'absolvicao', label: 'O réu deve ser absolvido?', checked: true },
  { id: 'diminuicao', label: 'Existe causa de diminuição de pena?', checked: true },
  { id: 'qualificadora', label: 'Existe qualificadora?', checked: true },
  { id: 'aumento', label: 'Existe causa de aumento de pena?', checked: true },
];

const JUROR_COLORS = [
  'bg-blue-500', 'bg-green-500', 'bg-amber-500', 'bg-purple-500',
  'bg-rose-500', 'bg-cyan-500', 'bg-orange-500',
];

const DEBATE_PHASES = ['Acusação', 'Defesa', 'Réplicas', 'Tréplicas', 'Deliberação'];

const DEBATE_PHASES_RICH = [
  { key: 'abertura', label: 'Abertura', icon: Gavel },
  { key: 'acusacao', label: 'Acusação', icon: Scale },
  { key: 'defesa', label: 'Defesa', icon: Shield },
  { key: 'replicas', label: 'Réplicas', icon: MessageSquare },
  { key: 'treplicas', label: 'Tréplicas', icon: MessageSquare },
  { key: 'deliberacao', label: 'Deliberação', icon: Users },
  { key: 'quesitos', label: 'Quesitos', icon: Vote },
  { key: 'veredicto', label: 'Veredicto', icon: Award },
  { key: 'relatorio', label: 'Relatório', icon: FileDown },
];

// ─── Steps ───

const STEPS = [
  { title: 'Configuração do Caso', icon: Gavel },
  { title: 'Composição do Júri', icon: Users },
  { title: 'Configuração da Sessão', icon: Scale },
  { title: 'Debate', icon: MessageCircle },
  { title: 'Veredicto', icon: Vote },
];

// ─── Dados Demográficos Brasileiros (IBGE 2022) ───

const DEMOGRAPHICS = {
  gender: [
    { value: 'feminino', weight: 51.1 },
    { value: 'masculino', weight: 48.9 },
  ],
  ageRanges: [
    { min: 18, max: 25, weight: 15 },
    { min: 26, max: 35, weight: 25 },
    { min: 36, max: 45, weight: 22 },
    { min: 46, max: 55, weight: 18 },
    { min: 56, max: 65, weight: 13 },
    { min: 66, max: 75, weight: 7 },
  ],
  education: [
    { value: 'fundamental', label: 'Ensino Fundamental', weight: 27 },
    { value: 'medio', label: 'Ensino Médio', weight: 38 },
    { value: 'superior', label: 'Ensino Superior', weight: 25 },
    { value: 'pos_graduacao', label: 'Pós-Graduação', weight: 10 },
  ],
  professions: [
    'Professor(a)', 'Comerciante', 'Funcionário(a) Público(a)', 'Aposentado(a)',
    'Autônomo(a)', 'Empresário(a)', 'Dona de casa', 'Estudante universitário(a)',
    'Motorista', 'Enfermeiro(a)', 'Vendedor(a)', 'Técnico(a) em informática',
    'Agricultor(a)', 'Operário(a)', 'Contador(a)', 'Engenheiro(a)',
    'Advogado(a)', 'Administrador(a)', 'Cabeleireiro(a)', 'Pedreiro',
    'Cozinheiro(a)', 'Eletricista', 'Mecânico(a)', 'Segurança',
    'Recepcionista', 'Auxiliar administrativo(a)', 'Médico(a)', 'Dentista',
    'Farmacêutico(a)', 'Psicólogo(a)', 'Assistente social', 'Jornalista',
    'Publicitário(a)', 'Designer', 'Programador(a)', 'Analista de sistemas',
    'Bombeiro(a)', 'Policial', 'Militar', 'Pastor(a)/Líder religioso(a)',
    'Fisioterapeuta', 'Nutricionista', 'Veterinário(a)', 'Arquiteto(a)',
    'Corretor(a) de imóveis', 'Garçom/Garçonete', 'Porteiro(a)',
    'Zelador(a)', 'Vigilante', 'Bancário(a)', 'Carteiro(a)',
    'Taxista/Motorista de app', 'Entregador(a)', 'Frentista',
    'Açougueiro(a)', 'Padeiro(a)', 'Costureiro(a)', 'Manicure',
    'Barbeiro(a)', 'Técnico(a) de enfermagem', 'Pedagogo(a)',
    'Bibliotecário(a)', 'Sociólogo(a)', 'Economista', 'Químico(a)',
    'Biólogo(a)', 'Físico(a)', 'Professor(a) universitário(a)',
  ],
  firstNamesFemale: [
    'Maria', 'Ana', 'Francisca', 'Juliana', 'Adriana', 'Fernanda',
    'Patricia', 'Aline', 'Sandra', 'Camila', 'Amanda', 'Bruna',
    'Jessica', 'Leticia', 'Mariana', 'Beatriz', 'Luciana', 'Vanessa',
    'Tatiana', 'Roberta', 'Renata', 'Simone', 'Claudia', 'Cristina',
    'Daniela', 'Gabriela', 'Isabela', 'Larissa', 'Natalia', 'Carolina',
    'Priscila', 'Raquel', 'Viviane', 'Eliane', 'Rosana', 'Michele',
    'Fabiana', 'Lilian', 'Marta', 'Sueli', 'Teresa', 'Vera',
    'Helena', 'Débora', 'Cláudia', 'Sônia', 'Regina', 'Márcia',
  ],
  firstNamesMale: [
    'José', 'João', 'Carlos', 'Paulo', 'Pedro', 'Lucas',
    'Marcos', 'Luis', 'Gabriel', 'Rafael', 'Daniel', 'Marcelo',
    'Bruno', 'Eduardo', 'Felipe', 'Rodrigo', 'Gustavo', 'André',
    'Ricardo', 'Fernando', 'Thiago', 'Diego', 'Leonardo', 'Mateus',
    'Vinicius', 'Henrique', 'Alexandre', 'Leandro', 'Renato', 'Fabio',
    'Sergio', 'Cesar', 'Roberto', 'Antonio', 'Jorge', 'Claudio',
    'Flavio', 'Márcio', 'Rogério', 'Luciano', 'Emerson', 'Edson',
    'Nilton', 'Valdir', 'Ademir', 'Geraldo', 'Manoel', 'Francisco',
  ],
  lastNames: [
    'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira',
    'Alves', 'Pereira', 'Lima', 'Gomes', 'Costa', 'Ribeiro',
    'Martins', 'Carvalho', 'Almeida', 'Lopes', 'Soares', 'Fernandes',
    'Vieira', 'Barbosa', 'Rocha', 'Dias', 'Nascimento', 'Andrade',
    'Moreira', 'Nunes', 'Marques', 'Machado', 'Mendes', 'Freitas',
    'Cardoso', 'Ramos', 'Gonçalves', 'Santana', 'Teixeira', 'Moura',
    'Correia', 'Araújo', 'Pinto', 'Campos', 'Cunha', 'Azevedo',
    'Monteiro', 'Melo', 'Fonseca', 'Cavalcanti', 'Braga', 'Miranda',
  ],
  personalityTraits: [
    'empático(a)', 'racional', 'conservador(a)', 'progressista',
    'cauteloso(a)', 'decidido(a)', 'observador(a)', 'impulsivo(a)',
    'analítico(a)', 'intuitivo(a)', 'detalhista', 'pragmático(a)',
    'idealista', 'cético(a)', 'compassivo(a)', 'rigoroso(a)',
    'reservado(a)', 'comunicativo(a)', 'metódico(a)', 'espontâneo(a)',
    'paciente', 'ansioso(a)', 'otimista', 'realista',
    'independente', 'colaborativo(a)', 'persistente', 'flexível',
    'justo(a)', 'crítico(a)', 'tolerante', 'exigente',
  ],
  // Hobbies/interesses para enriquecer backgrounds
  hobbies: [
    'leitura', 'esportes', 'música', 'culinária', 'jardinagem',
    'viagens', 'fotografia', 'artesanato', 'voluntariado', 'política',
    'religião', 'tecnologia', 'cinema', 'teatro', 'dança',
    'pesca', 'caminhada', 'academia', 'yoga', 'meditação',
  ],
  // Situação familiar
  familySituation: [
    'solteiro(a), sem filhos', 'casado(a), com 1 filho',
    'casado(a), com 2 filhos', 'casado(a), com 3 filhos',
    'divorciado(a), com filhos', 'viúvo(a)',
    'em união estável', 'solteiro(a), com 1 filho',
    'casado(a), sem filhos', 'divorciado(a), sem filhos',
  ],
  // Região de origem
  regions: [
    'zona urbana central', 'zona urbana periférica', 'zona rural',
    'bairro residencial de classe média', 'condomínio fechado',
    'conjunto habitacional popular', 'bairro comercial',
    'região metropolitana', 'cidade do interior', 'litoral',
  ],
  // Opiniões sobre justiça (para background)
  justiceViews: [
    'Acredita que a justiça deve ser rigorosa para manter a ordem social.',
    'Defende que todos merecem uma segunda chance.',
    'Valoriza mais as provas materiais do que depoimentos.',
    'Considera o contexto social do réu importante para o julgamento.',
    'Acredita que a lei deve ser aplicada igualmente para todos.',
    'Pensa que o sistema penitenciário deveria focar em reabilitação.',
    'Tem receio de condenar inocentes e prefere cautela.',
    'Acredita que crimes violentos devem ter punição exemplar.',
    'Valoriza o depoimento de testemunhas e peritos.',
    'Pensa que o réu é inocente até que se prove o contrário.',
    'Defende penas alternativas para crimes não violentos.',
    'Acredita que a intenção do ato é mais importante que o resultado.',
    'Considera fundamental ouvir todos os lados antes de julgar.',
    'Tem opinião forte sobre segurança pública na sua região.',
    'Acredita na importância do papel do Ministério Público.',
    'Valoriza a fundamentação jurídica e técnica das argumentações.',
  ],
};

function weightedRandom<T>(items: { value: T; weight: number }[]): T {
  const total = items.reduce((sum, item) => sum + item.weight, 0);
  let random = Math.random() * total;
  for (const item of items) {
    random -= item.weight;
    if (random <= 0) return item.value;
  }
  return items[items.length - 1].value;
}

// ─── Helpers ───

function generateRandomJuror(index: number): JuryMember {
  // Usar EXATAMENTE os mesmos arrays dos combos para garantir compatibilidade
  const genderLabel = GENDERS[Math.floor(Math.random() * GENDERS.length)];
  const gender = genderLabel === 'Feminino' ? 'feminino' : 'masculino';
  const ageRange = weightedRandom(DEMOGRAPHICS.ageRanges.map(r => ({ value: r, weight: r.weight })));
  const age = Math.floor(Math.random() * (ageRange.max - ageRange.min + 1)) + ageRange.min;
  const educationLabel = EDUCATION_LEVELS[Math.floor(Math.random() * EDUCATION_LEVELS.length)];
  const firstName = gender === 'feminino'
    ? DEMOGRAPHICS.firstNamesFemale[Math.floor(Math.random() * DEMOGRAPHICS.firstNamesFemale.length)]
    : DEMOGRAPHICS.firstNamesMale[Math.floor(Math.random() * DEMOGRAPHICS.firstNamesMale.length)];
  const lastName = DEMOGRAPHICS.lastNames[Math.floor(Math.random() * DEMOGRAPHICS.lastNames.length)];
  const profession = PROFESSIONS[Math.floor(Math.random() * PROFESSIONS.length)];

  // 2-3 traços de personalidade dos MESMOS que aparecem no combo
  const shuffled = [...PERSONALITY_TRAITS].sort(() => Math.random() - 0.5);
  const traits = shuffled.slice(0, 2 + Math.floor(Math.random() * 2));

  // Gerar background único e rico baseado no perfil completo
  const prof = (profession || 'profissional').toLowerCase();
  const edu = educationLabel.toLowerCase();
  const region = DEMOGRAPHICS.regions[Math.floor(Math.random() * DEMOGRAPHICS.regions.length)];
  const family = DEMOGRAPHICS.familySituation[Math.floor(Math.random() * DEMOGRAPHICS.familySituation.length)];
  const hobby1 = DEMOGRAPHICS.hobbies[Math.floor(Math.random() * DEMOGRAPHICS.hobbies.length)];
  const hobby2 = DEMOGRAPHICS.hobbies[Math.floor(Math.random() * DEMOGRAPHICS.hobbies.length)];
  const justiceView = DEMOGRAPHICS.justiceViews[Math.floor(Math.random() * DEMOGRAPHICS.justiceViews.length)];
  const yearsWorking = Math.max(1, age - (edu.includes('superior') ? 24 : edu.includes('médio') ? 20 : 18));

  const background = [
    `${genderLabel === 'Feminino' ? 'Moradora' : 'Morador'} de ${region}, ${age} anos, ${family}.`,
    `Trabalha como ${prof} há ${yearsWorking} anos. Formação: ${edu}.`,
    `Personalidade: ${traits.join(', ')}.`,
    `Nos momentos livres, dedica-se a ${hobby1} e ${hobby2}.`,
    justiceView,
  ].join(' ');

  return {
    id: `juror-${index}-${Date.now()}`,
    name: `${firstName} ${lastName}`,
    age,
    gender: genderLabel,
    profession,
    education: educationLabel,
    personality_traits: traits,
    background,
  };
}

function createEmptyJuror(index: number): JuryMember {
  return {
    id: `juror-${index}-${Date.now()}`,
    name: '',
    age: 30,
    gender: '',
    profession: '',
    education: '',
    personality_traits: [],
    background: '',
  };
}

// ─── Types ───

interface ChatMessage {
  id: string;
  sender: string;
  senderRole: 'prosecutor' | 'defense' | 'juror' | 'judge';
  jurorIndex?: number;
  content: string;
  phase: string;
  round?: number;
  timestamp: Date;
}

interface SpeakerInfo {
  name: string;
  role: 'promotor' | 'defensor' | 'juiz' | 'jurado';
}

interface JurorTendency {
  id: string;
  name: string;
  profession: string;
  gender: string;
  tendency: 'condenacao' | 'absolvicao' | null;
  confidence: number;
}

interface VerdictProbabilities {
  condenacao: number;
  absolvicao: number;
}

interface OpinionEvolutionEntry {
  member_id: string;
  member_name: string;
  round: number;
  stance: 'condenacao' | 'absolvicao';
  confidence: number;
  previous_stance: string | null;
  changed: boolean;
}

interface JurorOpinionDetail {
  stance: 'condenacao' | 'absolvicao';
  confidence: number;
  reasons: string;
  member_name: string;
}

interface QuesitResult {
  id: string;
  label: string;
  votes: { jurorName: string; vote: 'sim' | 'nao'; reasoning: string }[];
  result: 'sim' | 'nao';
}

interface DebateRound {
  id: number;
  status: 'pending' | 'running' | 'completed';
  messages: ChatMessage[];
}

interface SimInstance {
  id: number;
  simulationId: string;
  status: 'running' | 'completed' | 'failed';
  chatMessages: ChatMessage[];
  currentPhaseKey: string;
  completedPhases: string[];
  currentRound: number;
  jurorTendencies: JurorTendency[];
  verdictProbabilities: VerdictProbabilities;
  opinionEvolution: OpinionEvolutionEntry[];
  jurorOpinionDetails: Record<string, JurorOpinionDetail>;
  liveScore: { absolvicao: number; condenacao: number };
  verdictResults: QuesitResult[];
  finalVerdict: 'absolvido' | 'condenado' | null;
  analyticalReport: string;
  debateRoundsData: DebateRound[];
  activeRoundTab: number;
  currentSpeaker: SpeakerInfo | null;
  connectionStatus: 'connected' | 'reconnecting' | 'failed';
}

// ─── Persistence helpers ───

const STORAGE_KEY_PREFIX = 'verus_jury_sim_';

interface PersistedSimState {
  simulationId: string;
  chatMessages: ChatMessage[];
  currentPhaseKey: string;
  completedPhases: string[];
  currentRound: number;
  jurorTendencies: JurorTendency[];
  verdictProbabilities: VerdictProbabilities;
  opinionEvolution: OpinionEvolutionEntry[];
  jurorOpinionDetails: Record<string, JurorOpinionDetail>;
  liveScore: { absolvicao: number; condenacao: number };
  isSimulating: boolean;
  verdictResults: QuesitResult[];
  finalVerdict: 'absolvido' | 'condenado' | null;
  analyticalReport: string;
  debateRounds: DebateRound[];
  activeRoundTab: number;
  timestamp: number;
}

function saveSimState(simId: string, state: Omit<PersistedSimState, 'timestamp'>) {
  try {
    const key = STORAGE_KEY_PREFIX + simId;
    const data: PersistedSimState = { ...state, timestamp: Date.now() };
    localStorage.setItem(key, JSON.stringify(data));
  } catch {
    // localStorage full or unavailable — ignore
  }
}

function loadSimState(simId: string): PersistedSimState | null {
  try {
    const key = STORAGE_KEY_PREFIX + simId;
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const data = JSON.parse(raw) as PersistedSimState;
    // Expire after 24h
    if (Date.now() - data.timestamp > 24 * 60 * 60 * 1000) {
      localStorage.removeItem(key);
      return null;
    }
    // Rehydrate Date objects in chatMessages
    data.chatMessages = data.chatMessages.map((m) => ({
      ...m,
      timestamp: new Date(m.timestamp),
    }));
    return data;
  } catch {
    return null;
  }
}

function clearSimState(simId: string) {
  try {
    localStorage.removeItem(STORAGE_KEY_PREFIX + simId);
  } catch {
    // ignore
  }
}

// ─── Component ───

export default function JurySimulationPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>}>
      <JurySimulationPageInner />
    </Suspense>
  );
}

function JurySimulationPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const historyId = searchParams.get('id');
  const { toast } = useToast();

  // Track whether we loaded from history
  const [loadedFromHistory, setLoadedFromHistory] = useState(false);

  // Step navigation
  const [currentStep, setCurrentStep] = useState(0);

  // Step 1 - Caso
  const [caseTitle, setCaseTitle] = useState('');
  const [crimeType, setCrimeType] = useState('');
  const [caseDescription, setCaseDescription] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedCaseId, setSelectedCaseId] = useState('');

  // Buscar apenas casos criminais (contexto de júri)
  const { data: userCases } = useQuery({
    queryKey: ['user-cases-criminal'],
    queryFn: async () => {
      const response = await api.get('/api/v1/processos/?especialidade=criminal');
      return response.data.results || response.data;
    },
  });

  // Step 2 - Juri
  const [jurors, setJurors] = useState<JuryMember[]>(() =>
    Array.from({ length: 7 }, (_, i) => createEmptyJuror(i))
  );

  // Multi-simulation
  const [simulationCount, setSimulationCount] = useState(1);
  const [simInstances, setSimInstances] = useState<SimInstance[]>([]);
  const [activeSimTab, setActiveSimTab] = useState(0);
  const simAbortControllers = useRef<Record<number, AbortController>>({});

  // Step 3 - Sessao
  const [debateRounds, setDebateRounds] = useState(5);
  const [includeReplies, setIncludeReplies] = useState(true);
  const [formality, setFormality] = useState<'formal' | 'moderado' | 'informal'>('formal');
  const [quesitos, setQuesitos] = useState(DEFAULT_QUESITOS.map((q) => ({ ...q })));

  // Step 4 - Debate
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [currentDebatePhase, setCurrentDebatePhase] = useState(0);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [liveScore, setLiveScore] = useState({ absolvicao: 0, condenacao: 0 });
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [currentSpeaker, setCurrentSpeaker] = useState<SpeakerInfo | null>(null);
  const [completedPhases, setCompletedPhases] = useState<string[]>([]);
  const [currentPhaseKey, setCurrentPhaseKey] = useState('');
  const [currentRound, setCurrentRound] = useState(0);
  const [jurorTendencies, setJurorTendencies] = useState<JurorTendency[]>([]);

  // Step 5 - Veredicto
  const [verdictResults, setVerdictResults] = useState<QuesitResult[]>([]);
  const [finalVerdict, setFinalVerdict] = useState<'absolvido' | 'condenado' | null>(null);
  const [verdictProbabilities, setVerdictProbabilities] = useState<VerdictProbabilities>({ condenacao: 50, absolvicao: 50 });
  const [opinionEvolution, setOpinionEvolution] = useState<OpinionEvolutionEntry[]>([]);
  const [jurorOpinionDetails, setJurorOpinionDetails] = useState<Record<string, JurorOpinionDetail>>({});

  // Debate rounds (tabs)
  const [debateRoundsData, setDebateRoundsData] = useState<DebateRound[]>([]);
  const [activeRoundTab, setActiveRoundTab] = useState(-1);

  // Step 5 - Chat pós-veredicto
  const [verdictQuestion, setVerdictQuestion] = useState('');
  const [verdictChatHistory, setVerdictChatHistory] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const [isAskingQuestion, setIsAskingQuestion] = useState(false);
  const [analyticalReport, setAnalyticalReport] = useState('');
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const verdictChatEndRef = useRef<HTMLDivElement>(null);

  // Connection resilience state
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'reconnecting' | 'failed'>('connected');
  const retryCountRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentRoundRef = useRef(0);

  // Auto-scroll verdict chat
  useEffect(() => {
    verdictChatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [verdictChatHistory]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // ─── Restore persisted simulation state on mount ───
  useEffect(() => {
    // Check all localStorage keys for a persisted jury simulation
    try {
      const keys = Object.keys(localStorage).filter((k) => k.startsWith(STORAGE_KEY_PREFIX));
      if (keys.length === 0) return;
      // Find the most recent one
      let bestState: PersistedSimState | null = null;
      let bestKey = '';
      for (const key of keys) {
        const raw = localStorage.getItem(key);
        if (!raw) continue;
        const state = JSON.parse(raw) as PersistedSimState;
        if (!bestState || state.timestamp > bestState.timestamp) {
          bestState = state;
          bestKey = key;
        }
      }
      if (!bestState || !bestState.chatMessages || bestState.chatMessages.length === 0) return;
      // Only restore if the simulation was in progress (not completed)
      if (bestState.finalVerdict && !bestState.isSimulating) {
        // Completed simulation — restore to show verdict
      }
      // Rehydrate dates
      bestState.chatMessages = bestState.chatMessages.map((m) => ({
        ...m,
        timestamp: new Date(m.timestamp),
      }));

      // Restore state
      setSimulationId(bestState.simulationId);
      setChatMessages(bestState.chatMessages);
      setCurrentPhaseKey(bestState.currentPhaseKey);
      setCompletedPhases(bestState.completedPhases);
      setCurrentRound(bestState.currentRound);
      setJurorTendencies(bestState.jurorTendencies);
      setVerdictProbabilities(bestState.verdictProbabilities);
      setOpinionEvolution(bestState.opinionEvolution);
      setJurorOpinionDetails(bestState.jurorOpinionDetails);
      setLiveScore(bestState.liveScore);
      setVerdictResults(bestState.verdictResults || []);
      setFinalVerdict(bestState.finalVerdict || null);
      setAnalyticalReport(bestState.analyticalReport || '');
      setDebateRoundsData(bestState.debateRounds || []);
      setActiveRoundTab(bestState.activeRoundTab || 0);
      // Don't restore isSimulating=true — the stream is gone
      setIsSimulating(false);

      // Navigate to the right step
      if (bestState.finalVerdict) {
        setCurrentStep(4);
      } else if (bestState.chatMessages.length > 0) {
        setCurrentStep(3);
      }

      toast({
        title: 'Simulação restaurada',
        description: 'Encontramos uma simulação anterior salva. Seus dados foram restaurados.',
      });
    } catch {
      // Ignore restore errors
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only on mount

  // ── Load from history when ?id= is present ──
  const { data: historySimulation } = useSimulationDetail(historyId);
  const historyLoadedRef = useRef(false);

  useEffect(() => {
    if (!historySimulation || historyLoadedRef.current) return;
    if (historySimulation.status !== 'completed') return;
    historyLoadedRef.current = true;

    const result = historySimulation.result || {};

    // Populate state from saved simulation
    setSimulationId(historySimulation.id);
    setFinalVerdict(result.verdict === 'condenacao' ? 'condenado' : result.verdict === 'absolvicao' ? 'absolvido' : null);
    setAnalyticalReport(result.report || '');

    // Populate verdict probabilities
    if (result.probabilities) {
      setVerdictProbabilities(result.probabilities);
    }

    // Populate deliberation votes as live score
    if (result.deliberation_votes) {
      setLiveScore({
        absolvicao: result.deliberation_votes.absolvicao || 0,
        condenacao: result.deliberation_votes.condenacao || 0,
      });
    }

    // Populate juror opinion details
    if (result.juror_opinions) {
      setJurorOpinionDetails(result.juror_opinions);
    }

    // Populate opinion evolution
    if (result.opinion_evolution) {
      setOpinionEvolution(result.opinion_evolution);
    }

    // Jump to verdict step
    setCurrentStep(4);
    setLoadedFromHistory(true);

    toast({
      title: 'Simulação carregada do histórico',
      description: `"${historySimulation.title}" foi carregada com sucesso.`,
    });
  }, [historySimulation, toast]);

  // ─── Persist simulation state to localStorage ───
  useEffect(() => {
    if (!simulationId) return;
    // Only persist when there's meaningful state
    if (chatMessages.length === 0 && !isSimulating) return;
    saveSimState(simulationId, {
      simulationId,
      chatMessages,
      currentPhaseKey,
      completedPhases,
      currentRound,
      jurorTendencies,
      verdictProbabilities,
      opinionEvolution,
      jurorOpinionDetails,
      liveScore,
      isSimulating,
      verdictResults,
      finalVerdict,
      analyticalReport,
      debateRounds: debateRoundsData,
      activeRoundTab,
    });
  }, [
    simulationId, chatMessages, currentPhaseKey, completedPhases,
    currentRound, jurorTendencies, verdictProbabilities, opinionEvolution,
    jurorOpinionDetails, liveScore, isSimulating, verdictResults,
    finalVerdict, analyticalReport, debateRoundsData, activeRoundTab,
  ]);

  // ─── Handlers: Step 1 ───

  const handleSelectCase = useCallback((caseId: string) => {
    setSelectedCaseId(caseId);
    const selectedCase = userCases?.find((c: any) => c.id === caseId);
    if (selectedCase) {
      setCaseTitle(selectedCase.titulo || '');
      setCaseDescription(selectedCase.descricao || '');
      if (selectedCase.especialidade === 'criminal') {
        setCrimeType(selectedCase.tipo_crime || 'Homicídio doloso');
      }
      toast({
        title: 'Caso importado',
        description: `Dados de "${selectedCase.titulo}" preenchidos automaticamente.`,
      });
    }
  }, [userCases, toast]);

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadedFiles((prev) => [...prev, ...Array.from(e.target.files!) as File[]]);
    }
  }, []);

  const removeFile = useCallback((index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // ─── Handlers: Step 2 ───

  const updateJuror = useCallback((index: number, field: keyof JuryMember, value: any) => {
    setJurors((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  }, []);

  const toggleTrait = useCallback((jurorIndex: number, trait: string) => {
    setJurors((prev) => {
      const updated = [...prev];
      const juror = { ...updated[jurorIndex] };
      if (juror.personality_traits.includes(trait)) {
        juror.personality_traits = juror.personality_traits.filter((t) => t !== trait);
      } else {
        juror.personality_traits = [...juror.personality_traits, trait];
      }
      updated[jurorIndex] = juror;
      return updated;
    });
  }, []);

  const generateRandomJury = useCallback(() => {
    setJurors(Array.from({ length: 7 }, (_, i) => generateRandomJuror(i)));
    toast({ title: 'Júri gerado', description: '7 jurados gerados aleatoriamente com perfil demográfico brasileiro.' });
  }, [toast]);

  // ─── Handlers: Step 3 ───

  const toggleQuesito = useCallback((id: string) => {
    setQuesitos((prev) =>
      prev.map((q) => (q.id === id ? { ...q, checked: !q.checked } : q))
    );
  }, []);

  // ─── Handlers: Step 4 - Debate SSE ───

  // ─── SSE Event Processing (shared between start and retry) ───
  const processSSEEvent = useCallback((event: any) => {
    const eventType = event.type || event.event || 'message';

    const roleMap: Record<string, SpeakerInfo['role']> = {
      prosecutor: 'promotor',
      defense: 'defensor',
      judge: 'juiz',
      juror: 'jurado',
    };

    if (eventType === 'phase_change') {
      const phaseKey = event.phase || '';
      setCurrentPhaseKey((prev) => {
        if (prev && prev !== phaseKey) {
          setCompletedPhases((cp) => cp.includes(prev) ? cp : [...cp, prev]);
          // When leaving deliberation, mark all rounds as completed
          if (prev === 'deliberacao') {
            setDebateRoundsData((rounds) => rounds.map((r) => ({ ...r, status: 'completed' as const })));
          }
        }
        return phaseKey;
      });
      if (event.content) {
        setChatMessages((prev) => [
          ...prev,
          {
            id: `phase-${Date.now()}-${Math.random()}`,
            sender: 'Sistema',
            senderRole: 'judge',
            content: event.content,
            phase: event.phase || '',
            timestamp: new Date(),
          },
        ]);
      }
      return { action: 'flush' as const };
    } else if (eventType === 'speaker_start') {
      const newMsgId = `msg-${Date.now()}-${Math.random()}`;
      setCurrentSpeaker({
        name: event.sender || event.member_name || event.name || '',
        role: roleMap[event.sender_role] || roleMap[event.role] || 'juiz',
      });
      const msgRound = event.phase === 'deliberacao' ? (event.round || currentRoundRef.current) : undefined;
      setChatMessages((prev) => [
        ...prev,
        {
          id: newMsgId,
          sender: event.sender || event.member_name || event.name || '',
          senderRole: event.sender_role || (roleMap[event.role] ? event.role : 'judge') as any,
          jurorIndex: event.juror_index,
          content: '',
          phase: event.phase || '',
          round: msgRound,
          timestamp: new Date(),
        },
      ]);
      return { action: 'speaker_start' as const, msgId: newMsgId };
    } else if (eventType === 'speaker_end') {
      setCurrentSpeaker(null);
      return { action: 'flush' as const };
    } else if (eventType === 'message') {
      if (event.content) {
        return { action: 'message_chunk' as const, content: event.content, event };
      }
    } else if (eventType === 'round_update') {
      const roundNum = event.round || 0;
      const totalRounds = event.total_rounds || 0;
      setCurrentRound(roundNum);
      currentRoundRef.current = roundNum;
      // Initialize round tabs if not yet done
      setDebateRoundsData((prev) => {
        if (prev.length === 0 && totalRounds > 0) {
          const newRounds: DebateRound[] = Array.from({ length: totalRounds }, (_, i) => ({
            id: i + 1,
            status: i + 1 === roundNum ? 'running' : 'pending',
            messages: [],
          }));
          return newRounds;
        }
        // Mark previous round as completed, current as running
        return prev.map((r) => ({
          ...r,
          status: r.id < roundNum ? 'completed' : r.id === roundNum ? 'running' : r.status,
        }));
      });
      setActiveRoundTab(roundNum - 1);
    } else if (eventType === 'score_update') {
      setLiveScore({
        absolvicao: event.absolvicao || 0,
        condenacao: event.condenacao || 0,
      });
    } else if (eventType === 'juror_tendency') {
      setJurorTendencies((prev) =>
        prev.map((jt, idx) =>
          (jt.id === event.juror_id || jt.id === event.member_id || idx === event.juror_index)
            ? { ...jt, tendency: event.tendency || event.stance, confidence: event.confidence || 0 }
            : jt
        )
      );
      if (event.probabilities) {
        setVerdictProbabilities(event.probabilities);
      }
      if (event.member_id && event.stance) {
        setOpinionEvolution((prev) => [...prev, {
          member_id: event.member_id,
          member_name: event.member_name || '',
          round: event.round || 0,
          stance: event.stance,
          confidence: event.confidence || 0,
          previous_stance: null,
          changed: false,
        }]);
      }
    } else if (eventType === 'verdict') {
      setCurrentSpeaker(null);
      setVerdictResults(event.quesitos || []);
      setFinalVerdict(event.final_verdict);
      if (event.probabilities) setVerdictProbabilities(event.probabilities);
      if (event.juror_opinions) setJurorOpinionDetails(event.juror_opinions);
      if (event.opinion_evolution) setOpinionEvolution(event.opinion_evolution);
      if (event.score) {
        setLiveScore({
          absolvicao: event.score.absolvicao || 0,
          condenacao: event.score.condenacao || 0,
        });
      }
      setCurrentStep(4);
      return { action: 'flush' as const };
    } else if (eventType === 'completed') {
      // Simulation completed successfully — clear persisted state
      setSimulationId((currentSimId) => {
        if (currentSimId) clearSimState(currentSimId);
        return currentSimId;
      });
      toast({
        title: 'Simulação salva no histórico',
        description: 'Você pode revisitar esta simulação a qualquer momento na página de histórico.',
      });
      return { action: 'completed' as const };
    } else if (eventType === 'error' || eventType === 'erro') {
      toast({
        title: 'Erro na simulação',
        description: event.content || 'Erro desconhecido no servidor.',
        variant: 'destructive',
      });
      setIsSimulating(false);
      return { action: 'error' as const };
    }

    // Capture analytical report content (phase=relatorio)
    if (event.phase === 'relatorio' && event.content) {
      setAnalyticalReport((prev) => prev + event.content);
    }

    return { action: 'none' as const };
  }, [toast]);

  // ─── SSE Stream Reader with Auto-Retry ───
  const readSSEStream = useCallback(async (
    simId: string,
    payload: any,
    headers: Record<string, string>,
    retryAttempt: number = 0,
  ): Promise<void> => {
    const MAX_RETRIES = 3;
    const BASE_DELAY = 2000; // 2s, 4s, 8s

    try {
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const response = await fetch(`/api/v1/simulations/simulations/${simId}/jury/start/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No reader');

      // Connection established — reset retry count and status
      retryCountRef.current = 0;
      setConnectionStatus('connected');
      if (retryAttempt > 0) {
        toast({
          title: 'Conexão restabelecida',
          description: 'A simulação continua de onde parou.',
        });
      }

      let streamingMsgId: string | null = null;
      let streamingContent = '';
      let chatFlushTimer: ReturnType<typeof setTimeout> | null = null;
      let pendingChatFlush = false;

      const flushChatContent = () => {
        if (chatFlushTimer) {
          clearTimeout(chatFlushTimer);
          chatFlushTimer = null;
        }
        pendingChatFlush = false;
        if (streamingMsgId && streamingContent) {
          const id = streamingMsgId;
          const content = streamingContent;
          setChatMessages((prev) =>
            prev.map((msg) => msg.id === id ? { ...msg, content } : msg)
          );
        }
      };

      const scheduleChatFlush = () => {
        if (!chatFlushTimer) {
          pendingChatFlush = true;
          chatFlushTimer = setTimeout(flushChatContent, 50);
        }
      };

      const flushStreamingMessage = () => {
        flushChatContent();
        streamingMsgId = null;
        streamingContent = '';
      };

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr || jsonStr === '[DONE]') continue;

          try {
            const event = JSON.parse(jsonStr);
            const result = processSSEEvent(event);

            if (result.action === 'flush') {
              flushStreamingMessage();
            } else if (result.action === 'speaker_start') {
              flushStreamingMessage();
              streamingMsgId = result.msgId;
              streamingContent = '';
            } else if (result.action === 'message_chunk' && result.content) {
              if (streamingMsgId) {
                // Batched: accumulate in local var, flush to React state every 50ms
                streamingContent += result.content;
                scheduleChatFlush();
              } else {
                const msgId = `msg-${Date.now()}-${Math.random()}`;
                streamingMsgId = msgId;
                streamingContent = result.content;
                const ev = result.event;
                const fallbackRound = ev.phase === 'deliberacao' ? (ev.round || currentRoundRef.current) : undefined;
                setChatMessages((prev) => [
                  ...prev,
                  {
                    id: msgId,
                    sender: ev.sender || ev.member_name || '',
                    senderRole: ev.sender_role || 'judge',
                    jurorIndex: ev.juror_index,
                    content: result.content,
                    phase: ev.phase || '',
                    round: fallbackRound,
                    timestamp: new Date(),
                  },
                ]);
              }
            } else if (result.action === 'completed') {
              flushStreamingMessage();
            } else if (result.action === 'error') {
              return; // Stop — server-side error
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (error: any) {
      // Don't retry if manually aborted
      if (error.name === 'AbortError') return;

      if (retryAttempt < MAX_RETRIES) {
        const delay = BASE_DELAY * Math.pow(2, retryAttempt); // 2s, 4s, 8s
        retryCountRef.current = retryAttempt + 1;
        setConnectionStatus('reconnecting');
        toast({
          title: 'Conexão perdida',
          description: `Reconectando em ${delay / 1000}s... (tentativa ${retryAttempt + 1}/${MAX_RETRIES})`,
        });
        await new Promise((resolve) => setTimeout(resolve, delay));
        return readSSEStream(simId, payload, headers, retryAttempt + 1);
      } else {
        setConnectionStatus('failed');
        toast({
          title: 'Falha na conexao',
          description: 'Não foi possível reconectar. Seus dados foram salvos. Recarregue a página para tentar novamente.',
          variant: 'destructive',
        });
      }
    }
  }, [processSSEEvent, toast]);

  // ─── Multi-simulation SSE handler for a single instance ───
  const startSSEForInstance = useCallback(async (
    instanceIdx: number,
    simId: string,
    payload: any,
    headers: Record<string, string>,
  ) => {
    const controller = new AbortController();
    simAbortControllers.current[instanceIdx] = controller;

    const updateInstance = (updater: (inst: SimInstance) => SimInstance) => {
      setSimInstances((prev) =>
        prev.map((inst, i) => (i === instanceIdx ? updater(inst) : inst))
      );
    };

    try {
      const response = await fetch(`/api/v1/simulations/simulations/${simId}/jury/start/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No reader');

      let streamingMsgId: string | null = null;
      let streamingContent = '';
      let buffer = '';
      let instanceCurrentRound = 0;

      const roleMap: Record<string, SpeakerInfo['role']> = {
        prosecutor: 'promotor',
        defense: 'defensor',
        judge: 'juiz',
        juror: 'jurado',
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr || jsonStr === '[DONE]') continue;

          try {
            const event = JSON.parse(jsonStr);
            const eventType = event.type || event.event || 'message';

            if (eventType === 'phase_change') {
              const phaseKey = event.phase || '';
              updateInstance((inst) => {
                const newCompleted = inst.currentPhaseKey && inst.currentPhaseKey !== phaseKey && !inst.completedPhases.includes(inst.currentPhaseKey)
                  ? [...inst.completedPhases, inst.currentPhaseKey]
                  : inst.completedPhases;
                const msgs = event.content ? [...inst.chatMessages, {
                  id: `phase-${Date.now()}-${Math.random()}`,
                  sender: 'Sistema',
                  senderRole: 'judge' as const,
                  content: event.content,
                  phase: event.phase || '',
                  timestamp: new Date(),
                }] : inst.chatMessages;
                return { ...inst, currentPhaseKey: phaseKey, completedPhases: newCompleted, chatMessages: msgs };
              });
              streamingMsgId = null;
              streamingContent = '';
            } else if (eventType === 'speaker_start') {
              if (streamingMsgId && streamingContent) {
                const fid = streamingMsgId;
                const fc = streamingContent;
                updateInstance((inst) => ({
                  ...inst,
                  chatMessages: inst.chatMessages.map((m) => m.id === fid ? { ...m, content: fc } : m),
                }));
              }
              const newMsgId = `msg-${Date.now()}-${Math.random()}`;
              const msgRound = event.phase === 'deliberacao' ? (event.round || instanceCurrentRound) : undefined;
              const speakerInfo: SpeakerInfo = {
                name: event.sender || event.member_name || event.name || '',
                role: roleMap[event.sender_role] || roleMap[event.role] || 'juiz',
              };
              updateInstance((inst) => ({
                ...inst,
                currentSpeaker: speakerInfo,
                chatMessages: [...inst.chatMessages, {
                  id: newMsgId,
                  sender: event.sender || event.member_name || event.name || '',
                  senderRole: event.sender_role || 'judge' as any,
                  jurorIndex: event.juror_index,
                  content: '',
                  phase: event.phase || '',
                  round: msgRound,
                  timestamp: new Date(),
                }],
              }));
              streamingMsgId = newMsgId;
              streamingContent = '';
            } else if (eventType === 'speaker_end') {
              if (streamingMsgId && streamingContent) {
                const fid = streamingMsgId;
                const fc = streamingContent;
                updateInstance((inst) => ({
                  ...inst,
                  currentSpeaker: null,
                  chatMessages: inst.chatMessages.map((m) => m.id === fid ? { ...m, content: fc } : m),
                }));
              }
              streamingMsgId = null;
              streamingContent = '';
            } else if (eventType === 'message' && event.content) {
              if (streamingMsgId) {
                streamingContent += event.content;
                const fid = streamingMsgId;
                const fc = streamingContent;
                updateInstance((inst) => ({
                  ...inst,
                  chatMessages: inst.chatMessages.map((m) => m.id === fid ? { ...m, content: fc } : m),
                }));
              }
            } else if (eventType === 'round_update') {
              instanceCurrentRound = event.round || 0;
              updateInstance((inst) => ({
                ...inst,
                currentRound: event.round || 0,
              }));
            } else if (eventType === 'score_update') {
              updateInstance((inst) => ({
                ...inst,
                liveScore: { absolvicao: event.absolvicao || 0, condenacao: event.condenacao || 0 },
              }));
            } else if (eventType === 'juror_tendency') {
              updateInstance((inst) => ({
                ...inst,
                jurorTendencies: inst.jurorTendencies.map((jt, idx) =>
                  (jt.id === event.juror_id || jt.id === event.member_id || idx === event.juror_index)
                    ? { ...jt, tendency: event.tendency || event.stance, confidence: event.confidence || 0 }
                    : jt
                ),
                verdictProbabilities: event.probabilities || inst.verdictProbabilities,
                opinionEvolution: event.member_id && event.stance ? [...inst.opinionEvolution, {
                  member_id: event.member_id,
                  member_name: event.member_name || '',
                  round: event.round || 0,
                  stance: event.stance,
                  confidence: event.confidence || 0,
                  previous_stance: null,
                  changed: false,
                }] : inst.opinionEvolution,
              }));
            } else if (eventType === 'verdict') {
              updateInstance((inst) => ({
                ...inst,
                currentSpeaker: null,
                verdictResults: event.quesitos || [],
                finalVerdict: event.final_verdict,
                verdictProbabilities: event.probabilities || inst.verdictProbabilities,
                jurorOpinionDetails: event.juror_opinions || inst.jurorOpinionDetails,
                opinionEvolution: event.opinion_evolution || inst.opinionEvolution,
                liveScore: event.score ? { absolvicao: event.score.absolvicao || 0, condenacao: event.score.condenacao || 0 } : inst.liveScore,
                status: 'completed',
              }));
            } else if (eventType === 'completed') {
              updateInstance((inst) => ({ ...inst, status: 'completed' }));
            } else if (eventType === 'error' || eventType === 'erro') {
              updateInstance((inst) => ({ ...inst, status: 'failed' }));
            }

            if (event.phase === 'relatorio' && event.content) {
              updateInstance((inst) => ({ ...inst, analyticalReport: inst.analyticalReport + event.content }));
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return;
      updateInstance((inst) => ({ ...inst, status: 'failed', connectionStatus: 'failed' }));
    }
  }, []);

  // ─── Start ALL simultaneous simulations ───
  const startAllSimulations = useCallback(async () => {
    setIsSimulating(true);
    setCurrentStep(3);

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const payload = {
      case_title: caseTitle,
      crime_type: crimeType,
      case_description: caseDescription,
      jurors: jurors.map((j) => ({
        name: j.name,
        age: j.age,
        gender: j.gender,
        profession: j.profession,
        education: j.education,
        personality_traits: j.personality_traits,
        background: j.background,
      })),
      debate_rounds: debateRounds,
      include_replies: includeReplies,
      formality,
      quesitos: quesitos.filter((q) => q.checked).map((q) => ({ id: q.id, label: q.label })),
    };

    const instances: SimInstance[] = [];
    for (let i = 0; i < simulationCount; i++) {
      try {
        const createRes = await fetch('/api/v1/simulations/simulations/', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            simulation_type: 'jury',
            title: `${caseTitle} (Sim ${i + 1})`,
            description: caseDescription,
            ...(selectedCaseId ? { case: selectedCaseId } : {}),
            config: {
              crime_type: crimeType,
              case_description: caseDescription,
              case_title: caseTitle,
              debate_rounds: debateRounds,
              include_replicas: includeReplies,
              formality,
              quesitos: quesitos.filter((q) => q.checked).map((q) => q.label),
              jurors: payload.jurors,
            },
          }),
        });
        if (!createRes.ok) throw new Error(`HTTP ${createRes.status}`);
        const simData = await createRes.json();

        instances.push({
          id: i,
          simulationId: simData.id,
          status: 'running',
          chatMessages: [],
          currentPhaseKey: 'abertura',
          completedPhases: [],
          currentRound: 0,
          jurorTendencies: jurors.map((j) => ({
            id: j.id,
            name: j.name,
            profession: j.profession,
            gender: j.gender,
            tendency: null,
            confidence: 0,
          })),
          verdictProbabilities: { condenacao: 50, absolvicao: 50 },
          opinionEvolution: [],
          jurorOpinionDetails: {},
          liveScore: { absolvicao: 0, condenacao: 0 },
          verdictResults: [],
          finalVerdict: null,
          analyticalReport: '',
          debateRoundsData: [],
          activeRoundTab: -1,
          currentSpeaker: null,
          connectionStatus: 'connected',
        });
      } catch (error: any) {
        toast({
          title: `Erro na simulação ${i + 1}`,
          description: error.message || 'Falha ao criar simulação.',
          variant: 'destructive',
        });
      }
    }

    setSimInstances(instances);
    setActiveSimTab(0);

    // Start all SSE connections simultaneously (don't await)
    for (const inst of instances) {
      startSSEForInstance(inst.id, inst.simulationId, payload, headers);
    }
  }, [caseTitle, crimeType, caseDescription, jurors, debateRounds, includeReplies, formality, quesitos, simulationCount, selectedCaseId, toast, startSSEForInstance]);

  const startSimulation = useCallback(async () => {
    setIsSimulating(true);
    setChatMessages([]);
    setCurrentDebatePhase(0);
    setLiveScore({ absolvicao: 0, condenacao: 0 });
    setCurrentSpeaker(null);
    setCompletedPhases([]);
    setCurrentPhaseKey('abertura');
    setCurrentRound(0);
    setJurorTendencies(jurors.map((j) => ({
      id: j.id,
      name: j.name,
      profession: j.profession,
      gender: j.gender,
      tendency: null,
      confidence: 0,
    })));
    setVerdictProbabilities({ condenacao: 50, absolvicao: 50 });
    setOpinionEvolution([]);
    setJurorOpinionDetails({});
    setConnectionStatus('connected');
    retryCountRef.current = 0;
    currentRoundRef.current = 0;
    setDebateRoundsData([]);
    setActiveRoundTab(-1);

    try {
      const payload = {
        case_title: caseTitle,
        crime_type: crimeType,
        case_description: caseDescription,
        jurors: jurors.map((j) => ({
          name: j.name,
          age: j.age,
          gender: j.gender,
          profession: j.profession,
          education: j.education,
          personality_traits: j.personality_traits,
          background: j.background,
        })),
        debate_rounds: debateRounds,
        include_replies: includeReplies,
        formality,
        quesitos: quesitos.filter((q) => q.checked).map((q) => ({ id: q.id, label: q.label })),
      };

      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };

      // 1. Criar a simulação no backend
      const createRes = await fetch('/api/v1/simulations/simulations/', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          simulation_type: 'jury',
          title: caseTitle,
          description: caseDescription,
          ...(selectedCaseId ? { case: selectedCaseId } : {}),
          config: {
            crime_type: crimeType,
            case_description: caseDescription,
            case_title: caseTitle,
            debate_rounds: debateRounds,
            include_replicas: includeReplies,
            formality,
            quesitos: quesitos.filter((q) => q.checked).map((q) => q.label),
            jurors: payload.jurors,
          },
        }),
      });
      if (!createRes.ok) throw new Error(`Erro ao criar simulação: HTTP ${createRes.status}`);
      const simData = await createRes.json();
      const simId = simData.id;
      setSimulationId(simId);

      // 2. Iniciar streaming SSE do debate (with auto-retry)
      await readSSEStream(simId, payload, headers);

    } catch (error: any) {
      toast({
        title: 'Erro na simulação',
        description: error.message || 'Falha ao conectar com o servidor.',
        variant: 'destructive',
      });
    } finally {
      setIsSimulating(false);
      setConnectionStatus('connected');
    }
  }, [caseTitle, crimeType, caseDescription, jurors, debateRounds, includeReplies, formality, quesitos, toast, readSSEStream]);

  const advancePhase = useCallback(() => {
    if (currentDebatePhase < DEBATE_PHASES.length - 1) {
      setCurrentDebatePhase((prev) => prev + 1);
    }
  }, [currentDebatePhase]);

  // ─── Handlers: Step 5 ───

  const exportReport = useCallback(async () => {
    if (!finalVerdict && !analyticalReport) {
      toast({ title: 'Nada para exportar', description: 'O veredicto ainda nao foi gerado.', variant: 'destructive' });
      return;
    }

    const title = caseTitle || 'Simulação de Juri';
    const dateStr = new Date().toLocaleDateString('pt-BR');

    // Try backend PDF generation first
    if (simulationId) {
      setIsExportingPdf(true);
      try {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        const res = await fetch(`/api/v1/simulations/simulations/${simulationId}/generate-pdf/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          const fileName = `simulação_juri_${new Date().toISOString().split('T')[0]}.pdf`;
          a.download = fileName;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          toast({ title: 'PDF exportado', description: `Arquivo "${fileName}" baixado com sucesso.` });
          setIsExportingPdf(false);
          return;
        }
        console.warn('Backend PDF generation failed, falling back to client-side HTML.');
      } catch {
        console.warn('Backend PDF endpoint unavailable, falling back to client-side HTML.');
      }
      setIsExportingPdf(false);
    }

    // Fallback: client-side HTML blob download
    const markdownToHtml = (text: string) => {
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br/>');
    };

    const verdictLabel = finalVerdict === 'condenado' ? 'CONDENADO' : finalVerdict === 'absolvido' ? 'ABSOLVIDO' : '';
    const scoreHtml = liveScore
      ? `<div style="text-align:center;margin:20px 0;"><strong>Absolvicao:</strong> ${liveScore.absolvicao} | <strong>Condenacao:</strong> ${liveScore.condenacao}</div>`
      : '';

    const htmlContent = `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>${title}</title>
  <style>
    @page { size: A4; margin: 2.5cm 2cm 2.5cm 3cm; }
    body { font-family: 'Times New Roman', Times, serif; font-size: 12pt; line-height: 1.5; color: #000; max-width: 210mm; margin: 0 auto; padding: 2.5cm 2cm 2.5cm 3cm; text-align: justify; }
    h1 { font-size: 16pt; font-weight: bold; text-align: center; margin-bottom: 24pt; }
    h2 { font-size: 14pt; font-weight: bold; margin-top: 24pt; margin-bottom: 12pt; border-bottom: 1px solid #ccc; padding-bottom: 6pt; }
    h3 { font-size: 12pt; font-weight: bold; margin-top: 18pt; margin-bottom: 6pt; }
    p { margin-bottom: 12pt; text-indent: 2cm; }
    p:first-of-type { text-indent: 0; }
    .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 16px; margin-bottom: 24px; }
    .verdict-badge { text-align: center; padding: 12px 24px; font-size: 14pt; font-weight: bold; border: 2px solid #333; display: inline-block; margin: 16px auto; }
    .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #ccc; font-size: 9pt; color: #999; text-align: center; }
    table { width: 100%; border-collapse: collapse; margin: 12pt 0; font-size: 10pt; }
    th { background-color: #d3d3d3; padding: 8pt; text-align: left; font-weight: bold; border: 1px solid #000; }
    td { border: 1px solid #000; padding: 8pt; }
  </style>
</head>
<body>
  <div class="header">
    <h1>SIMULACAO DE TRIBUNAL DO JURI</h1>
    <p style="text-indent:0;font-size:11pt;color:#555;">${title}</p>
  </div>
  <p style="text-indent:0;"><strong>Data:</strong> ${dateStr} | <strong>Crime:</strong> ${crimeType || 'N/A'}</p>
  ${verdictLabel ? `<div style="text-align:center;margin:20px 0;"><span class="verdict-badge">${verdictLabel}</span></div>` : ''}
  ${scoreHtml}
  ${analyticalReport ? `<div><h2>Relatorio Analitico</h2><div>${markdownToHtml(analyticalReport)}</div></div>` : ''}
  <div class="footer">
    <p>Documento gerado automaticamente pelo Verus.AI - Simulação de Tribunal do Júri</p>
    <p>Este documento e uma simulação e não possui valor jurídico.</p>
  </div>
</body>
</html>`;

    const blob = new Blob([htmlContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const fileName = `simulação_juri_${new Date().toISOString().split('T')[0]}.pdf`;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({ title: 'PDF exportado', description: `Arquivo "${fileName}" baixado com sucesso.` });
  }, [toast, finalVerdict, analyticalReport, simulationId, caseTitle, crimeType, liveScore]);

  const askVerdictQuestion = useCallback(async () => {
    if (!verdictQuestion.trim() || isAskingQuestion) return;

    const question = verdictQuestion.trim();
    setVerdictChatHistory((prev) => [...prev, { role: 'user', content: question }]);
    setVerdictQuestion('');
    setIsAskingQuestion(true);

    try {
      // Use the question-verdict endpoint with the simulation ID
      if (!simulationId) {
        setVerdictChatHistory((prev) => [...prev, { role: 'assistant', content: 'Erro: ID da simulação não encontrado.' }]);
        setIsAskingQuestion(false);
        return;
      }
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch(`/api/v1/simulations/simulations/${simulationId}/question-verdict/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question }),
      });

      if (res.ok) {
        const data = await res.json();
        setVerdictChatHistory((prev) => [...prev, { role: 'assistant', content: data.answer }]);
      } else {
        setVerdictChatHistory((prev) => [...prev, { role: 'assistant', content: 'Erro ao processar a pergunta. Tente novamente.' }]);
      }
    } catch {
      setVerdictChatHistory((prev) => [...prev, { role: 'assistant', content: 'Erro de conexão. Tente novamente.' }]);
    } finally {
      setIsAskingQuestion(false);
    }
  }, [verdictQuestion, isAskingQuestion, simulationId]);

  const resetSimulation = useCallback(() => {
    setSimulationCount(1);
    // Abort any active SSE connection
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    // Abort multi-simulation connections
    Object.values(simAbortControllers.current).forEach((c) => c.abort());
    simAbortControllers.current = {};
    setSimInstances([]);
    setActiveSimTab(0);
    setSimulationCount(1);
    // Clear persisted state
    if (simulationId) {
      clearSimState(simulationId);
    }
    setCurrentStep(0);
    setCaseTitle('');
    setCrimeType('');
    setCaseDescription('');
    setUploadedFiles([]);
    setSelectedCaseId('');
    setJurors(Array.from({ length: 7 }, (_, i) => createEmptyJuror(i)));
    setDebateRounds(5);
    setIncludeReplies(true);
    setFormality('formal');
    setQuesitos(DEFAULT_QUESITOS.map((q) => ({ ...q })));
    setChatMessages([]);
    setVerdictResults([]);
    setFinalVerdict(null);
    setLiveScore({ absolvicao: 0, condenacao: 0 });
    setCurrentSpeaker(null);
    setCompletedPhases([]);
    setCurrentPhaseKey('');
    setCurrentRound(0);
    setJurorTendencies([]);
    setVerdictProbabilities({ condenacao: 50, absolvicao: 50 });
    setOpinionEvolution([]);
    setJurorOpinionDetails({});
    setVerdictChatHistory([]);
    setVerdictQuestion('');
    setAnalyticalReport('');
    setSimulationId(null);
    setConnectionStatus('connected');
    retryCountRef.current = 0;
    currentRoundRef.current = 0;
    setDebateRoundsData([]);
    setActiveRoundTab(-1);
  }, [simulationId]);

  // ─── Navigation ───

  const canAdvance = () => {
    if (currentStep === 0) return caseTitle.trim() !== '' && crimeType !== '';
    if (currentStep === 1) return jurors.every((j) => j.name.trim() !== '');
    if (currentStep === 2) return quesitos.some((q) => q.checked);
    return true;
  };

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) setCurrentStep((s) => s + 1);
  };
  const prevStep = () => {
    if (currentStep > 0) setCurrentStep((s) => s - 1);
  };

  // ─── Render Stepper ───

  const renderStepper = () => (
    <div className="flex items-center justify-center gap-1 py-3 sm:py-4 px-2 sm:px-6 bg-card border-b overflow-x-auto">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const isActive = i === currentStep;
        const isCompleted = i < currentStep;
        return (
          <div key={i} className="flex items-center shrink-0">
            <button
              onClick={() => i < currentStep && setCurrentStep(i)}
              disabled={i > currentStep}
              className={`flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : isCompleted
                  ? 'bg-primary/10 text-primary cursor-pointer hover:bg-primary/20'
                  : 'text-muted-foreground'
              }`}
            >
              {isCompleted ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <Icon className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{step.title}</span>
            </button>
            {i < STEPS.length - 1 && (
              <ChevronRight className="h-4 w-4 text-muted-foreground mx-0.5 sm:mx-1 shrink-0" />
            )}
          </div>
        );
      })}
    </div>
  );

  // ─── Render Steps ───

  const renderStep0 = () => (
    <div className="max-w-3xl mx-auto space-y-4 sm:space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Configuração do Caso</h2>
        <p className="text-muted-foreground">Defina os detalhes do caso a ser julgado.</p>
      </div>

      {/* Aviso sobre qualidade dos dados */}
      <div className="flex gap-3 p-4 rounded-lg border border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
        <AlertCircle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-amber-800 dark:text-amber-200">
            Quanto mais detalhes, melhor a simulação
          </p>
          <p className="text-amber-700 dark:text-amber-300 mt-1">
            Anexe a denúncia completa, laudos periciais, depoimentos de testemunhas e todas as peças
            do processo. Informações superficiais produzem resultados genéricos e imprecisos.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Importar de caso existente */}
        <Card className="border-dashed border-2 border-muted-foreground/20">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 mb-3">
              <Briefcase className="h-5 w-5 text-primary" />
              <div>
                <h3 className="text-sm font-semibold">Importar de Caso Existente</h3>
                <p className="text-xs text-muted-foreground">Selecione um caso para preencher automaticamente</p>
              </div>
            </div>

            <Select value={selectedCaseId} onValueChange={handleSelectCase}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione um caso ou digite manualmente abaixo" />
              </SelectTrigger>
              <SelectContent>
                {userCases?.map((c: any) => (
                  <SelectItem key={c.id} value={c.id}>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{c.titulo}</span>
                      {c.numero_processo && <span className="text-xs text-muted-foreground">({c.numero_processo})</span>}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Separator className="my-3" />
            <p className="text-xs text-muted-foreground text-center">ou preencha manualmente abaixo</p>
          </CardContent>
        </Card>

        <div className="space-y-2">
          <Label htmlFor="case-title">Título do Caso *</Label>
          <Input
            id="case-title"
            value={caseTitle}
            onChange={(e) => setCaseTitle(e.target.value)}
            placeholder="Ex: Caso João Silva - Homicídio doloso qualificado"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="crime-type">Tipo de Crime *</Label>
          <Select value={crimeType} onValueChange={setCrimeType}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione o tipo de crime" />
            </SelectTrigger>
            <SelectContent>
              {CRIME_TYPES.map((ct) => (
                <SelectItem key={ct} value={ct}>{ct}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="case-desc">Descrição Resumida dos Fatos</Label>
          <div className="relative">
            <Textarea
              id="case-desc"
              value={caseDescription}
              onChange={(e) => setCaseDescription(e.target.value)}
              placeholder="Descreva brevemente os fatos do caso..."
              rows={5}
              className="pr-32"
            />
            <div className="absolute top-1 right-1">
              <AIEnhanceButton
                value={caseDescription}
                onEnhance={setCaseDescription}
                context="descrição de fatos para simulação de júri"
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Documentos do Processo</Label>
          <p className="text-xs text-muted-foreground">
            Denúncia, defesa, provas, perícia (PDF, DOCX, TXT)
          </p>
          <div
            className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">Clique para enviar documentos</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.odt"
              className="hidden"
              onChange={handleFileUpload}
            />
          </div>
          {uploadedFiles.length > 0 && (
            <div className="space-y-2 mt-3">
              {uploadedFiles.map((f, i) => (
                <div key={i} className="flex items-center justify-between bg-muted rounded-lg px-3 py-2">
                  <span className="text-sm truncate">{f.name}</span>
                  <Button variant="ghost" size="sm" onClick={() => removeFile(i)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );

  const renderStep1 = () => (
    <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold mb-1">Composição do Júri</h2>
          <p className="text-muted-foreground text-sm">7 jurados conforme CPP art. 447</p>
        </div>
        <Button variant="outline" onClick={generateRandomJury} className="w-full sm:w-auto">
          <Shuffle className="h-4 w-4 mr-2" />
          Gerar Júri Aleatório
        </Button>
      </div>

      <ScrollArea className="h-[600px] pr-2 sm:pr-4">
        <div className="space-y-4">
          {jurors.map((juror, index) => (
            <Card key={juror.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className={`${JUROR_COLORS[index]} text-white text-xs`}>
                      {index + 1}
                    </AvatarFallback>
                  </Avatar>
                  <CardTitle className="text-base">Jurado {index + 1}</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Nome</Label>
                    <Input
                      value={juror.name}
                      onChange={(e) => updateJuror(index, 'name', e.target.value)}
                      placeholder="Nome fictício"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Idade ({juror.age})</Label>
                    <Slider
                      value={[juror.age]}
                      onValueChange={([v]) => updateJuror(index, 'age', v)}
                      min={18}
                      max={80}
                      step={1}
                      className="py-2"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Gênero</Label>
                    <Select
                      value={juror.gender}
                      onValueChange={(v) => updateJuror(index, 'gender', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        {GENDERS.map((g) => (
                          <SelectItem key={g} value={g}>{g}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Profissão</Label>
                    <Select
                      value={juror.profession}
                      onValueChange={(v) => updateJuror(index, 'profession', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        {PROFESSIONS.map((p) => (
                          <SelectItem key={p} value={p}>{p}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Escolaridade</Label>
                    <Select
                      value={juror.education}
                      onValueChange={(v) => updateJuror(index, 'education', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        {EDUCATION_LEVELS.map((e) => (
                          <SelectItem key={e} value={e}>{e}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs">Traços de Personalidade</Label>
                  <div className="flex flex-wrap gap-1.5">
                    {PERSONALITY_TRAITS.map((trait) => (
                      <Badge
                        key={trait}
                        variant={juror.personality_traits.includes(trait) ? 'default' : 'outline'}
                        className="cursor-pointer text-xs"
                        onClick={() => toggleTrait(index, trait)}
                      >
                        {trait}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <Label className="text-xs">Background (opcional)</Label>
                  <Textarea
                    value={juror.background}
                    onChange={(e) => updateJuror(index, 'background', e.target.value)}
                    placeholder="Breve descrição do jurado..."
                    rows={2}
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );

  const renderStep2 = () => (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Configuração da Sessão</h2>
        <p className="text-muted-foreground">Defina os parâmetros da sessão de julgamento.</p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <Label>Número de Rodadas de Debate: {debateRounds}</Label>
          <Slider
            value={[debateRounds]}
            onValueChange={([v]) => setDebateRounds(v)}
            min={3}
            max={10}
            step={1}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>3 (rápido)</span>
            <span>10 (detalhado)</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Incluir Réplicas e Tréplicas</Label>
            <p className="text-xs text-muted-foreground">
              Adiciona fases de réplica e tréplica ao debate
            </p>
          </div>
          <Switch checked={includeReplies} onCheckedChange={setIncludeReplies} />
        </div>

        <div className="space-y-2">
          <Label>Nível de Formalidade</Label>
          <Select value={formality} onValueChange={(v: any) => setFormality(v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="formal">Formal</SelectItem>
              <SelectItem value="moderado">Moderado</SelectItem>
              <SelectItem value="informal">Informal</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Quantidade de Simulações Simultâneas</Label>
          <p className="text-xs text-muted-foreground">
            Execute múltiplas simulações ao mesmo tempo e compare os resultados
          </p>
          <Select value={String(simulationCount)} onValueChange={(v) => setSimulationCount(Number(v))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4, 5].map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {n} simulação{n > 1 ? 'ões' : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Separator />

        <div className="space-y-3">
          <Label className="text-base font-semibold">Quesitos a Serem Votados</Label>
          <p className="text-xs text-muted-foreground">
            Conforme CPP art. 483. Selecione os quesitos aplicáveis.
          </p>
          {quesitos.map((q) => (
            <div key={q.id} className="flex items-center space-x-3">
              <Checkbox
                id={q.id}
                checked={q.checked}
                onCheckedChange={() => toggleQuesito(q.id)}
              />
              <Label htmlFor={q.id} className="text-sm font-normal cursor-pointer">
                {q.label}
              </Label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => {
    const phaseProgress = DEBATE_PHASES_RICH.length > 0
      ? Math.round(((completedPhases.length + (currentPhaseKey ? 0.5 : 0)) / DEBATE_PHASES_RICH.length) * 100)
      : 0;
    const overallProgress = Math.min(
      100,
      Math.round(
        (completedPhases.length / DEBATE_PHASES_RICH.length) * 70 +
        (currentRound / Math.max(debateRounds, 1)) * 30
      )
    );

    return (
      <div className="max-w-5xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-1">Sessão do Júri</h2>
            <p className="text-muted-foreground">{caseTitle}</p>
          </div>
          {!isSimulating && chatMessages.length === 0 && simInstances.length === 0 && (
            <Button onClick={simulationCount > 1 ? startAllSimulations : startSimulation}>
              <Play className="h-4 w-4 mr-2" />
              Iniciar {simulationCount > 1 ? `${simulationCount} Simulações` : 'Simulação'}
            </Button>
          )}
        </div>

        {/* === Multi-simulation Tab Bar === */}
        {simInstances.length > 1 && (
          <div className="flex gap-2 overflow-x-auto pb-1">
            {simInstances.map((sim, i) => (
              <button
                key={i}
                onClick={() => setActiveSimTab(i)}
                className={cn(
                  'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all shrink-0 border sim-tab-active',
                  activeSimTab === i ? 'bg-primary text-primary-foreground border-primary' : 'bg-muted border-transparent',
                  sim.status === 'completed' && activeSimTab !== i && 'border-green-500 border-2',
                  sim.status === 'failed' && activeSimTab !== i && 'border-red-500 border-2'
                )}
              >
                Simulação {i + 1}
                {sim.status === 'completed' && <CheckCircle2 className="ml-1 h-3 w-3" />}
                {sim.status === 'running' && <Loader2 className="ml-1 h-3 w-3 animate-spin" />}
                {sim.status === 'failed' && <X className="ml-1 h-3 w-3" />}
              </button>
            ))}
          </div>
        )}

        {/* === 1. Painel de Progresso em Tempo Real === */}
        {(isSimulating || chatMessages.length > 0 || simInstances.length > 0) && (
          <div className="grid grid-cols-2 gap-2 sm:gap-3 md:grid-cols-4">
            <Card className="p-3">
              <div className="text-xs text-muted-foreground">Fase Atual</div>
              <div className="text-sm font-bold capitalize">
                {currentPhaseKey
                  ? DEBATE_PHASES_RICH.find((p) => p.key === currentPhaseKey)?.label || currentPhaseKey
                  : 'Aguardando'}
              </div>
              <Progress value={phaseProgress} className="mt-2 h-1.5" />
            </Card>
            <Card className="p-3">
              <div className="text-xs text-muted-foreground">Rodada</div>
              <div className="text-lg font-bold">{currentRound}/{debateRounds}</div>
            </Card>
            <Card className="p-3">
              <div className="text-xs text-muted-foreground">Probabilidades</div>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-red-500 font-bold text-xs">{verdictProbabilities.condenacao}%</span>
                <div className="flex-1 h-2 bg-green-200 dark:bg-green-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-500 rounded-full transition-all duration-500"
                    style={{ width: `${verdictProbabilities.condenacao}%` }}
                  />
                </div>
                <span className="text-green-500 font-bold text-xs">{verdictProbabilities.absolvicao}%</span>
              </div>
              <div className="text-[10px] text-muted-foreground mt-1">
                {verdictProbabilities.condenacao > verdictProbabilities.absolvicao
                  ? 'Tendencia: Condenacao'
                  : verdictProbabilities.absolvicao > verdictProbabilities.condenacao
                  ? 'Tendencia: Absolvicao'
                  : 'Equilibrado'}
              </div>
            </Card>
            <Card className="p-3">
              <div className="text-xs text-muted-foreground">Progresso Geral</div>
              <div className="text-lg font-bold">{overallProgress}%</div>
              <Progress value={overallProgress} className="mt-2 h-1.5" />
            </Card>
          </div>
        )}

        {/* === 2. Timeline de Fases with Phase-Specific Accents === */}
        {(isSimulating || chatMessages.length > 0) && (
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {DEBATE_PHASES_RICH.map((phase) => {
              const PhaseIcon = phase.icon;
              const isActive = currentPhaseKey === phase.key;
              const phaseAccent = phase.key === 'acusacao' || phase.key === 'replicas'
                ? 'bg-red-500/10 text-red-700 dark:text-red-300 border-red-300 dark:border-red-700'
                : phase.key === 'defesa' || phase.key === 'treplicas'
                ? 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700'
                : phase.key === 'abertura'
                ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700'
                : phase.key === 'deliberacao'
                ? 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-700'
                : phase.key === 'quesitos'
                ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700'
                : phase.key === 'veredicto'
                ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700'
                : 'bg-primary text-primary-foreground';
              const activeGlow = phase.key === 'acusacao' || phase.key === 'replicas'
                ? 'prosecution-active'
                : phase.key === 'defesa' || phase.key === 'treplicas'
                ? 'defense-active'
                : 'speaker-active';
              return (
                <div
                  key={phase.key}
                  className={cn(
                    'flex items-center gap-1 px-2 py-1 rounded-full text-xs shrink-0 transition-all duration-300 border',
                    isActive && `${phaseAccent} ${activeGlow} phase-badge-enter`,
                    completedPhases.includes(phase.key) && !isActive && 'bg-primary/10 text-primary border-transparent',
                    !completedPhases.includes(phase.key) && !isActive && 'bg-muted text-muted-foreground border-transparent'
                  )}
                >
                  {isActive && phase.key === 'abertura' && (
                    <Gavel className="h-3 w-3 gavel-thinking" />
                  )}
                  {(!isActive || phase.key !== 'abertura') && (
                    <PhaseIcon className="h-3 w-3" />
                  )}
                  {phase.label}
                  {completedPhases.includes(phase.key) && (
                    <CheckCircle2 className="h-3 w-3 ml-0.5" />
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* === Abertura: Session announcement === */}
        {currentPhaseKey === 'abertura' && isSimulating && chatMessages.length === 0 && (
          <div className="court-atmosphere rounded-lg p-6 text-center border">
            <Gavel className="h-10 w-10 mx-auto mb-3 text-amber-500 gavel-thinking" />
            <p className="text-lg font-semibold session-announce">Sessão Aberta</p>
            <p className="text-sm text-muted-foreground mt-1">O Juiz Presidente abre a sessão do Tribunal do Júri</p>
          </div>
        )}

        {/* === Connection Status Banner === */}
        {connectionStatus !== 'connected' && (
          <div className={cn(
            'flex items-center gap-3 px-4 py-3 rounded-lg border text-sm font-medium',
            connectionStatus === 'reconnecting'
              ? 'bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-200'
              : 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950/30 dark:border-red-800 dark:text-red-200'
          )}>
            {connectionStatus === 'reconnecting' ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin shrink-0" />
                <span>Reconectando... (tentativa {retryCountRef.current}/3)</span>
                <span className="text-xs ml-auto opacity-75">Seus dados estao salvos</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 shrink-0" />
                <span>Conexão perdida. Seus dados foram salvos.</span>
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-auto"
                  onClick={() => window.location.reload()}
                >
                  Recarregar
                </Button>
              </>
            )}
          </div>
        )}

        {/* === 4. Cards de Jurados com Tendência + Deliberation animations === */}
        {(isSimulating || chatMessages.length > 0) && jurorTendencies.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-1.5 sm:gap-2">
            {jurorTendencies.map((member, idx) => {
              const isSpeaking = currentSpeaker?.role === 'jurado' && currentSpeaker?.name === member.name;
              const isDeliberating = currentPhaseKey === 'deliberacao' && !isSpeaking && member.tendency === null;
              return (
              <Card
                key={member.id}
                className={cn(
                  'p-2 text-center transition-all duration-300',
                  isSpeaking && 'border-2 speaker-active',
                  isDeliberating && 'juror-thinking',
                  member.tendency === 'condenacao' && !isSpeaking && 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30',
                  member.tendency === 'absolvicao' && !isSpeaking && 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/30',
                )}
              >
                <Avatar className="h-8 w-8 mx-auto mb-1">
                  <AvatarFallback className={cn(
                    'text-xs',
                    member.gender === 'Feminino' ? 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200' : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                  )}>
                    {member.name ? member.name.split(' ').map((n) => n[0]).join('').substring(0, 2) : String(idx + 1)}
                  </AvatarFallback>
                </Avatar>
                <div className="text-[10px] font-medium truncate">{member.name ? member.name.split(' ')[0] : `Jurado ${idx + 1}`}</div>
                <div className="text-[9px] text-muted-foreground truncate">{member.profession}</div>
                {member.tendency && (
                  <>
                    <Badge
                      variant="outline"
                      className={cn(
                        'mt-1 text-[8px] px-1 py-0',
                        member.tendency === 'condenacao'
                          ? 'border-red-300 text-red-600 dark:border-red-700 dark:text-red-400'
                          : 'border-green-300 text-green-600 dark:border-green-700 dark:text-green-400'
                      )}
                    >
                      {member.tendency === 'condenacao' ? 'Cond.' : 'Abs.'}
                    </Badge>
                    {member.confidence > 0 && (
                      <div className="mt-1 w-full">
                        <div className="h-1 bg-muted rounded-full overflow-hidden">
                          <div
                            className={cn(
                              'h-full rounded-full tendency-fill',
                              member.tendency === 'condenacao' ? 'bg-red-500' : 'bg-green-500'
                            )}
                            style={{ width: `${member.confidence * 100}%` }}
                          />
                        </div>
                        <div className="text-[8px] text-muted-foreground mt-0.5">
                          {(member.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                    )}
                  </>
                )}
              </Card>
              );
            })}
          </div>
        )}

        {/* === 3. Indicador "Quem está falando" with phase-specific glow === */}
        {isSimulating && currentSpeaker && (
          <div className={cn(
            'flex items-center gap-2 py-2.5 px-3 rounded-lg border-2',
            currentSpeaker.role === 'promotor' ? 'bg-red-50/50 dark:bg-red-950/20 prosecution-active' :
            currentSpeaker.role === 'defensor' ? 'bg-blue-50/50 dark:bg-blue-950/20 defense-active' :
            currentSpeaker.role === 'juiz' ? 'bg-amber-50/50 dark:bg-amber-950/20 speaker-active' : 'bg-emerald-50/50 dark:bg-emerald-950/20 speaker-active'
          )}>
            <div className={cn(
              'h-8 w-8 rounded-full flex items-center justify-center text-xs text-white shrink-0 animate-pulse',
              currentSpeaker.role === 'promotor' ? 'bg-red-500' :
              currentSpeaker.role === 'defensor' ? 'bg-blue-500' :
              currentSpeaker.role === 'juiz' ? 'bg-amber-500' : 'bg-emerald-500'
            )}>
              {currentSpeaker.role === 'juiz' ? (
                <Scale className="h-4 w-4 gavel-thinking" />
              ) : (
                <span>{currentSpeaker.name?.[0]?.toUpperCase() || '?'}</span>
              )}
            </div>
            <div className="flex-1">
              <span className="text-sm font-medium">{currentSpeaker.name || currentSpeaker.role}</span>
              <span className="text-xs text-muted-foreground ml-2">
                {currentSpeaker.role === 'juiz' ? 'está conduzindo...' :
                 currentSpeaker.role === 'promotor' ? 'está acusando...' :
                 currentSpeaker.role === 'defensor' ? 'está defendendo...' :
                 'está elaborando...'}
              </span>
            </div>
            <div className={cn(
              'speaking-wave ml-auto',
              currentSpeaker.role === 'promotor' ? 'text-red-500' :
              currentSpeaker.role === 'defensor' ? 'text-blue-500' :
              currentSpeaker.role === 'juiz' ? 'text-amber-500' : 'text-emerald-500'
            )}>
              <span /><span /><span /><span />
            </div>
          </div>
        )}

        {/* === Round Tabs (shown during deliberation) === */}
        {debateRoundsData.length > 0 && (currentPhaseKey === 'deliberacao' || completedPhases.includes('deliberacao')) && (
          <div className="flex gap-2 overflow-x-auto pb-1">
            <button
              onClick={() => setActiveRoundTab(-1)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors shrink-0 border',
                activeRoundTab === -1
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-muted text-muted-foreground border-transparent hover:bg-muted/80'
              )}
            >
              Todas as Fases
            </button>
            {debateRoundsData.map((round, i) => (
              <button
                key={round.id}
                onClick={() => setActiveRoundTab(i)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors shrink-0 border',
                  activeRoundTab === i
                    ? 'bg-primary text-primary-foreground border-primary'
                    : round.status === 'completed'
                    ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-950/30 dark:text-green-400 dark:border-green-800 hover:bg-green-100 dark:hover:bg-green-950/50'
                    : round.status === 'running'
                    ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800 animate-pulse'
                    : 'bg-muted text-muted-foreground border-transparent'
                )}
              >
                Rodada {round.id}
                {round.status === 'completed' && <CheckCircle2 className="h-3 w-3" />}
                {round.status === 'running' && <Loader2 className="h-3 w-3 animate-spin" />}
              </button>
            ))}
          </div>
        )}

        {/* Chat area */}
        <Card className="min-h-[300px] sm:min-h-[400px]">
          <ScrollArea className="h-[350px] sm:h-[400px] p-3 sm:p-4">
            <div className="space-y-3">
              {/* === 5. Estado vazio / Carregando === */}
              {chatMessages.length === 0 && !isSimulating && (
                <div className="flex flex-col items-center justify-center h-[350px] text-muted-foreground">
                  <MessageCircle className="h-12 w-12 mb-3 opacity-40" />
                  <p>Clique em &quot;Iniciar Simulação&quot; para começar o debate.</p>
                </div>
              )}
              {chatMessages.length === 0 && isSimulating && (
                <div className="flex flex-col items-center justify-center py-12 text-center court-atmosphere rounded-lg">
                  <Gavel className="h-12 w-12 text-amber-500 mb-4 gavel-thinking" />
                  <h3 className="text-lg font-semibold session-announce">Preparando Sessão do Tribunal</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    O Juiz Presidente vai abrir a sessão em instantes...
                  </p>
                  <div className="speaking-wave text-amber-500 mt-4">
                    <span /><span /><span /><span />
                  </div>
                </div>
              )}
              {chatMessages
                .filter((msg) => {
                  // When a specific round tab is selected, show only that round's deliberation messages
                  // plus all non-deliberation messages
                  if (activeRoundTab < 0 || debateRoundsData.length === 0) return true;
                  if (msg.phase !== 'deliberacao') return true;
                  return msg.round === activeRoundTab + 1;
                })
                .map((msg) => {
                const isJuror = msg.senderRole === 'juror';
                const color = isJuror && msg.jurorIndex !== undefined
                  ? JUROR_COLORS[msg.jurorIndex % JUROR_COLORS.length]
                  : msg.senderRole === 'prosecutor'
                  ? 'bg-red-500'
                  : msg.senderRole === 'defense'
                  ? 'bg-green-500'
                  : msg.senderRole === 'judge'
                  ? 'bg-amber-500'
                  : 'bg-gray-500';

                // Show markdown only for completed (non-streaming) messages
                const isStreamingMsg = isSimulating && currentSpeaker && msg.id === chatMessages[chatMessages.length - 1]?.id;

                return (
                  <div key={msg.id} className="flex items-start gap-2 sm:gap-3">
                    <Avatar className="h-7 w-7 sm:h-8 sm:w-8 shrink-0">
                      <AvatarFallback className={`${color} text-white text-[10px] sm:text-xs`}>
                        {msg.sender.substring(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                        <span className="text-xs sm:text-sm font-semibold">{msg.sender}</span>
                        <Badge variant="outline" className={cn(
                          'text-[9px] sm:text-[10px] px-1 sm:px-1.5 py-0',
                          (msg.phase === 'acusacao' || msg.phase === 'replicas') && 'border-red-300 text-red-600 dark:border-red-700 dark:text-red-400',
                          (msg.phase === 'defesa' || msg.phase === 'treplicas') && 'border-blue-300 text-blue-600 dark:border-blue-700 dark:text-blue-400',
                          msg.phase === 'abertura' && 'border-amber-300 text-amber-600 dark:border-amber-700 dark:text-amber-400',
                          msg.phase === 'deliberacao' && 'border-purple-300 text-purple-600 dark:border-purple-700 dark:text-purple-400',
                          msg.phase === 'quesitos' && 'border-emerald-300 text-emerald-600 dark:border-emerald-700 dark:text-emerald-400',
                          msg.phase === 'veredicto' && 'border-amber-300 text-amber-600 dark:border-amber-700 dark:text-amber-400',
                        )}>
                          {msg.phase}
                        </Badge>
                        {msg.round && (
                          <Badge variant="outline" className="text-[9px] sm:text-[10px] px-1 sm:px-1.5 py-0">
                            R{msg.round}
                          </Badge>
                        )}
                      </div>
                      {isStreamingMsg ? (
                        <p className="text-xs sm:text-sm text-foreground/90 mt-0.5 whitespace-pre-wrap break-words">
                          {msg.content}
                        </p>
                      ) : (
                        <div className="prose prose-sm dark:prose-invert max-w-none mt-0.5 text-xs sm:text-sm [&>p]:mb-1 [&>ul]:mb-1 [&>ol]:mb-1 [&>h1]:text-sm [&>h2]:text-sm [&>h3]:text-xs">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              {isSimulating && chatMessages.length > 0 && !currentSpeaker && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Simulação em andamento...</span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </ScrollArea>
        </Card>

        {/* Advance phase button */}
        {isSimulating && currentDebatePhase < DEBATE_PHASES.length - 1 && (
          <Button onClick={advancePhase} variant="outline" className="w-full">
            Próxima Fase: {DEBATE_PHASES[currentDebatePhase + 1]}
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    );
  };

  const renderStep4 = () => {
    // Agrupar evolucao por rodada para o grafico
    const rounds = Array.from(new Set(opinionEvolution.map((e) => e.round))).sort((a, b) => a - b);
    const jurorNames = Array.from(new Set(opinionEvolution.map((e) => e.member_name))).filter(Boolean);

    return (
      <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6">
        {loadedFromHistory && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-50 border border-blue-200 dark:bg-blue-950/20 dark:border-blue-900">
            <History className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-700 dark:text-blue-300">Carregado do histórico</span>
          </div>
        )}
        <div className="text-center">
          <div className="verdict-sparkle inline-block">
            <Gavel className="h-8 w-8 mx-auto mb-2 text-amber-500 gavel-drop" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold mb-2 verdict-reveal">Veredicto</h2>
          {finalVerdict && (
            <Badge
              variant={finalVerdict === 'absolvido' ? 'default' : 'destructive'}
              className="text-base sm:text-lg px-4 py-1.5 verdict-reveal"
              style={{ animationDelay: '0.3s', animationFillMode: 'both' }}
            >
              {finalVerdict === 'absolvido' ? 'ABSOLVIDO' : 'CONDENADO'}
            </Badge>
          )}
        </div>

        {/* Barra de probabilidade */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Probabilidades do Veredicto</CardTitle>
            <CardDescription>Baseado na confianca ponderada dos jurados</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium w-24 text-red-600">Condenacao</span>
                <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden relative">
                  <div
                    className="h-full bg-red-500 rounded-full transition-all duration-700 flex items-center justify-end pr-2"
                    style={{ width: `${verdictProbabilities.condenacao}%` }}
                  >
                    {verdictProbabilities.condenacao > 15 && (
                      <span className="text-white text-xs font-bold">{verdictProbabilities.condenacao}%</span>
                    )}
                  </div>
                  {verdictProbabilities.condenacao <= 15 && (
                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs font-bold text-red-600">
                      {verdictProbabilities.condenacao}%
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium w-24 text-green-600">Absolvicao</span>
                <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden relative">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-700 flex items-center justify-end pr-2"
                    style={{ width: `${verdictProbabilities.absolvicao}%` }}
                  >
                    {verdictProbabilities.absolvicao > 15 && (
                      <span className="text-white text-xs font-bold">{verdictProbabilities.absolvicao}%</span>
                    )}
                  </div>
                  {verdictProbabilities.absolvicao <= 15 && (
                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs font-bold text-green-600">
                      {verdictProbabilities.absolvicao}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Evolução de opinião ao longo das rodadas */}
        {opinionEvolution.length > 0 && rounds.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Evolução de Opinião por Rodada</CardTitle>
              <CardDescription>Como cada jurado mudou de posição ao longo do debate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-1 font-medium">Jurado</th>
                      {rounds.map((r) => (
                        <th key={r} className="text-center py-2 px-1 font-medium">R{r}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {jurorNames.map((name) => (
                      <tr key={name} className="border-b last:border-0">
                        <td className="py-2 px-1 font-medium truncate max-w-[100px]">{name.split(' ')[0]}</td>
                        {rounds.map((r) => {
                          const entry = opinionEvolution.find(
                            (e) => e.member_name === name && e.round === r
                          );
                          if (!entry) return <td key={r} className="text-center py-2 px-1">-</td>;
                          return (
                            <td key={r} className="text-center py-2 px-1">
                              <Badge
                                variant="outline"
                                className={cn(
                                  'text-[9px] px-1 py-0',
                                  entry.stance === 'condenacao'
                                    ? 'border-red-300 text-red-600 bg-red-50 dark:border-red-800 dark:text-red-400 dark:bg-red-950/30'
                                    : 'border-green-300 text-green-600 bg-green-50 dark:border-green-800 dark:text-green-400 dark:bg-green-950/30'
                                )}
                              >
                                {entry.stance === 'condenacao' ? 'C' : 'A'} {(entry.confidence * 100).toFixed(0)}%
                              </Badge>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Placar final with sequential animation */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          <Card className="border-green-500/50 bg-green-500/5 score-card-enter" style={{ animationDelay: '0.5s' }}>
            <CardContent className="text-center p-4 sm:p-6">
              <p className="text-xs sm:text-sm text-muted-foreground">Absolvição</p>
              <p className="text-3xl sm:text-4xl font-bold text-green-600 score-update" key={`abs-${liveScore.absolvicao}`}>{liveScore.absolvicao}</p>
            </CardContent>
          </Card>
          <Card className="border-red-500/50 bg-red-500/5 score-card-enter" style={{ animationDelay: '0.7s' }}>
            <CardContent className="text-center p-4 sm:p-6">
              <p className="text-xs sm:text-sm text-muted-foreground">Condenação</p>
              <p className="text-3xl sm:text-4xl font-bold text-red-600 score-update" key={`cond-${liveScore.condenacao}`}>{liveScore.condenacao}</p>
            </CardContent>
          </Card>
        </div>

        {/* Resultado dos quesitos */}
        {verdictResults.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold">Votação dos Quesitos</h3>
            {verdictResults.map((qr, qrIdx) => (
              <Card key={qr.id} className="vote-reveal" style={{ animationDelay: `${qrIdx * 0.2}s`, animationFillMode: 'both' }}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{qr.label}</CardTitle>
                    <Badge variant={qr.result === 'sim' ? 'default' : 'secondary'}>
                      {qr.result === 'sim' ? 'SIM' : 'NAO'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {qr.votes.map((v, vi) => (
                      <div key={vi} className="flex items-center gap-3 text-sm quesit-vote-enter" style={{ animationDelay: `${qrIdx * 0.2 + vi * 0.1}s` }}>
                        <Avatar className="h-6 w-6">
                          <AvatarFallback className={`${JUROR_COLORS[vi % JUROR_COLORS.length]} text-white text-[10px]`}>
                            {vi + 1}
                          </AvatarFallback>
                        </Avatar>
                        <span className="font-medium w-32 truncate">{v.jurorName}</span>
                        <Badge variant={v.vote === 'sim' ? 'default' : 'outline'} className="text-xs tally-update">
                          {v.vote.toUpperCase()}
                        </Badge>
                        <span className="text-muted-foreground truncate">{v.reasoning}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Confiança individual de cada jurado */}
        {loadedFromHistory && Object.keys(jurorOpinionDetails).length > 0 ? (
          <div className="space-y-3">
            <h3 className="text-xl font-semibold">Confiança Individual dos Jurados</h3>
            <div className="grid gap-3 md:grid-cols-2">
              {Object.entries(jurorOpinionDetails).map(([id, detail], i) => (
                <Card key={id}>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-10 w-10">
                        <AvatarFallback className={`${JUROR_COLORS[i % JUROR_COLORS.length]} text-white`}>
                          {i + 1}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm">{detail.member_name || `Jurado ${i + 1}`}</p>
                      </div>
                      <Badge variant={detail.stance === 'absolvicao' ? 'default' : 'destructive'}>
                        {detail.stance === 'absolvicao' ? 'Absolvicao' : 'Condenacao'}
                      </Badge>
                    </div>
                    {detail.confidence > 0 && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Confiança</span>
                          <span>{(detail.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <Progress
                          value={detail.confidence * 100}
                          className={cn(
                            'h-2',
                            detail.stance === 'condenacao' ? '[&>div]:bg-red-500' : '[&>div]:bg-green-500'
                          )}
                        />
                      </div>
                    )}
                    {detail.reasons && (
                      <p className="text-xs text-muted-foreground mt-1">{detail.reasons}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ) : jurors.some((j) => j.name) && (
          <div className="space-y-3">
            <h3 className="text-xl font-semibold">Confiança Individual dos Jurados</h3>
            <div className="grid gap-3 md:grid-cols-2">
              {jurors.map((juror, i) => {
                const tendency = jurorTendencies.find((jt) => jt.id === juror.id);
                const stance = tendency?.tendency;
                const confidence = tendency?.confidence || 0;

                return (
                  <Card key={juror.id}>
                    <CardContent className="p-4 space-y-2">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback className={`${JUROR_COLORS[i]} text-white`}>
                            {i + 1}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">{juror.name}</p>
                          <p className="text-xs text-muted-foreground">{juror.profession}</p>
                        </div>
                        {stance && (
                          <Badge variant={stance === 'absolvicao' ? 'default' : 'destructive'}>
                            {stance === 'absolvicao' ? 'Absolvicao' : 'Condenacao'}
                          </Badge>
                        )}
                      </div>
                      {confidence > 0 && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Confiança</span>
                            <span>{(confidence * 100).toFixed(0)}%</span>
                          </div>
                          <Progress
                            value={confidence * 100}
                            className={cn(
                              'h-2',
                              stance === 'condenacao' ? '[&>div]:bg-red-500' : '[&>div]:bg-green-500'
                            )}
                          />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Relatório Analítico */}
        {analyticalReport && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <FileDown className="h-4 w-4" />
                Relatório Analítico do Julgamento
              </CardTitle>
              <CardDescription>Análise detalhada gerada pela IA após o veredicto</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="max-h-[400px]">
                <div className="prose prose-sm dark:prose-invert max-w-none text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {analyticalReport}
                  </ReactMarkdown>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Chat pós-veredicto */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              Pergunte sobre o Veredicto
            </CardTitle>
            <CardDescription>
              Explore cenários alternativos e entenda as decisões dos jurados
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Sugestões de perguntas */}
            {verdictChatHistory.length === 0 && (
              <div className="flex flex-wrap gap-2">
                {[
                  'Por que o jurado 3 votou pela condenacao?',
                  'Quais foram os argumentos mais fracos da defesa?',
                  'Se eu tivesse apresentado prova de alibi, o resultado mudaria?',
                  'Qual a probabilidade de reforma em instancia superior?',
                ].map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    size="sm"
                    className="text-xs h-auto py-1.5 px-3"
                    onClick={() => {
                      setVerdictQuestion(suggestion);
                    }}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            )}

            {/* Histórico do chat */}
            {verdictChatHistory.length > 0 && (
              <ScrollArea className="max-h-[300px]">
                <div className="space-y-3">
                  {verdictChatHistory.map((msg, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        'flex gap-2',
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      <div
                        className={cn(
                          'rounded-lg px-3 py-2 max-w-[85%] text-sm',
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        )}
                      >
                        {msg.role === 'assistant' ? (
                          <div className="prose prose-sm dark:prose-invert max-w-none [&>p]:mb-1 [&>ul]:mb-1">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        )}
                      </div>
                    </div>
                  ))}
                  {isAskingQuestion && (
                    <div className="flex gap-2 justify-start">
                      <div className="bg-muted rounded-lg px-3 py-2 text-sm flex items-center gap-2">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Analisando...
                      </div>
                    </div>
                  )}
                  <div ref={verdictChatEndRef} />
                </div>
              </ScrollArea>
            )}

            {/* Input de pergunta */}
            <div className="flex gap-2">
              <Input
                value={verdictQuestion}
                onChange={(e) => setVerdictQuestion(e.target.value)}
                placeholder="Faca uma pergunta sobre o veredicto..."
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    askVerdictQuestion();
                  }
                }}
                disabled={isAskingQuestion}
              />
              <Button
                onClick={askVerdictQuestion}
                disabled={!verdictQuestion.trim() || isAskingQuestion}
                size="icon"
              >
                {isAskingQuestion ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Actions - stacked on mobile */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button onClick={exportReport} className="flex-1" disabled={isExportingPdf}>
            {isExportingPdf ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <FileDown className="h-4 w-4 mr-2" />
            )}
            {isExportingPdf ? 'Gerando PDF...' : 'Exportar Relatorio (PDF)'}
          </Button>
          <Button variant="outline" onClick={resetSimulation} className="flex-1">
            <RotateCcw className="h-4 w-4 mr-2" />
            Nova Simulação
          </Button>
        </div>
      </div>
    );
  };

  // ─── Main Render ───

  return (
    <div className="min-h-screen flex flex-col -mx-3 sm:-mx-6 -mb-6">
      {renderStepper()}

      <div className="flex-1 p-3 sm:p-6">
        {currentStep === 0 && renderStep0()}
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
        {currentStep === 4 && renderStep4()}
        <SimulationHistoryList type="jury" />
      </div>

      {/* Navigation buttons */}
      {currentStep < 3 && (
        <div className="border-t p-3 sm:p-4 flex items-center justify-between max-w-3xl mx-auto w-full safe-area-bottom">
          <Button
            variant="outline"
            onClick={currentStep === 0 ? () => router.push('/dashboard/simulations') : prevStep}
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            {currentStep === 0 ? 'Voltar' : 'Anterior'}
          </Button>
          <Button onClick={nextStep} disabled={!canAdvance()}>
            Próximo
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      )}
    </div>
  );
}
