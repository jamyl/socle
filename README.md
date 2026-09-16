# socle

A project template for Claude Code. The working method ships with it; your
domain gets filled in by an interview the first time you run it.

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-2.1.154%2B-blue)](https://claude.com/claude-code)

**[English](#english) · [Français](#français)**

---

## English

- [What this is](#what-this-is)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [What the bootstrap asks you](#what-the-bootstrap-asks-you)
- [The daily cycle](#the-daily-cycle)
- [What's inside](#whats-inside)
- [Optional modules](#optional-modules)
- [What it leaves out, on purpose](#what-it-leaves-out-on-purpose)
- [What a run costs](#what-a-run-costs)
- [Check that it worked](#check-that-it-worked)
- [Words used here](#words-used-here)
- [When something breaks](#when-something-breaks)
- [Contributing](#contributing)
- [Origin and license](#origin-and-license)

### What this is

Building software with an AI coding agent has two recurring problems. You
re-explain your rules every session, and you have to take the agent's word that
the tests pass.

This template removes both. The method lives in files that Claude Code reads on
its own, so the rules survive between sessions. And every report the agent
writes ends with a command *you* run to check the result yourself, so you never
have to believe a claim you can't reproduce.

What you get is a repository where one command delivers a user story from branch
to merged pull request, a code review where three independent readers examine the
same change without seeing each other's findings, and one firm rule: a test only
counts as proof once somebody has watched it fail.

The template ships no application code and no business rules. It asks for yours.

New to Claude Code? Every term on this page is defined in
[Words used here](#words-used-here). Read that section first if *skill*,
*subagent*, *story*, or *epic* isn't already familiar.

### Requirements

Check these once per machine, before you start:

| Tool | Check it with | If it's missing |
|---|---|---|
| Claude Code 2.1.154 or later | `claude --version` | Update. Below that version the Workflow tool doesn't exist, and the three-reader review silently doesn't run |
| GitHub CLI, signed in | `gh auth status` | `gh auth login` |
| Node.js | `node --version` | Needed by the `context7` documentation server in the Laravel module |
| Python 3 | `python3 --version` | Needed by the `dejavu` module. Its scripts use the standard library only, so there's nothing to install with `pip` |
| A container runtime | `docker compose version` | Install Docker Desktop, or OrbStack on macOS. Needed by the `stack-laravel` module |

Node.js, Python, and Docker are each tied to one optional module. Skip the ones
whose module you don't activate.

### Quickstart

Three steps take you from nothing to a project with its first epic written.

1. Create your repository from this template:

   ```bash
   gh repo create my-project --template jamyl/socle --private --clone
   cd my-project
   ```

   You should now see `CLAUDE.md`, `GETTING-STARTED.md`, `modules/`, and
   `scripts/bootstrap.sh`. If `modules/` is absent, the copy was incomplete;
   start over.

2. Open a session and bootstrap the project:

   ```bash
   claude
   ```

   Then, inside the session, run `/bootstrap-project`. This is a **skill** — a
   named instruction set that Claude Code loads on demand, invoked with a
   leading slash. The bootstrap runs once, interviews you, writes your
   documentation, and then deletes itself.

3. Deliver the first story:

   ```text
   /deliver-story
   ```

Read [GETTING-STARTED.md](GETTING-STARTED.md) in full before step 2. It covers
prerequisites, each step in detail, what to check, and what to do when something
goes wrong. The bootstrap deletes that file too, because it describes the
template rather than your project.

### What the bootstrap asks you

The interview comes in four rounds, and you're asked to approve the result
before anything gets written.

1. **Identity** — the project name, a slug in kebab-case for container and
   database names, and the purpose in one sentence.
2. **Product** — who uses it and for what, what has to work before you can say
   the product exists, and what is explicitly out of scope.
3. **Constraints and architecture** — legal or regulatory obligations, hosting
   target, the languages your team debugs in production, scale at twelve months,
   realtime or offline needs, your deadline, and any stack you've already been
   handed.
4. **The rules that cost the most to break** — three to five invariants of your
   domain, each phrased so a test can check it.

Round 4 decides the quality of everything that follows. Those rules become the
checklist that one of the three reviewers applies to *every* change, for as long
as the project lives. "No code outside X writes to Y" can be checked. "The code
should be clean" cannot. A vague answer here produces a vague review for months.

After the interview, the agent names the hard mechanism in your design, if there
is one — concurrency, consistency, offline sync — and offers a prior-art search
on it, with the cost stated, then waits. It checks two or three candidate
ecosystems for maintained implementations of the building blocks you need, which
costs nothing but a few HTTP requests. Then it proposes one stack, one
alternative, and the sentence that rules the alternative out.

**Laravel is one possible outcome, not the default.** The `stack-laravel` module
activates because the discovery lands on PHP; any other answer gets a stack
written from the interview and a `developer` subagent generated for it.

Nothing is written before you approve.

### The daily cycle

Two commands carry the work, and each leaves a trace on disk:

```text
/cadrer-story "<a raw requirement>"
      |
      v   2 to 5 stories written to an epic file, in Given/When/Then form
      |
/deliver-story
      |
      v   branch -> plan -> TDD -> tests green -> three-reader review
      |   -> pull request -> CI green -> squash merge
      |
docs/backlog/JOURNAL.md        one line per delivery
docs/backlog/DECISIONS.md      one line per call made without asking you
```

To chain several stories without retyping, run `/loop 10m /deliver-story E01`.
The loop stops on its own when no story in scope is still actionable.

Writing a story and delivering it are separate commands on purpose. A badly
framed story discovered during delivery costs a branch that's already open and a
plan that's already written. Discovered during framing, it costs a re-read.

### What's inside

**The delivery cycle.** `/deliver-story` picks the next actionable story by
walking the dependency graph, not a fixed list. A story whose prerequisite lives
in a later epic gets skipped, then becomes a candidate again once that
prerequisite ships. If a story needs a human — a legal opinion, an account with
a third party, an API key — it's marked `blocked` with the reason, and the agent
moves to the next one instead of losing a turn discovering the wall.

**Counter-proof discipline.** A test is proof only once you've seen it fail.
Before writing "this is covered", the agent removes the guard the test claims to
protect, re-runs it, confirms red, and restores. The skill carries eight
concrete ways a test can stay green while proving nothing: tautology, missing
setup, a race timed with `sleep` instead of a signal, a guard that's duplicated
elsewhere, and four more. All eight were met in practice, within two days. The
question that summarizes them: *what would this test have to see to turn red?*

**The three-reader review.** After the tests pass, three read-only subagents
read the same diff in parallel without seeing each other's findings:
`reviewer` for conventions and structure, `security-scanner` for
vulnerabilities, and `domain-expert` for your own invariants. Their findings are
deduplicated and sorted in code, not by a model. Their tools are limited to
reading files: no editing, no shell. `reviewer` and `security-scanner` have no
network access at all, because their input is a diff someone else may have
written. `domain-expert` keeps web search, so it can check a regulatory text.
That's structural, not a promise in a prompt.

If one reader returns nothing at all, the workflow says so. Incomplete coverage
is not the same as "nothing to report", and treating the two alike is how a
review quietly stops being a review.

**Prior art before architecture.** The `dejavu` module searches published
research for the hard part of your design before you rebuild it. It reads one
paper per isolated subagent, so no source anchors another, then commits to a
single recommended path with citations. Conclusions get recorded in
`docs/engineering/prior-art.md` with their identifiers, because a conclusion
nobody can reopen gets re-researched next session.

**Eleven test levels.** `docs/engineering/testing-strategy.md` defines levels N1
to N11, each with its scope and the moment it runs in CI. Two of them are the
ones most projects skip and the ones that find the expensive defects: N4 runs
concurrent operations as real processes and proves the executions actually
overlapped, and N6 runs mutation testing on the critical domain only.

### Optional modules

You choose modules during the interview. Nothing is copied unless you ask for it.

| Module | What it adds | Activate it when |
|---|---|---|
| `stack-laravel` | Docker Compose with PHP 8.4, PostgreSQL 16, Redis, Mailpit, and Horizon, all images pinned by digest. GitHub Actions running Pint, Larastan level 8, Pest on PostgreSQL, and a dependency audit. A secret scanner, four Laravel subagents, and a pre-written first epic | The architecture discovery lands on PHP and Laravel |
| `mobile-flutter` | A `mobile/` directory, toolchain stories that start out `blocked` because Xcode and Android Studio can't be automated, and visual regression test levels | You're building an iOS, Android, or PWA app |
| `dejavu` | The `/dejavu` prior-art skill embedded in your repository and versioned with it. Four academic sources, no API keys, standard-library Python | Your architecture has a non-trivial mechanism. Skip it if your machine already has `/dejavu` installed globally |

The module rows say *when the discovery lands there*, not what you pick up front.

With no stack module you get the core: the method, the skills, three read-only
reviewers, and documentation skeletons. The bootstrap then writes `stack.md` and
`testing-strategy.md` from the discovery, and generates a `developer` subagent —
plus `dba` when there's a relational database — from `.claude/templates/`.

### What it leaves out, on purpose

**No application scaffold.** Neither `composer create-project` nor
`flutter create` ships here. The scaffold is born in the first delivery
iteration, with that day's versions. A scaffold frozen inside a template rots
within months, and nobody notices before they've built on top of it.

**No business domain.** The template asks for your invariants rather than
assuming any.

**No complete backlog.** The bootstrap writes the first epic and nothing else.
Epics written months before they're needed are epics you rewrite.

### What a run costs

These commands spawn subagents and make real network calls. Know the cost before
you start a loop.

| Action | What it spends |
|---|---|
| One three-reader review | 3 subagents, one per reader, on every story |
| One `/dejavu` search | Roughly 18 to 26 agent-shaped calls (1 categorize, 12 to 20 isolated reads on Haiku, scoring, clustering, up to 3 full-text reads, 1 convergence), plus real HTTP to four APIs |
| Checking ecosystems with `codesearch.py` | Nothing. It's a Python script — no model in the loop |
| `/loop` | Runs unattended until the backlog is exhausted. It expires after seven days |

Every subagent declares `model: sonnet`; the isolated prior-art reads run on
Haiku. The heavy model is reserved for `/security-review`, the one gate the
delivery cycle imposes on the critical domain. The full policy, and how to move
one agent up when your domain warrants it, is in
[`docs/engineering/models.md`](docs/engineering/models.md).

A loop that's running consumes tokens while you're looking elsewhere, and it
re-launches `/deliver-story` even when you thought you were done. If a delivery
starts without you typing anything, that's the loop: check `CronList` before
concluding anything, and `CronDelete <id>` stops it early.

### Check that it worked

After the bootstrap, two commands tell you whether it finished. First, look for
leftover placeholders:

```bash
grep -rn '{{[A-Z_]\+}}' . --exclude-dir=.git
```

You should see nothing. Every surviving placeholder is a spot where your project
still talks about the template. The pattern matches only the real shape — two
braces, uppercase letters, two braces — so a bare `grep "{{"` doesn't drag in
legitimate braces from code.

Then confirm the template removed itself:

```bash
ls modules scripts
```

You should see "No such file or directory". If those directories are still
there, the bootstrap stopped partway.

If you activated `stack-laravel`, check that the environment starts:

```bash
docker compose up -d && docker compose ps
```

Every service should read `running`, and the database should read `healthy`.

Two projects that both activated `stack-laravel` can't run at the same time
without editing ports. Both publish 8080 for the app, 5433 for PostgreSQL, 6380
for Redis, and 8026 for Mailpit. The second `docker compose up -d` either fails on a taken
port or, worse, connects a tool to the other project's database.

### Words used here

| Term | What it means |
|---|---|
| Claude Code | Anthropic's coding agent, run from a terminal, an IDE, or a browser |
| Skill | A named instruction set that the agent loads on demand. You invoke one by typing a slash and its name, like `/deliver-story` |
| Subagent | A separate agent run with its own tool list and its own context. The three reviewers are subagents |
| Workflow | A JavaScript file in `.claude/workflows/` that orchestrates several subagents deterministically. `review-story` is one |
| Story | One unit of work with acceptance criteria, numbered `US-XYZ`. Also called a user story |
| Epic | A file grouping related stories, numbered `E01`, `E02`, and so on |
| Backlog | Everything in `docs/backlog/`: the epics, the delivery journal, and the decision log |
| TDD | Test-driven development. Write the failing test, then the code that makes it pass |
| Counter-proof | Deliberately breaking the code a test protects, to confirm the test turns red |
| Squash merge | Merging a branch as a single commit, so one story reads as one commit on `main` |
| Bootstrap | The one-time run that turns this template into your project |

### When something breaks

[GETTING-STARTED.md](GETTING-STARTED.md) ends with a symptom-cause-fix table
covering the failures people actually hit: the bootstrap refusing to start,
placeholders surviving, a reviewer staying silent, and a `domain-expert` that
never finds anything because it was never specialized.

Two rules are worth repeating here. Never merge on a red CI. And if a reviewer
returns no report, that's incomplete coverage, not a clean bill of health.

### Contributing

Issues and pull requests are welcome. Two things to know before you open one.

`.github/workflows/template.yml` bootstraps a throwaway copy in five module
combinations on every pull request, and checks that nothing of the template
survives, that no backup file is left behind, and that only the writing
placeholders remain. Run the same check locally before opening a pull request:

```bash
cp -R . /tmp/socle-check && cd /tmp/socle-check
./scripts/bootstrap.sh test-slug stack-laravel
grep -rn '{{[A-Z_]\+}}' . --exclude-dir=.git   # only the writing placeholders
ls modules scripts                              # No such file or directory
```

`CONTRIBUTING.md` at the root belongs to the *generated project*, not to this
template. It's one of the files your project inherits.

### Origin and license

This template was extracted from a real project delivered with this method. What
survived the extraction is what had already caught a defect: the counter-proof
discipline, the three-reader review, the "here's how to check it yourself"
section that closes every report, and the whitelist that keeps the agent from
installing tools nobody approved.

Licensed under [MIT](LICENSE).

---

## Français

- [Ce que c'est](#ce-que-cest)
- [Prérequis](#prérequis)
- [Démarrage rapide](#démarrage-rapide)
- [Ce que l'amorçage te demande](#ce-que-lamorçage-te-demande)
- [Le cycle quotidien](#le-cycle-quotidien)
- [Ce qu'il y a dedans](#ce-quil-y-a-dedans)
- [Modules optionnels](#modules-optionnels)
- [Ce qu'il n'y a pas dedans, exprès](#ce-quil-ny-a-pas-dedans-exprès)
- [Ce qu'un run coûte](#ce-quun-run-coûte)
- [Vérifier que ça a marché](#vérifier-que-ça-a-marché)
- [Les mots employés ici](#les-mots-employés-ici)
- [Quand quelque chose casse](#quand-quelque-chose-casse)
- [Contribuer](#contribuer)
- [Origine et licence](#origine-et-licence)

### Ce que c'est

Développer avec un agent de code pose deux problèmes qui reviennent. Tu
réexpliques tes règles à chaque session, et tu dois croire l'agent sur parole
quand il dit que les tests passent.

Ce template règle les deux. La méthode vit dans des fichiers que Claude Code lit
de lui-même, donc les règles survivent d'une session à l'autre. Et chaque
rapport que l'agent écrit finit par une commande que **tu** lances pour
constater le résultat toi-même, ce qui t'évite de croire une affirmation que tu
ne peux pas reproduire.

Tu obtiens un dépôt où une commande livre une user story de la branche à la pull
request mergée, une revue de code où trois relecteurs indépendants examinent le
même changement sans voir les remarques des autres, et une règle ferme : un test
n'est une preuve qu'une fois qu'on l'a vu échouer.

Le template n'apporte ni code applicatif ni règles métier. Il demande les
tiennes.

Tu débutes avec Claude Code ? Chaque terme de cette page est défini dans
[Les mots employés ici](#les-mots-employés-ici). Commence par cette section si
*skill*, *sous-agent*, *story* ou *epic* ne te sont pas déjà familiers.

### Prérequis

À vérifier une fois par poste, avant de commencer :

| Outil | Comment vérifier | S'il manque |
|---|---|---|
| Claude Code 2.1.154 ou plus | `claude --version` | Mets à jour. En dessous, l'outil Workflow n'existe pas et la revue à trois relecteurs ne tourne pas, sans le dire |
| GitHub CLI, connecté | `gh auth status` | `gh auth login` |
| Node.js | `node --version` | Requis par le serveur de documentation `context7` du module Laravel |
| Python 3 | `python3 --version` | Requis par le module `dejavu`. Ses scripts n'utilisent que la bibliothèque standard, il n'y a rien à installer avec `pip` |
| Un runtime de conteneurs | `docker compose version` | Docker Desktop, ou OrbStack sur macOS. Requis par le module `stack-laravel` |

Node.js, Python et Docker sont chacun liés à un module optionnel. Ignore ceux
dont tu n'activeras pas le module.

### Démarrage rapide

Trois étapes t'amènent de rien à un projet dont le premier epic est écrit.

1. Crée ton dépôt depuis ce template :

   ```bash
   gh repo create mon-projet --template jamyl/socle --private --clone
   cd mon-projet
   ```

   Tu dois maintenant voir `CLAUDE.md`, `GETTING-STARTED.md`, `modules/` et
   `scripts/bootstrap.sh`. Si `modules/` est absent, la copie est incomplète :
   recommence.

2. Ouvre une session et amorce le projet :

   ```bash
   claude
   ```

   Puis, dans la session, lance `/bootstrap-project`. C'est un **skill** : un
   jeu d'instructions nommé que Claude Code charge à la demande, invoqué par une
   barre oblique suivie de son nom. L'amorçage tourne une seule fois,
   t'interviewe, rédige ta documentation, puis se supprime.

3. Livre la première story :

   ```text
   /deliver-story
   ```

Lis [GETTING-STARTED.md](GETTING-STARTED.md) en entier avant l'étape 2. Il
couvre les prérequis, chaque étape en détail, ce qu'il faut vérifier, et quoi
faire quand ça ne va pas. L'amorçage supprime ce fichier aussi, parce qu'il
parle du template et non de ton projet.

### Ce que l'amorçage te demande

L'interview se fait en quatre lots, et rien n'est écrit avant que tu valides le
résultat.

1. **Identité** — le nom du projet, un slug en kebab-case qui sert aux
   conteneurs et à la base de données, et le but en une phrase.
2. **Produit** — qui l'utilise et pour quoi, ce qui doit marcher pour dire que
   le produit existe, et ce qui est explicitement hors périmètre.
3. **Contraintes et architecture** — obligations légales ou réglementaires,
   cible d'hébergement, les langages que ton équipe sait déboguer en production,
   l'échelle à douze mois, les besoins temps réel ou hors-ligne, ton délai, et
   une stack déjà imposée s'il y en a une.
4. **Les règles qui coûtent le plus cher à violer** — trois à cinq invariants de
   ton domaine, chacun formulé pour qu'un test puisse le vérifier.

Le lot 4 décide de la qualité de tout le reste. Ces règles deviennent la liste
que l'un des trois relecteurs applique à *chaque* changement, aussi longtemps
que le projet vit. « Aucun code hors de X n'écrit dans Y » se vérifie. « Le code
doit être propre » ne se vérifie pas. Une réponse molle ici produit une revue
molle pendant des mois.

Après l'interview, l'agent nomme le mécanisme dur de ta conception s'il y en a
un — concurrence, cohérence, synchronisation hors-ligne — te propose une
recherche d'antériorité dessus en annonçant son coût, et **attend**. Il vérifie
dans deux ou trois écosystèmes candidats qu'une implémentation maintenue des
briques dont tu as besoin existe, ce qui ne coûte que quelques requêtes HTTP.
Puis il propose une stack, une alternative, et la phrase qui écarte l'alternative.

**Laravel est une issue possible, pas le choix par défaut.** Le module
`stack-laravel` s'active parce que la découverte aboutit à PHP ; toute autre
réponse donne un `stack.md` rédigé depuis l'interview et un sous-agent
`developer` généré pour cette stack.

Rien n'est écrit avant que tu valides.

### Le cycle quotidien

Deux commandes portent le travail, et chacune laisse une trace sur le disque :

```text
/cadrer-story "<un requis brut>"
      |
      v   2 à 5 stories écrites dans un fichier d'epic, en Étant donné/Quand/Alors
      |
/deliver-story
      |
      v   branche -> plan -> TDD -> tests verts -> revue à trois relecteurs
      |   -> pull request -> CI verte -> merge squash
      |
docs/backlog/JOURNAL.md        une ligne par livraison
docs/backlog/DECISIONS.md      une ligne par choix tranché sans te demander
```

Pour enchaîner plusieurs stories sans retaper, lance
`/loop 10m /deliver-story E01`. La boucle s'arrête d'elle-même quand aucune
story du périmètre n'est plus actionnable.

Écrire une story et la livrer sont deux commandes séparées exprès. Une story mal
cadrée découverte pendant la livraison coûte une branche déjà ouverte et un plan
déjà écrit. Découverte pendant le cadrage, elle coûte une relecture.

### Ce qu'il y a dedans

**Le cycle de livraison.** `/deliver-story` choisit la prochaine story
actionnable en parcourant le graphe des dépendances, pas une liste figée. Une
story dont le prérequis vit dans un epic plus loin est sautée, puis redevient
candidate quand ce prérequis est livré. Si une story exige un humain — un avis
juridique, un compte chez un tiers, une clé d'API — elle passe `bloqué` avec son
motif, et l'agent prend la suivante au lieu de perdre un tour à découvrir le mur.

**La discipline de contre-épreuve.** Un test n'est une preuve qu'une fois qu'on
l'a vu échouer. Avant d'écrire « c'est couvert », l'agent retire le garde que le
test prétend protéger, relance, constate le rouge, et restaure. Le skill porte
huit façons concrètes dont un test peut rester vert sans rien prouver : la
tautologie, la mise en scène absente, une course calée sur un `sleep` au lieu
d'un signal, un garde doublé ailleurs, et quatre autres. Les huit ont été
rencontrées en vrai, en deux jours. La question qui les résume : *que devrait
voir ce test pour devenir rouge ?*

**La revue à trois relecteurs.** Une fois les tests verts, trois sous-agents en
lecture seule lisent le même diff en parallèle sans se lire entre eux :
`reviewer` pour les conventions et la structure, `security-scanner` pour les
vulnérabilités, et `domain-expert` pour tes propres invariants. Leurs remarques
sont dédupliquées et triées en code, pas par un modèle. Leurs outils sont
limités à la lecture de fichiers : pas d'édition, pas de shell. `reviewer` et
`security-scanner` n'ont **aucun accès réseau**, parce que leur entrée est un
diff que quelqu'un d'autre a peut-être écrit. `domain-expert` garde la recherche
web, pour pouvoir vérifier un texte réglementaire. C'est structurel, pas une
promesse dans un prompt.

Si un relecteur ne rend rien du tout, le workflow le signale. Une couverture
incomplète n'est pas « rien à signaler », et confondre les deux est la façon
dont une revue cesse discrètement d'être une revue.

**L'antériorité avant l'architecture.** Le module `dejavu` cherche dans la
recherche publiée la partie dure de ta conception, avant que tu la rebâtisses. Il
fait lire un article par sous-agent isolé, pour qu'aucune source n'ancre les
autres, puis s'engage sur un seul chemin recommandé, cité. Les conclusions se
consignent dans `docs/engineering/prior-art.md` avec leurs identifiants, parce
qu'une conclusion que personne ne peut rouvrir est une recherche à refaire à la
session suivante.

**Onze niveaux de test.** `docs/engineering/testing-strategy.md` définit les
niveaux N1 à N11, chacun avec son périmètre et son moment d'exécution en CI. Deux
d'entre eux sont ceux que la plupart des projets n'ont pas, et ceux qui trouvent
les défauts les plus chers : N4 lance des opérations concurrentes en vrais
processus et prouve que les exécutions se sont recouvertes, et N6 fait du
mutation testing sur le domaine critique seulement.

### Modules optionnels

Tu choisis les modules pendant l'interview. Rien n'est copié sans que tu le
demandes.

| Module | Ce qu'il apporte | Quand l'activer |
|---|---|---|
| `stack-laravel` | Docker Compose avec PHP 8.4, PostgreSQL 16, Redis, Mailpit et Horizon, toutes les images épinglées par digest. GitHub Actions qui lance Pint, Larastan niveau 8, Pest sur PostgreSQL et un audit des dépendances. Un scanner de secrets, quatre sous-agents Laravel, et un premier epic pré-écrit | La découverte d'architecture aboutit à PHP et Laravel |
| `mobile-flutter` | Un dossier `mobile/`, des stories de toolchain qui partent `bloqué` parce que Xcode et Android Studio ne s'automatisent pas, et des niveaux de test de régression visuelle | Tu construis une app iOS, Android ou PWA |
| `dejavu` | Le skill d'antériorité `/dejavu` embarqué dans ton dépôt et versionné avec lui. Quatre sources académiques, aucune clé d'API, Python en bibliothèque standard | Ton architecture porte un mécanisme non trivial. À ignorer si ton poste a déjà `/dejavu` en global |

Les colonnes « quand l'activer » disent **où la découverte aboutit**, pas ce que
tu choisis d'avance.

Sans module de stack, tu as le cœur : la méthode, les skills, trois relecteurs en
lecture seule et des squelettes de documentation. L'amorçage rédige alors
`stack.md` et `testing-strategy.md` depuis la découverte, et génère un sous-agent
`developer` — plus `dba` s'il y a une base relationnelle — depuis
`.claude/templates/`.

### Ce qu'il n'y a pas dedans, exprès

**Aucun scaffold applicatif.** Ni `composer create-project`, ni
`flutter create`. Le scaffold naît de la première itération de livraison, avec
les versions du jour. Un scaffold figé dans un template pourrit en quelques
mois, et personne ne s'en aperçoit avant d'avoir bâti dessus.

**Aucun domaine métier.** Le template demande tes invariants au lieu d'en
supposer.

**Aucun backlog complet.** L'amorçage écrit le premier epic et rien d'autre. Les
epics rédigés des mois avant qu'on en ait besoin sont des epics à réécrire.

### Ce qu'un run coûte

Ces commandes lancent des sous-agents et font de vrais appels réseau. Connais le
coût avant de démarrer une boucle.

| Action | Ce qu'elle dépense |
|---|---|
| Une revue à trois relecteurs | 3 sous-agents, un par relecteur, sur chaque story |
| Une recherche `/dejavu` | Environ 18 à 26 appels d'agent (1 catégorisation, 12 à 20 lectures isolées en Haiku, notation, regroupement, jusqu'à 3 lectures de texte intégral, 1 convergence), plus du HTTP réel vers quatre APIs |
| Vérifier les écosystèmes avec `codesearch.py` | Rien. C'est un script Python — aucun modèle dans la boucle |
| `/loop` | Tourne sans surveillance jusqu'à épuisement du backlog. Elle expire après sept jours |

Chaque sous-agent déclare `model: sonnet` ; les lectures isolées d'antériorité
tournent en Haiku. Le modèle lourd est réservé à `/security-review`, le seul gate
que le cycle de livraison impose sur le domaine critique. La politique complète,
et comment monter un agent d'un cran quand ton domaine le justifie, sont dans
[`docs/engineering/models.md`](docs/engineering/models.md).

Une boucle qui tourne consomme des tokens pendant que tu regardes ailleurs, et
elle relance `/deliver-story` même quand tu croyais avoir fini. Si une livraison
démarre sans que tu aies rien tapé, c'est elle : vérifie avec `CronList` avant
de conclure quoi que ce soit, et `CronDelete <id>` l'arrête plus tôt.

### Vérifier que ça a marché

Après l'amorçage, deux commandes te disent s'il est allé au bout. D'abord,
cherche les placeholders restants :

```bash
grep -rn '{{[A-Z_]\+}}' . --exclude-dir=.git
```

Tu ne dois rien voir. Chaque placeholder survivant est un endroit où ton projet
parle encore du template. Le motif ne cherche que la forme réelle — deux
accolades, des majuscules, deux accolades — pour qu'un `grep "{{"` nu n'attrape
pas les accolades légitimes d'un bout de code.

Puis confirme que le template s'est retiré :

```bash
ls modules scripts
```

Tu dois voir « No such file or directory ». Si ces dossiers sont encore là,
l'amorçage s'est arrêté en route.

Si tu as activé `stack-laravel`, vérifie que l'environnement démarre :

```bash
docker compose up -d && docker compose ps
```

Tous les services doivent afficher `running`, et la base `healthy`.

Deux projets ayant tous deux activé `stack-laravel` ne peuvent pas tourner en
même temps sans modifier les ports. Les deux publient 8080 pour l'app, 5433 pour
PostgreSQL, 6380 pour Redis et 8026 pour Mailpit. Le second `docker compose up -d` échoue
sur un port déjà pris ou, pire, connecte un outil à la base de l'autre projet.

### Les mots employés ici

| Terme | Ce que ça veut dire |
|---|---|
| Claude Code | L'agent de code d'Anthropic, utilisable depuis un terminal, un IDE ou un navigateur |
| Skill | Un jeu d'instructions nommé que l'agent charge à la demande. On l'invoque en tapant une barre oblique et son nom, comme `/deliver-story` |
| Sous-agent | Un agent lancé à part, avec sa propre liste d'outils et son propre contexte. Les trois relecteurs sont des sous-agents |
| Workflow | Un fichier JavaScript dans `.claude/workflows/` qui orchestre plusieurs sous-agents de façon déterministe. `review-story` en est un |
| Story | Une unité de travail avec ses critères d'acceptation, numérotée `US-XYZ`. Aussi appelée user story |
| Epic | Un fichier qui regroupe des stories liées, numéroté `E01`, `E02`, et ainsi de suite |
| Backlog | Tout ce qui vit dans `docs/backlog/` : les epics, le journal des livraisons et le journal des décisions |
| TDD | Développement piloté par les tests. Écrire le test qui échoue, puis le code qui le fait passer |
| Contre-épreuve | Casser volontairement le code qu'un test protège, pour confirmer que le test devient rouge |
| Merge squash | Fusionner une branche en un seul commit, pour qu'une story se lise comme un commit sur `main` |
| Amorçage | Le run unique qui transforme ce template en ton projet |

### Quand quelque chose casse

[GETTING-STARTED.md](GETTING-STARTED.md) finit par un tableau
symptôme-cause-remède couvrant les pannes qu'on rencontre vraiment : l'amorçage
qui refuse de démarrer, des placeholders qui survivent, un relecteur qui reste
muet, et un `domain-expert` qui ne trouve jamais rien parce qu'il n'a jamais été
spécialisé.

Deux règles méritent d'être répétées ici. Ne merge jamais sur une CI rouge. Et
si un relecteur ne rend pas de rapport, c'est une couverture incomplète, pas un
quitus.

### Contribuer

Les issues et les pull requests sont bienvenues. Deux choses à savoir avant
d'en ouvrir une.

`.github/workflows/template.yml` amorce une copie jetable dans cinq combinaisons
de modules à chaque pull request, et vérifie que rien du template ne survit,
qu'aucune sauvegarde ne traîne, et que seuls les placeholders de rédaction
restent. Lance le même contrôle en local avant d'ouvrir une PR :

```bash
cp -R . /tmp/socle-check && cd /tmp/socle-check
./scripts/bootstrap.sh test-slug stack-laravel
grep -rn '{{[A-Z_]\+}}' . --exclude-dir=.git   # seulement les placeholders de rédaction
ls modules scripts                              # No such file or directory
```

Le `CONTRIBUTING.md` à la racine appartient au *projet engendré*, pas à ce
template. C'est l'un des fichiers dont ton projet hérite.

### Origine et licence

Ce template est extrait d'un projet réel livré avec cette méthode. Ce qui a
survécu à l'extraction, c'est ce qui avait déjà attrapé un défaut : la
discipline de contre-épreuve, la revue à trois relecteurs, la section « comment
tu peux le vérifier toi-même » qui clôt chaque rapport, et la liste blanche qui
empêche l'agent d'installer un outil que personne n'a approuvé.

Sous licence [MIT](LICENSE).
