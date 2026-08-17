# Sous-agents — réserves à connaître

Onze agents génériques ici, quatre de plus si le module `stack-laravel` est
activé. **Ils sont repris tels quels d'un jeu importé** (`AratKruglik/claude-laravel`),
triés mais pas réécrits. Ce fichier dit ce qu'ils ne savent pas — le lire avant
de croire l'un d'eux.

## Ce qu'ils ignorent tous

- **Le backlog, le journal et les règles du domaine.** Aucun n'a lu
  `CLAUDE.md` § « règles qui coûtent le plus cher à violer ». Un agent qui
  propose une solution correcte en général peut violer un invariant du projet
  sans le savoir.
- **La méthode.** Ils ne connaissent ni le cycle `deliver-story`, ni la
  discipline de contre-épreuve, ni le passage obligatoire par une PR.

**Leur travail passe par les mêmes tests et la même revue que le tien.** Onze
d'entre eux peuvent écrire et lancer des commandes.

## Réserves précises

- **Plusieurs supposent Vue/Inertia.** Le module `stack-laravel` fait du
  **Filament**, pas de l'Inertia : `reviewer`, `debugger`, `ddd-architect`,
  `integration-architect` et `ba` mentionnent des `Inertia props`, des pages Vue
  ou `routes/web.php` en mode Inertia. Ces passages sont **hors sujet ici** —
  les ignorer, pas les appliquer.
- **`developer` référence `figma`/`stitch`**, MCP absents et non prévus. Il
  travaillera sans, mais ses instructions de design ne mèneront nulle part.
- **`dba` est bridé en lecture seule** (`Edit`/`Write`/`Bash` retirés). Son
  métier est d'écrire des migrations, or les nôtres sont additives et passent par
  le cycle de story. **Il propose, le cycle applique.**
- **`security-scanner` et `reviewer` ne remplacent pas `/security-review`.** Sur
  le projet d'origine, c'est `/security-review` qui a trouvé une faille
  exploitable à *chaque* story du domaine critique. Ne jamais le remplacer par
  l'automatique.
- **`tester` ne remplace pas le cycle TDD** de `deliver-story`.
- **`qa` dépend du MCP `playwright`.** Sans lui, il ne peut rien vérifier. Le nom
  d'un outil peut avoir changé côté serveur — si un appel échoue sur un nom
  inconnu, c'est la piste.

## Ce qui a été retiré du jeu importé, et pourquoi

- **`frontend`** (Vue/Inertia) : ne correspond à aucune stack du template.
- **`filament`** : visait une version antérieure à celle du module. Il aurait
  produit du code pour une stack qui n'est pas la nôtre — le pire cas, parce
  qu'il compile.
- **Les 7 outils MCP GitHub d'écriture** (`push_files`, `create_pull_request`,
  `create_branch`…) réclamés par `devops`, `docs-writer` et `reviewer`. Ce projet
  fait des PR, mais par le **CLI `gh` en local, après les tests**. `push_files`
  permettrait de pousser du code sans passer par la suite locale — exactement ce
  que la PR est censée empêcher. **Ne pas retirer `--read-only` du `.mcp.json`.**

## `domain-expert` : le seul à spécialiser

C'est le seul agent de ce dossier que `/bootstrap-project` **doit** réécrire, et
c'est celui qui compte. Il porte les invariants du domaine et alimente le
troisième nœud de la revue en fan-out.

**S'il ne trouve jamais rien, il n'a pas été spécialisé.** Vérifier alors qu'il
ne contient plus ni `{{…}}` ni les blocs « À REMPLIR », et que ses invariants
sont les mêmes que ceux de `.claude/workflows/review-story.js`.
