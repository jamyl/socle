# Template — Spec UX écran par écran

> Usage : produire `docs/product/ux-flows.md` avant de coder des écrans.
> Une spec écrite après les écrans ne sert qu'à les décrire ; écrite avant, elle
> évite les écrans qu'on aurait jetés.
>
> 🔧 Remplace les `[…]` et la section « invariants » par ceux du projet.

## Invariants NON négociables (à respecter dans toute la spec)

- `[Invariant de domaine n°1 — ce qu'aucun écran ne doit jamais suggérer.
  C'est le plus important : un écran qui promet ce que le produit ne fait pas
  crée une attente que le support paiera.]`
- **La source de vérité est le serveur** : tout chiffre affiché vient de lui,
  aucun calcul côté client. `[Adapter si le projet a une raison contraire.]`
- `[Langues et sens d'écriture obligatoires — chaque écran spécifié dans
  chacune, layout miroir vérifié si RTL. La microcopy est livrée traduite,
  pas « à traduire plus tard ».]`
- **Sobriété** : aucun écran ni état spéculatif hors du parcours du jalon en
  cours.

## Sources de vérité à lire d'abord

- `docs/product/vision.md` (personas et périmètre)
- `docs/backlog/[epic concerné]` (les écrans à couvrir et leurs critères)
- `docs/engineering/stack.md` (forme des erreurs, mécanisme d'i18n)

## Prompt

Agis comme un designer UX senior spécialisé `[type de produit et contrainte
dominante : multilingue, offline, forte charge réglementaire…]`.

Rédige une spec UX **écran par écran** pour `[NOM]`, style `[STYLE]`.

Écrans à couvrir : `[liste exhaustive du parcours du jalon]`.

Pour **chaque** écran, fournis :

1. **But** de l'écran et sa place dans le parcours.
2. **Action principale** — le seul CTA qui compte — puis les secondaires.
3. **Éléments UI**, cohérents avec le design system.
4. **États** : nominal, **vide**, **chargement**, **erreur** (messages
   actionnables), et **hors-ligne** si le produit y est exposé.
   > Ce sont les trois derniers qu'on oublie, et ceux que l'utilisateur voit le
   > jour où ça compte.
5. **Microcopy dans toutes les langues obligatoires** : titres, boutons, erreurs,
   états vides.
6. **Hook de rétention** éventuel — **sans dark pattern**. Si le hook ne survit
   pas à la question « est-ce que je l'accepterais pour moi ? », il n'entre pas.

Contraintes : respecte les invariants ci-dessus ; aucune donnée sensible affichée
sans ré-authentification.

Termine par la **liste complète des écrans de l'epic** avec une case cochée par
écran couvert — c'est ainsi qu'on voit un écran orphelin.
