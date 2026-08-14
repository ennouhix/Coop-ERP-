interface LogoProps {
  className?: string;
}

/**
 * Marque de l'ERP : quatre modules métier (achat, vente, stock, comptabilité)
 * reliés à un cœur en losange, écho de la géométrie zellige.
 * Hérite de la couleur via `currentColor`.
 */
export function Logo({ className }: LogoProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="1.5" y="1.5" width="6" height="6" rx="1.5" />
      <rect x="16.5" y="1.5" width="6" height="6" rx="1.5" />
      <rect x="1.5" y="16.5" width="6" height="6" rx="1.5" />
      <rect x="16.5" y="16.5" width="6" height="6" rx="1.5" />
      <path d="M12 7.5L16.5 12L12 16.5L7.5 12Z" fill="currentColor" stroke="none" />
    </svg>
  );
}
