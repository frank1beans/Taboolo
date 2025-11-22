import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageShellProps = {
  title: string;
  description?: string;
  breadcrumb?: ReactNode;
  toolbar?: ReactNode;
  headerAside?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
};

/**
 * Struttura pagina compatta e coerente:
 * - Header sempre visibile e allineato
 * - Toolbar opzionale sotto l'header
 * - Corpo con overflow controllato per evitare scroll della pagina intera
 */
export function PageShell({
  title,
  description,
  breadcrumb,
  toolbar,
  headerAside,
  children,
  className,
  bodyClassName,
}: PageShellProps) {
  return (
    <div className={cn("workspace-shell", className)}>
      <div className="workspace-inner">
        {breadcrumb ? <div className="workspace-breadcrumb">{breadcrumb}</div> : null}

        <div className="workspace-header">
          <div className="workspace-heading">
            <h1 className="workspace-title">{title}</h1>
            {description ? <p className="workspace-subtitle">{description}</p> : null}
          </div>
          {headerAside ? <div className="workspace-header-aside">{headerAside}</div> : null}
        </div>

        {toolbar ? <div className="workspace-toolbar">{toolbar}</div> : null}

        <div className={cn("workspace-body", bodyClassName)}>{children}</div>
      </div>
    </div>
  );
}
