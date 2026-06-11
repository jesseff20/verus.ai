export default function DashboardLoading() {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-primary/20 border-t-primary" />
        <p className="text-sm text-muted-foreground font-mono tracking-wide">
          Carregando...
        </p>
      </div>
    </div>
  );
}
