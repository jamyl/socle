# Stratégie de tests

> Complète [stack.md](stack.md). Principe directeur : pyramide classique, **avec
> des garanties renforcées sur le domaine critique** — celui que `CLAUDE.md`
> désigne comme portant les règles les plus chères à violer.

## 1. Les niveaux

### N1 — Analyse statique (à chaque push)
`pint --test` (formatage **vérifié**, pas seulement appliqué), Larastan **niveau
8**, `composer audit`.

**Un warning statique = build rouge.** Pas de baseline d'exceptions qui grossit :
une exception se justifie ligne à ligne dans `phpstan.neon`, ou le code change.

### N2 — Tests unitaires (à chaque push)
Pest, `tests/Unit/`. Logique pure sans base ni réseau : value objects, machines à
états, calculs, règles d'expiration. Suite rapide (< 30 s) — au-delà, elle touche
à quelque chose qu'elle ne devrait pas.

### N3 — Tests feature/API (à chaque push)
Pest, `tests/Feature/`, **sur PostgreSQL éphémère** (service container en CI).

🔑 **Jamais SQLite.** Les verrous et les contraintes diffèrent : un test vert sur
SQLite ne dit rien d'une application qui tourne sur PostgreSQL (stack.md §3.6).
⚠️ Le `phpunit.xml` par défaut de Laravel pointe sur SQLite — le basculer fait
partie d'US-104.

Cible : endpoints complets (`FormRequest` → `Action` → `Resource`), policies,
**isolation inter-tenants** (un test par ressource), webhooks signés / falsifiés
/ rejoués, jobs.

**Factories uniquement**, jamais de fixtures mutables partagées.

### N4 — Concurrence & invariants (PR vers `main`)
Pest, `tests/Concurrency/`. Le niveau que la plupart des projets n'ont pas, et
celui qui trouve les défauts les plus chers : N opérations parallèles **réelles**
(`pcntl_fork`, pas une boucle) sur la même ressource → l'invariant tient.

⚠️ **Prouver d'abord la mise en scène.** Chaque processus enregistre sa fenêtre
d'exécution, et le test **exige un recouvrement**. Sans cette preuve, N
opérations qui se sont simplement suivies rendent le même vert, et le test ne
démontre rien. Vécu.

Ne pas utiliser `RefreshDatabase` ici : les forks ont besoin d'une base réelle,
pas d'une transaction ouverte.

### N5 — Contrat OpenAPI (PR vers `main`)
La spec est **générée** par Scramble depuis le code et versionnée. Les réponses
des tests feature sont validées contre elle ; un client généré est régénéré et
diffé — un écart non commité casse le build. C'est le seul mécanisme « sans
écart » qui tienne dans le temps.

### N6 — Mutation testing (nightly)
Infection sur le **domaine critique uniquement**, MSI ≥ 90 %. Un test qui passe
ne suffit pas : il faut prouver qu'il **échouerait** si le code était faux. Trop
lent par push.

### N7 — Rendu & régression visuelle (à chaque push)
*Fourni par le module `mobile-flutter`.* Sans lui, ce niveau ne s'applique pas.

### N8 — Parcours sur cible réelle (pré-release)
*Fourni par le module `mobile-flutter`.*

### N9 — E2E API métier (PR vers `main`)
Scénarios Pest de bout en bout : le cycle de vie complet de l'objet central du
produit, création → fin de vie, plus les chemins d'échec (annulation,
compensation, expiration). **Ces scénarios sont la spécification exécutable du
produit.**

### N10 — Performance (jalon)
Les rares budgets qui comptent, mesurés en continu (« telle lecture sous telle
charge en moins de tant »). Pas de perf-CI permanente avant d'en avoir besoin.

⚠️ **Le piège qui fait mentir une mesure** : insérer en masse sous
`RefreshDatabase`, c'est insérer dans une transaction ouverte. Un `ANALYZE`
d'autovacuum qui passe pendant ce temps voit les pages sans voir les lignes et
enregistre `reltuples = 0` sur une table de plusieurs Mo — le planificateur la
croit vide et choisit un plan catastrophique. Diagnostic : `reltuples` nul avec
`relpages` élevé dans `pg_class`. Correctif : `ANALYZE` explicite après le
chargement. **Quand une mesure est absurde, soupçonner les statistiques du
moteur avant le code.**

### N11 — Sécurité (jalon + continu)
Continu : `composer audit` en N1. Jalon : `/security-review` sur `backend/`, plus
une revue ciblée sur les classes de risque du projet — IDOR/BOLA inter-tenants,
logique du domaine critique, webhooks, exposition de secrets.

## 2. Politique de couverture

Pas de pourcentage global fétiche — la couverture se pilote par **criticité** :

| Périmètre | Exigence |
|---|---|
| Domaine critique (cf. `CLAUDE.md`) | 100 % des chemins critiques + concurrence (N4) + mutation (N6) |
| Reste du backend | Chaque comportement des critères d'acceptation a son test feature |

## 3. Données de test & environnements

- **Factories uniquement.** Jamais de fixtures partagées mutables.
- Seeds dédiés et réalistes pour **staging** — jamais rejoués en production.
- Les tests **ne touchent jamais un service externe réel** : chaque tiers vit
  derrière une interface avec un fake.
- 🔴 **La suite de tests ne doit pas pouvoir atteindre la base de
  développement.** Ce garde-fou s'écrit — un `RefreshDatabase` mal configuré
  efface la base sur laquelle on travaillait, et on ne le découvre qu'après.

## 4. Orchestration CI

| Moment | Contenu | Durée cible |
|---|---|---|
| Chaque push | N1 + N2 + N3 | < 5 min |
| PR vers `main` | + N4 + N5 + N9 | < 15 min |
| Nightly | N6 + audits complets | — |
| Jalon | N10 + N11 | ponctuel |

**Règle de merge : un merge dans `main` = déployable en staging sans
intervention.**

## 5. Ce qui rend un test recevable

Un test n'est une preuve que si **on l'a vu échouer**. Retire le garde qu'il
prétend couvrir, relance, constate le rouge, restaure. Les huit motifs de fausse
vérification sont énumérés dans `.claude/skills/deliver-story/SKILL.md` — les
lire avant d'écrire « c'est couvert ».

Deux pièges spécifiques à cette stack :

- **`->throws()` à deux appels** : le premier lève, le second n'est jamais
  atteint. Un seul appel par assertion d'exception.
- **La queue est `sync` en test**, et Laravel fait partir les jobs `afterCommit`
  sous `RefreshDatabase` : un job dispatché s'exécute **en ligne** pendant le
  test. Mesurer un **delta**, jamais un compte absolu.

La question qui résume tout : *« que devrait voir ce test pour devenir rouge ? »*
Si la réponse n'est pas immédiate et concrète, il ne couvre rien.
