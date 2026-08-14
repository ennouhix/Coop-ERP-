import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  /** Étiquette au-dessus du titre (petit texte mono, ex. « Gestion », « Comptabilité »). */
  eyebrow?: string;
  /** Zone d'action à droite du titre (boutons, filtres...). */
  children?: ReactNode;
}

/**
 * En-tête de page standard : règle ocre, titre de facture « atelier »,
 * sous-titre et actions. Chaque écran de données l'utilise pour garder
 * une identité commune, y compris en arabe (RTL).
 */
export function PageHeader({ title, subtitle, eyebrow, children }: PageHeaderProps) {
  return (
    <div className="page-heading">
      <div>
        <div className="flex items-start gap-3">
          <span aria-hidden="true" className="page-heading-rule mt-1" />
          <div>
            {eyebrow && <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ochre-600">{eyebrow}</p>}
            <h1>{title}</h1>
            {subtitle && <p className="page-heading-subtitle">{subtitle}</p>}
          </div>
        </div>
      </div>
      {children && <div className="flex shrink-0 flex-wrap items-center gap-2">{children}</div>}
    </div>
  );
}
