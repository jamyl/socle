# Démarrer un nouveau projet — étape par étape

> Ce fichier est **supprimé** par l'amorçage : il parle du template, pas de ton
> projet. Lis-le une fois, en entier, avant de lancer quoi que ce soit.

## Ce que tu obtiens

Un projet où la **méthode est déjà là** : une story se livre en une commande
(`/deliver-story`), passe par TDD, une revue en fan-out à trois nœuds, une CI
verte et une PR mergée en squash. C'est ce cycle qui a produit 50 stories en
44 h sur le projet dont ce socle est extrait.

Ce que le socle n'apporte pas : ton domaine. Il te le **demande**.

---

## Étape 0 — Prérequis (une fois par poste)

| Outil | Vérification | Si absent |
|---|---|---|
| `gh` authentifié | `gh auth status` | `gh auth login` |
| Runtime de conteneurs | `docker compose version` | OrbStack (plus rapide que Docker Desktop sur macOS) ou Docker Desktop |
| Skill `/dejavu` | `ls ~/.claude/skills/dejavu` | `npx github:jamyl/dejavu install` |
| `DEJAVU_CONTACT` | `echo $DEJAVU_CONTACT` | `echo 'export DEJAVU_CONTACT="Ton Nom ton@email"' >> ~/.zshrc` puis **rouvre le terminal** |

⚠️ **`DEJAVU_CONTACT` doit être dans ton `~/.zshrc`, pas seulement exporté dans
un terminal.** Un `export` à la main n'est pas visible depuis Claude Code : son
processus a démarré avant. Les APIs académiques réclament ce contact.

---

## Étape 1 — Créer le repo depuis le template

```bash
gh repo create mon-projet --template jamyl/socle --private --clone
cd mon-projet
```

**Ce que tu dois voir** : un dossier contenant `CLAUDE.md`, `GETTING-STARTED.md`,
`modules/` et `scripts/bootstrap.sh`.

**Ce qui signalerait un problème** : pas de `modules/` → le template n'a pas été
copié en entier, recommence.

---

## Étape 2 — Amorcer, avec Claude Code

```bash
claude
```

puis, dans la session :

```
/bootstrap-project mon-projet
```

**Ce qui va se passer**, dans cet ordre — et tu es sollicité à chaque palier :

1. **Interview** — quatre lots de questions : identité (nom, slug, but en une
   phrase), produit (personas, premier jalon, hors périmètre), contraintes
   (légales, techniques, modules à activer), puis **les 3 à 5 règles qui coûtent
   le plus cher à violer** dans ton domaine.

   > 🔑 **Ce dernier lot décide de la qualité de tout le projet.** Ces règles
   > deviennent la liste d'invariants que le nœud `domain-expert` vérifiera sur
   > *chaque* diff, pendant des mois. Une règle molle ici produit une revue molle
   > jusqu'à la fin. Prends le temps.

2. **Antériorité** — si ton architecture porte un mécanisme non trivial
   (concurrence, cohérence, cache, protocole, crypto, scale-out), `/dejavu` va
   chercher si c'est déjà résolu et publié. La conclusion est consignée dans
   `docs/engineering/prior-art.md` **avec ses identifiants**. Sur du CRUD, il
   s'abstiendra — c'est normal, il a sa propre porte d'entrée.

3. **Proposition d'architecture** — moins d'une page : stack, modèle de domaine,
   où vit chaque invariant, questions ouvertes. **Rien n'est écrit avant que tu
   valides.** C'est le moment de corriger : un bootstrap part sur un
   malentendu ou ne part pas.

4. **Écriture** — `scripts/bootstrap.sh` fait la mécanique (placeholders,
   modules, auto-suppression), puis Claude rédige `vision.md`, `stack.md`,
   `CLAUDE.md`, l'agent `domain-expert`, le backlog et **E01 uniquement**.

5. **Commit initial** et un rapport qui te dit ce qui reste à faire de ton côté.

---

## Étape 3 — Vérifier l'amorçage

```bash
grep -rn "{{" . --exclude-dir=.git
```

**Ce que tu dois voir : rien.** Chaque `{{…}}` survivant est un endroit où ton
projet parle encore du template.

