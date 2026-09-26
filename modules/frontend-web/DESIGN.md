# DESIGN.md — le système visuel du projet

> Lu par tout agent **avant** d'écrire une ligne d'interface. Format DESIGN.md
> (Google Stitch), en français. Les valeurs vivent dans `design/tokens.json` :
> ce fichier dit **pourquoi** et **quand**, le JSON dit **combien**. Quand l'un
> bouge, l'autre bouge.
>
> À REMPLIR au bootstrap, depuis une maquette, une référence ou une
> interview. Un DESIGN.md vague donne
> une interface générique : chaque section finit par une règle vérifiable.

## 1. Atmosphère

À REMPLIR — trois adjectifs et ce qu'ils excluent. Ex. : « sobre, dense,
technique — pas de dégradés, pas d'illustrations ».

## 2. Couleurs et rôles

| Rôle | Token | Usage | Jamais |
|---|---|---|---|
| Fond | `--color-fond` | À REMPLIR | |
| Texte | `--color-texte` | | |
| Accent | `--color-accent` | une action principale par écran | décoration |

Contraste texte/fond ≥ 4,5:1 (WCAG AA) — axe le vérifie.

## 3. Typographie

À REMPLIR — familles (une ou deux), échelle (tailles et interlignages), graisses
autorisées. Longueur de ligne ≤ 80 caractères.

## 4. Composants

À REMPLIR — pour chaque composant du socle UI : ses états **tous dessinés**
(repos, survol, focus, désactivé, chargement, erreur, vide).

## 5. Mise en page

À REMPLIR — grille, espacements (uniquement `--espace-*`), points de rupture.

## 6. Profondeur et mouvement

À REMPLIR — ombres, rayons, durées. Toute animation respecte
`prefers-reduced-motion`.

## 7. À faire / à ne pas faire

À REMPLIR — les défauts à refuser nommément. Ex. : « pas de police Inter par
défaut, pas de dégradé violet, pas de cartes aux coins arrondis uniformes ».
