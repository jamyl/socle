# Template — Design system

> Usage : produire le socle UI **avant** les écrans. Un design system écrit après
> coup ne fait que constater les incohérences déjà livrées.
>
> 🔧 Remplace les `[…]` et adapte les invariants au projet.

## Invariants NON négociables

- `[Contrainte typographique et directionnelle — ex. : la typo doit rendre
  correctement telle écriture ; tout composant est pensé LTR ET RTL en miroir,
  pas rétrofité. Des tests de rendu dans chaque sens sont exigés.]`
- **Tokens, jamais de valeurs en dur** : couleurs, typographie et espacements
  exposés comme tokens réutilisables. Une valeur en dur se propage par copie et
  ne se corrige plus jamais partout.
- **Contraste vérifié**, pas estimé — AA au minimum, mesuré.
- **Sobriété** : un jeu de composants couvrant le jalon en cours, rien de
  spéculatif.

## Sources de vérité à lire d'abord

- `docs/backlog/[epic UI]` (les critères exacts du socle)
- `docs/engineering/stack.md` (framework d'interface, mécanisme d'i18n)
- `docs/product/vision.md` (positionnement, ce que la marque doit inspirer)

## Prompt

Agis comme un designer UI de premier plan, expert `[écritures / plateformes
concernées]`. Crée le design system de `[NOM]`, ambiance `[STYLE DE MARQUE]`.

Fournis :

1. **Palette** par **rôles** — primaire, surface, succès, erreur, alerte — en
   tokens, contraste AA **vérifié et chiffré**.
   > Des rôles, pas des noms de couleurs : « erreur » survit à un changement de
   > charte, « rouge » non.
2. **Typographie** : échelle + police compatible avec toutes les écritures
   cibles, **avec justification du choix**. Tailles en tokens.
3. **Espacements** : une échelle unique (4/8 pt), en tokens.
4. **Composants de base** : boutons, champs, cartes, listes, bandeaux
   (hors-ligne, erreur) — et pour chacun ses **états vide / chargement /
   erreur**.
5. **Patterns de navigation** et style d'onboarding.
6. **Icônes** : jeu retenu et style.
7. **Preuve directionnelle** : pour 2-3 composants clés, le rendu décrit dans
   **chaque** sens d'écriture. Un composant « qui devrait marcher en RTL » ne
   marche pas en RTL.

Contrainte : tout est exprimé en **tokens et composants réutilisables**, prêts à
traduire en thème, jamais en maquettes figées.
