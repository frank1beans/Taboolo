import { ReactNode } from "react";
import { FolderTile, FolderTileProps } from "./FolderTile";

interface FolderGridProps {
  title?: string;
  description?: string;
  items: FolderTileProps[];
  emptyContent?: ReactNode;
}

export const FolderGrid = ({
  title,
  description,
  items,
  emptyContent,
}: FolderGridProps) => {
  return (
    <section className="space-y-4">
      {(title || description) && (
        <div>
          {title ? <h3 className="text-lg font-semibold">{title}</h3> : null}
          {description ? (
            <p className="text-sm text-muted-foreground">{description}</p>
          ) : null}
        </div>
      )}

      {items.length ? (
        <div className="grid gap-4 grid-cols-[repeat(auto-fit,_minmax(260px,_1fr))]">
          {items.map((item) => (
            <FolderTile key={item.id ?? `${item.title}-${item.subtitle ?? "folder"}`} {...item} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
          {emptyContent ?? "Nessun elemento disponibile in questa cartella."}
        </div>
      )}
    </section>
  );
};
