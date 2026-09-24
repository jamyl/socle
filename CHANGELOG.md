# Journal des versions

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Versionnage : [SemVer](https://semver.org/lang/fr/).

Ce fichier documente **le template**, pas le projet qu'il engendre : l'amorçage
le supprime, comme `GETTING-STARTED.md` et la CI du template.

## [Non publié]

### Ajouté
- **Hooks qui tiennent les interdits** (`.claude/hooks/`) : `guard-bash.mjs`
  refuse un push vers `main` sous toutes ses formes, un push forcé,
  `--no-verify`, et `gh pr merge` sur une story dont le dernier essai n'est pas
  vert ; `stop-gate.mjs`, opt-in, empêche l'agent de s'arrêter sur un rouge non
  consigné. Idée reprise de Shopify Helix : une revue est une gate, pas un
  conseil. Le bloc `deny` que la documentation décrivait est enfin commité, et le
  plugin `dart-flutter`, hors liste blanche, retiré de `settings.json`.
- **Boucle d'exploration bornée** (`.claude/rules/exploration-policy.md`) : deux
  essais au plus par hypothèse, pré-vol obligatoire sur les essais passés, et
  interdiction de contourner un test. Le garde est tenu par
  `.claude/skills/deliver-story/scripts/eval-run.mjs`, qui refuse en code 3 un
  troisième essai sur une hypothèse morte — avant d'exécuter quoi que ce soit.
- **Scorer d'essais** : `eval-run.mjs attempt` exécute les commandes de
  `stack.md` §5, note trois dimensions (secrets, tests, analyse statique),
  détecte les boucles par empreinte de l'arbre de travail et signature d'échec,
  et consigne chaque essai dans `.socle/runs/<story>/`. `preflight` rend le
  cache lisible, `retro` en tire le ratio essais/réussite et les lignes à coller
  dans `JOURNAL.md` et `DECISIONS.md`. Zéro dépendance, zéro appel de modèle.
- **Banc de tests du scorer** : 20 tests `node --test`, dont la régression des
  deux strikes. Ils ont trouvé deux vrais défauts avant la première utilisation.
- **`scan-secrets.sh` remonté dans le cœur** : tout projet en hérite, avec ou
  sans module de stack, et la dimension « secrets » du scorer existe partout.
- **Chemin d'adoption pour un projet existant** : `scripts/adopt.sh` copie la
  méthode sans jamais écraser (un `CLAUDE.socle.md` se dépose à côté d'un
  `CLAUDE.md` existant, `.gitignore` ne reçoit que ses lignes manquantes,
  `README.md` et `LICENSE` ne sont pas touchés), et le skill `/adopter-socle`
  déduit la stack en lisant le dépôt au lieu de l'interviewer. `--stack <module>`
  reprend les agents et règles d'un module sans son infrastructure.
- **`docs/engineering/config-locale.md`** : ce qui se commite, ce qui reste local,
  et pourquoi une liste `deny` n'est pas un contrôle de sécurité.
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
- **Vidéo de présentation** en tête du README (24 s, sans commentaire audio) :
  un GIF de 713 Ko qui joue en ligne, et le MP4 1080p avec le son en lien. Tout
  le texte à l'écran est réel — extrait du README ou de la sortie de
  `eval-run.mjs`. GitHub retire la balise `<video>` de tout README, chemin
  relatif comme URL absolue : l'image animée est le seul format qui se lise sans
  clic. L'amorçage supprime `docs/assets/` — la vidéo documente le template, pas
  le projet engendré.

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
- **README en français d'abord**, puis en anglais, et deux sections de plus par
  langue : l'adoption dans un projet existant, et la configuration locale.
- **`/deliver-story` gagne sa boucle d'exploration** : §3 décrit ce qu'on fait
  quand un rouge résiste, §4 cite l'essai consigné plutôt qu'une seconde
  exécution à la main, §5 lance la rétrospective avant la ligne de journal — qui
  porte désormais le nombre d'essais.
- **Node devient un prérequis du cœur**, plus seulement du module Laravel : le
  scorer d'essais en a besoin sur chaque story.

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
