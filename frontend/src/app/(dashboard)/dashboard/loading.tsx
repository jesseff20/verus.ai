export default function ContentLoading() {
  return (
    <div className="p-6 max-w-6xl mx-auto animate-pulse">
      {/* Header skeleton */}
      <div className="mb-8 space-y-2">
        <div className="h-7 w-56 rounded-lg bg-muted" />
        <div className="h-4 w-80 rounded bg-muted/70" />
      </div>

      {/* Content skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-36 rounded-xl bg-muted border border-border"
          />
        ))}
      </div>
    </div>
  );
}
