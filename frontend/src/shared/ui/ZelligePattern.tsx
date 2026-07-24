/**
 * Motif signature de la marque — inspiré des entrelacs géométriques du
 * zellige marocain, simplifié en tracé fin. Utilisé UNIQUEMENT sur l'écran
 * de connexion : sur les écrans de données, il nuirait à la lisibilité.
 * C'est le seul "accessoire" décoratif de toute l'interface.
 */
export function ZelligePattern({ className = "" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <pattern id="zellige" width="50" height="50" patternUnits="userSpaceOnUse">
          <path
            d="M25 0 L50 25 L25 50 L0 25 Z M25 10 L40 25 L25 40 L10 25 Z"
            stroke="currentColor"
            strokeWidth="0.75"
            fill="none"
          />
        </pattern>
      </defs>
      <rect width="200" height="200" fill="url(#zellige)" />
    </svg>
  );
}
