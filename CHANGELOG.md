# Journal des versions

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Versionnage : [SemVer](https://semver.org/lang/fr/).

Ce fichier documente **le template**, pas le projet qu'il engendre : l'amorçage
le supprime, comme `GETTING-STARTED.md` et la CI du template.

## [Non publié]

### Ajouté
- **Découverte d'architecture** à l'amorçage : sept questions fermées qui
  discriminent une stack, un run `/dejavu` proposé et chiffré sur le seul
  mécanisme dur, et `codesearch.py` seul pour vérifier les briques dans deux ou
  trois écosystèmes.
- **Gabarits d'agents de stack** (`.claude/templates/agent-stack-{developer,dba}.md`)
  déplacés vers `.claude/agents/` quand aucun module de stack n'est activé, puis
  spécialisés par l'amorçage. `dba` est supprimé si la stack n'a pas de base
  relationnelle.
- **CI du template** (`.github/workflows/template.yml`) : amorçage à blanc dans
  cinq combinaisons de modules, `shellcheck`, `compileall`, `node --check` sur le
  workflow de revue, contrôle des liens relatifs.
- **`docs/engineering/models.md`** : quel modèle tourne où et ce qu'un cycle coûte.

### Modifié
- **Laravel devient une option**, plus le chemin attendu : `stack-laravel`
  s'active parce que la découverte y aboutit, et n'est plus une question posée à
  l'interview.
- **Les quatre agents du module Laravel réécrits** : en français, sur la stack que
  le module livre réellement (Laravel 13, Filament, Horizon, PostgreSQL 16), sans
  les onze skills et deux fichiers de règles inexistants, sans les MCP `figma` et
  `ide` configurés nulle part, toutes commandes passant par le conteneur.
- **`model: sonnet` sur tous les agents.** `domain-expert` n'en déclarait aucun et
  héritait du modèle de session ; `security-scanner` était en `opus`. Les lectures
  isolées de `/dejavu` passent en `haiku` — seul écart de la copie vendorisée avec
  l'amont.
- **Un seul vocabulaire** : `H<n>` pour les hypothèses produit de `vision.md` §8,
  `D<n>` pour les décisions de `DECISIONS.md`. `/cadrer-story` ne dit plus
  « hypothèse ».

### Corrigé
- Le contrôle final de l'amorçage criait au loup sur sa propre documentation : le
  README, `GETTING-STARTED.md` et le skill citaient un exemple de placeholder en
  toutes lettres, que le motif attrapait comme un oubli.
- `.claude/agents/README.md` décrivait l'inverse de la réalité sur l'accès
  sortant : c'est `domain-expert` qui déclare `WebSearch`, pas `security-scanner`.
- Le tableau d'outillage de `CLAUDE.md` présentait `context7`, `github` et
  `playwright` comme acquis. Les deux premiers viennent du module Laravel, le
  troisième n'est fourni par rien.
- `CONTRIBUTING.md` ne disait pas qu'il appartient au projet engendré : l'encart
  « Contributing » de GitHub y envoyait un visiteur lire un fichier à placeholder.

## [0.1.0] — 2026-09-15

Premier état publiable. Agrège les trois premières pull requests ; la #1 a été
mergée le 2026-09-05, les deux autres le 2026-09-15.

### Ajouté
- `/cadrer-story` et `docs/backlog/DECISIONS.md` — le maillon qui écrit les
  stories, et le journal qui permet au cadrage de tourner sans s'arrêter (#2).
- Module `dejavu` : le skill d'antériorité embarqué et versionné avec le projet,
  scripts Python en bibliothèque standard seule (#2).
- README bilingue anglais puis français, avec ce qu'un run coûte, comment
  vérifier l'amorçage et un glossaire (#3).
- Licence MIT (#1).

### Modifié
- Cœur réduit aux trois agents que la revue invoque réellement ; neuf agents
  importés supprimés (#1).
- `scripts/bootstrap.sh` portable entre BSD et GNU (`sed -i.bak`), avec un trap
  qui nettoie les sauvegardes quelle que soit la sortie (#1).
- Le garde CI `Backend scaffoldé ?` lit son prédicat sur la branche de base : une
  PR ne peut plus sauter les gates en supprimant un fichier (#1).
- `gh pr checks --watch --fail-fast` à la place de `gh run watch`, qui exige un
  identifiant de run et bloque une boucle en le demandant (#1).
- Origine désidentifiée, métrique non vérifiable retirée (#3).

### Corrigé
- Un nœud de revue mort était compté comme un rapport vide : `agent()` résout à
  `null` sans lever, et le `?? []` transformait le silence en « rien à signaler »
  (#1).

[Non publié]: https://github.com/jamyl/socle/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jamyl/socle/releases/tag/v0.1.0
