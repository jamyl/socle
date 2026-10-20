# Fiabilité des agents — qui fait, qui vérifie, qui merge

Comme pour un virement : **celui qui fait n'est pas celui qui valide.** Deux
résultats publiés fondent cette règle :
- un agent de code triche quand il peut toucher ce qui le juge.
  [EvilGenie](https://arxiv.org/abs/2511.21654) (2025) a pris Claude Code
  (Sonnet 4) à coder en dur des cas de test, sur 2,1 % des problèmes, et Gemini
  CLI à modifier ou supprimer des fichiers de test ;
- un modèle évaluateur reconnaît ses propres productions et les préfère
  (Panickssery et al., 2024, *LLM Evaluators Recognize and Favor Their Own
  Generations*).

D'où la règle de ce dépôt : **les machines décident, l'IA conseille.**

```
L'agent écrit            compte agent séparé, sans droit sur .github/workflows
   ↓
CI GitHub, sans IA       tests, analyse statique, garde des tests, mutation   → DÉCIDE
   ↓
review-story             relecteurs à l'aveugle, grille, verdict MERGE|HUMAIN  → CONSEILLE
   ↓
CI verte + MERGE         le robot Fusion merge (l'agent n'a que la lecture) ; sinon le propriétaire
   ↓
Alarme de merge          issue si un contrôle n'était pas vert                 → SIGNALE
```

## Les pièces, et pourquoi l'agent ne peut pas les contourner

| Pièce | Fichier | Pourquoi l'agent ne peut pas la contourner |
|---|---|---|
| Compte agent séparé | `.claude/settings.local.json` (non commité), voir `config-locale.md` | Son jeton n'a pas la portée `workflow` : GitHub refuse tout push qui touche `.github/workflows/` |
| Garde des tests | `.github/workflows/integrite.yml` | Logique écrite dans le workflow ; motifs par stack lus sur la **base** de la PR (`.github/integrite.d/`). Rouge si : test supprimé, contournement ajouté, assertion existante modifiée ou retirée, nombre de tests en baisse, fichier de règles modifié |
| Mutation | job `mutation` de `backend.yml` (module `stack-laravel`) | Classes modifiées des dossiers sensibles ; seuil lu sur la base, qui ne se baisse jamais |
| Verdict de revue | `.claude/workflows/review-story.js`, `eval-run.mjs verdict` | Relecteurs en lecture seule, qui ne voient ni la PR, ni les commits, ni l'avis de l'auteur ; grille et verdict **calculés en code** ; un seul verdict par commit. **C'est un conseil, pas un verrou** : l'agent lance la revue lui-même |
| Garde du merge | `.claude/hooks/guard-bash.mjs` | Refuse `gh pr merge` sans verdict `MERGE` pour le commit relu. Rattrape l'oubli, pas la triche : un hook lit la commande telle qu'elle est écrite |
| Robot de fusion (mode organisation) | `.github/workflows/fusion.yml` | Le compte agent n'a que la lecture et ne peut pas merger. Le robot exécute la version de `main`, ne lit jamais le code de la PR, refuse une PR qui touche `.github/`, exige tous les contrôles verts, les indispensables présents, et `VERDICT: MERGE <sha>` du compte agent pour ce commit. Il merge avec `--match-head-commit` |
| Alarme de merge | `.github/workflows/alarme-merge.yml` | Sans GitHub Pro, rien n'empêche un merge sur du rouge : l'alarme le rend visible, par une issue au propriétaire |

## Ce que chaque pièce a montré

- **Garde des tests** : rejouée sur les 8 dernières PR d'un projet réel, les 8
  passent. Sur une copie piégée, elle nomme les 5 tricheries (fichier supprimé,
  `skip` ajouté, assertion affaiblie, nombre de tests en baisse, configuration
  de tests modifiée) et sort en code 1.
- **Mutation** : sur le même projet, elle a trouvé un trou que les
  contre-épreuves faites à la main avaient raté.
- **Robot de fusion** : éprouvé sur le même projet, monté en organisation. Le
  merge est refusé au compte agent, une PR verte de sa copie est mergée par
  `github-actions`, une PR rouge reste ouverte, un push de workflow par l'agent
  est refusé, et la CI des PR de fork tourne sans clic. Dans socle, sa logique
  est rejouée sur 13 scénarios contre un faux `gh` (PR #21).
- **Alarme** : sur ce dépôt, elle a d'abord crié au push direct pour un merge
  normal. GitHub met quelques secondes à rattacher un commit à sa PR. Elle
  réessaie maintenant avant de conclure.

## Limites assumées

- **Sur un dépôt personnel, sans GitHub Pro, la règle de merge est une méthode
  surveillée, pas un verrou.** L'alarme signale, elle n'empêche pas. **En mode
  organisation, c'est un verrou** : le compte agent n'a pas le droit de merger.
  Le verdict, lui, reste un conseil, puisque c'est l'agent qui le pose. Ce qui
  décide, ce sont les contrôles de la CI qu'il ne peut pas modifier.
- **Même famille de modèles.** Sonnet relit ce qu'Opus écrit. L'aveugle, la
  grille et un verdict calculé en code **atténuent** le biais « je préfère ce qui
  me ressemble », sans le supprimer. Les relecteurs déclarent l'ID complet
  `claude-sonnet-5-5` : une surcharge de l'alias `sonnet` vers Opus ferait de
  l'auteur et du relecteur le même modèle.
- **Une garde rouge n'est pas une accusation.** Modifier une assertion est
  parfois légitime, quand la story change le comportement attendu : c'est alors
  le propriétaire qui merge.
- **Un projet adopté** (`scripts/adopt.sh`) ne reçoit pas la CI : la garde et
  l'alarme se copient à la main depuis le gabarit.
- **Contre-épreuve sur une copie de travail : toujours
  `git worktree add --detach`.** Sans `--detach`, la copie prend la branche
  nommée, et un commit de test y atterrit.
