# E01 — Fondations projet & environnement (P0)

**Objectif** : environnement opérationnel, monorepo structuré, CI verte, assets
Claude Code en place. **Aucune logique métier ici.**

> 🔧 Epic pré-écrit par le module `stack-laravel`. `/bootstrap-project` l'adapte
> (nom du repo, slug, ports) plutôt que d'en écrire un nouveau. Ajuste les
> statuts : une story qui attend une action humaine part **`bloqué (motif)`**.

---

## US-101 — Environnement backend (Docker)
**En tant que** développeur, **je veux** tout le backend en conteneurs **afin de**
ne dépendre d'aucun service installé sur le poste.
**Priorité** P0 · **Estimation** S · **Statut** à faire

Critères d'acceptation :
- [ ] **Aucun service backend installé sur le poste** (ni Herd, ni `brew install php/postgresql`) : un runtime de conteneurs suffit. OrbStack recommandé sur macOS — son partage de fichiers est nettement plus rapide que Docker Desktop, ce qui sert directement le volume `vendor/`.
- [ ] `docker-compose.yml` à la racine démarrant **tout le backend** : `app` (PHP 8.4), `db` (PostgreSQL 16), `redis`, `mailpit`, `horizon` — **images pinnées par digest**, volumes nommés, **ports dédiés**. `docker compose up -d` puis `docker compose exec app php -v` OK.
- [ ] Composer, artisan et Pest s'exécutent **dans le conteneur** ; aucune commande PHP ne dépend du poste hôte.
- [ ] `vendor/` en **volume nommé**, pas en bind mount — les bind mounts macOS s'effondrent sur des milliers de petits fichiers.
- [ ] Checklist d'installation documentée dans `docs/setup.md`.

> Le `docker-compose.yml` et l'image PHP sont **fournis par le module** : cette
> story les vérifie et documente, elle ne les réécrit pas.

## US-102 — Monorepo & git
**En tant que** développeur, **je veux** un repo structuré **afin de** versionner
tout le projet.
**Priorité** P0 · **Estimation** XS · **Statut** à faire

Critères d'acceptation :
- [ ] Repo GitHub **privé** rattaché (`git remote -v` le montre) ; structure `backend/`, `docs/`.
- [ ] Branche par défaut `main` ; le nom du dossier local n'a pas à correspondre au nom du repo — git ne les lie pas.
- [ ] `.gitignore` couvrant la stack, l'OS et `.env*` (avec `!.env.example`).
- [ ] Convention de commits notée dans `CONTRIBUTING.md` (courte : type + sujet).

## US-103 — Assets Claude Code
**En tant que** développeur assisté par Claude, **je veux** un contexte projet
propre **afin d'** avoir des sessions efficaces.
**Priorité** P0 · **Estimation** S · **Statut** à faire

Critères d'acceptation :
- [ ] `CLAUDE.md` **court** : pointeurs vers `docs/engineering/stack.md`, `testing-strategy.md` et `docs/backlog/` — **sans dupliquer leur contenu**. Un CLAUDE.md qui recopie ses sources divergera d'elles.
- [ ] Section « règles qui coûtent le plus cher à violer » remplie avec les invariants du domaine, formulés de façon **testable**.
- [ ] `.claude/agents/domain-expert.md` spécialisé : le domaine, son vocabulaire, ses invariants, ses pièges de conformité.
- [ ] Le nœud `domain-expert` de `.claude/workflows/review-story.js` porte les **mêmes** invariants. Les trois endroits restent d'accord.
- [ ] Fiches `docs/domain/` par sous-domaine, si le métier le justifie.

## US-104 — Backend scaffold + CI
**En tant que** développeur, **je veux** un squelette Laravel testé en CI **afin
de** détecter les régressions dès le premier jour.
**Priorité** P0 · **Estimation** S · **Statut** à faire
**Dépend de** : US-101, US-102

Critères d'acceptation :
- [ ] Laravel dans `backend/` (**versions du jour** — le scaffold n'est pas figé dans le template), Pest installé, Pint et Larastan **niveau 8** configurés.
- [ ] Connexions PostgreSQL + Redis pointant sur les **conteneurs Compose d'US-101**, jamais un service système ; migration baseline exécutée.
- [ ] 🔑 **`phpunit.xml` basculé de SQLite vers PostgreSQL.** Le défaut Laravel viole `stack.md` §3.6 — c'est le premier écart à corriger, et il est silencieux.
- [ ] GitHub Actions conformes aux gates de `testing-strategy.md` §4 : secrets + statique + migrations + tests **sur PostgreSQL** + audit des dépendances. CI verte sur un test trivial.
- [ ] Horizon installé pour les queues.

> ⚠️ **À surveiller à cette étape** : le squelette Laravel peut épingler une
> version de PHPUnit incompatible avec la version de Pest visée. Le relever
> explicitement plutôt que de contourner.

## US-105 — Environnements & secrets
**En tant que** développeur, **je veux** une convention d'environnements **afin
de** ne jamais fuiter un secret.
**Priorité** P0 · **Estimation** XS · **Statut** à faire
**Dépend de** : US-104

Critères d'acceptation :
- [ ] `backend/.env.example` **exhaustif** — chaque variable que le code lit y figure, avec une valeur factice.
- [ ] Aucun secret commité : `.github/scan-secrets.sh` branché en job CI dédié.
- [ ] 🔑 **Scanner testé DANS LES DEUX SENS** : 0 faux positif sur le dépôt réel, **et** détection d'un faux secret de chaque motif glissé temporairement. Le second test est le seul qui prouve qu'il marche — sans lui, c'est un décor vert.
- [ ] Environnements nommés : `local`, `staging`, `production`, documentés dans `docs/environnements.md`.

## US-106 — Garde-fou : la suite de tests n'atteint pas la base de dev
**En tant que** développeur, **je veux** que les tests ne puissent pas toucher la
base de développement **afin de** ne pas perdre mon travail.
**Priorité** P0 · **Estimation** XS · **Statut** à faire
**Dépend de** : US-104

Critères d'acceptation :
- [ ] La suite refuse de démarrer si la base cible n'est pas la base de test (nom vérifié, pas supposé).
- [ ] Contre-épreuve : pointer volontairement la config sur la base de dev → la suite **refuse** et le dit clairement.

> Pourquoi une story à part entière : `RefreshDatabase` mal configuré efface la
> base sur laquelle on travaillait, et on ne le découvre qu'après. Le coût de ce
> garde est de quelques lignes ; le coût de son absence est une journée.