```bash
ls modules scripts 2>&1
```

**Ce que tu dois voir** : « No such file or directory ». Le template s'est
retiré. S'ils sont encore là, l'amorçage s'est arrêté en route.

Si tu as activé `stack-laravel` :

```bash
docker compose up -d && docker compose ps
```

**Ce que tu dois voir** : tous les services en `running`, et un `healthy` sur la
base.

> ⚠️ **Deux projets issus de ce template ne peuvent pas tourner en même temps.**
> Ils publient les mêmes ports hôte — app 8080, PostgreSQL 5433, Redis 6380,
> Mailpit 8026. Le second `up -d` échouera sur un port déjà pris, **ou pire**, un
> outil se connectera au 5433 de l'autre projet et les données n'auront aucun
> sens. Si tu fais tourner deux projets en parallèle, décale les ports du second
> dans son `docker-compose.yml` (5434, 6381, 8027, 8081) et note-les dans son
> `stack.md` §5.

---

## Étape 4 — Livrer

```
/deliver-story
```

Une story, de bout en bout : branche, TDD, tests verts, revue en fan-out, PR,
CI verte, merge squash. Le rapport finit toujours par une section « comment tu
peux le vérifier toi-même » avec une commande copiable.

Pour enchaîner sans relancer à la main :

```
/loop 10m /deliver-story E01
```

La boucle s'arrête d'elle-même sur `BACKLOG ÉPUISÉ — ARRÊTER LA BOUCLE`. Elle
expire après 7 jours ; `CronList` puis `CronDelete <id>` l'arrête plus tôt.

> ⚠️ **Une boucle qui tourne consomme des tokens sans que tu la regardes**, et
> elle relancera `/deliver-story` même quand tu croyais avoir fini. Si un
> `/deliver-story` se déclenche sans que tu l'aies tapé, c'est elle : vérifie
> avec `CronList` avant de conclure quoi que ce soit.

---

## Les deux modules

| Module | Ce qu'il apporte | Quand l'activer |
|---|---|---|
| `stack-laravel` | Docker Compose (PHP 8.4, PostgreSQL 16, Redis, Mailpit, Horizon — images pinnées par digest), CI GitHub Actions (Pint, Larastan 8, Pest sur PostgreSQL, `composer audit`), scanner de secrets, `.mcp.json` (laravel-boost, context7, github lecture seule), 4 sous-agents Laravel, `stack.md` et `testing-strategy.md` remplis, `E01-fondations.md` pré-écrit | Backend PHP/Laravel |
| `mobile-flutter` | Dossier `mobile/`, stories E01 de toolchain (déjà `bloqué` : Xcode et Android Studio ne s'automatisent pas), niveaux de test N7/N8, notes du plugin `dart-flutter` | App iOS/Android/PWA |

Aucun module → le cœur seul : méthode, skills, agents génériques, squelettes de
docs. L'amorçage rédige alors `stack.md` de zéro depuis l'interview.

> **Le scaffold applicatif n'est pas dans le template**, volontairement. Ni
> `composer create-project`, ni `flutter create`. Il naît de la première
> itération `/deliver-story` (US-104), avec les versions du jour. Un scaffold
> figé dans un template pourrit en quelques mois — et personne ne s'en aperçoit
> avant d'avoir bâti dessus.

---

## Si quelque chose ne va pas

| Symptôme | Cause probable | Quoi faire |
|---|---|---|
| `/bootstrap-project` refuse de démarrer | Repo déjà amorcé | C'est le garde attendu. `/deliver-story` à la place |
| `bootstrap.sh` affiche l'usage | Slug manquant ou invalide | Slug en kebab-case, 3 à 40 caractères, commence par une lettre |
| Des `{{…}}` subsistent après l'amorçage | Rédaction interrompue | Relance la session et demande de finir la rédaction ; **ne relance pas** le script |
| Un nœud de la revue reste muet | Agent absent ou mal nommé | Le workflow le signale. Couverture incomplète ≠ « rien à signaler » |
| `domain-expert` ne trouve jamais rien | Ses invariants sont restés génériques | Rouvre `.claude/workflows/review-story.js` et `.claude/agents/domain-expert.md` : le bootstrap ne les a pas spécialisés |
