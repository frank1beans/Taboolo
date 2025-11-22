interface ExplorerBreadcrumbProps {
  items: { label: string }[];
  onNavigate?: (index: number) => void;
}

export const ExplorerBreadcrumb = ({
  items,
  onNavigate,
}: ExplorerBreadcrumbProps) => {
  return (
    <nav className="flex items-center gap-1 text-sm text-muted-foreground" aria-label="Percorso cartelle">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <span key={item.label} className="inline-flex items-center gap-1">
            <button
              type="button"
              className={`rounded px-1 py-0.5 text-sm ${isLast ? "text-foreground font-semibold" : "hover:text-foreground"}`}
              onClick={() => {
                if (!isLast) onNavigate?.(index);
              }}
              disabled={isLast}
            >
              {item.label}
            </button>
            {!isLast ? <span className="text-muted-foreground">/</span> : null}
          </span>
        );
      })}
    </nav>
  );
};
