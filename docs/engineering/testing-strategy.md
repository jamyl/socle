# Stratégie de tests

> Complète [stack.md](stack.md). Principe directeur : pyramide classique, **avec
> des garanties renforcées sur le domaine critique** — celui que `CLAUDE.md`
> désigne comme portant les règles les plus chères à violer.
>
> 🔧 Version agnostique. Le module `stack-laravel` la remplace par une version
> outillée (Pint, Larastan, Pest) ; `mobile-flutter` ajoute N7 et N8 ;
> `frontend-web` outille N7 pour le web (`docs/engineering/frontend.md`).

## 1. Les niveaux

Chaque niveau indique son périmètre, son moment d'exécution en CI, et la story
qui l'instaure.

### N1 — Analyse statique (à chaque push)
Formatage vérifié (pas seulement appliqué), analyse statique au **niveau le plus
strict que le projet peut tenir**, audit des dépendances.

**Un warning statique = build rouge.** Pas de fichier de baseline d'exceptions
qui grossit : une exception se justifie ligne à ligne, ou le code change.

### N2 — Tests unitaires (à chaque push)
Logique pure, sans base ni réseau : value objects, machines à états, calculs,
règles d'expiration. Suite rapide — si elle dépasse la trentaine de secondes,
c'est qu'elle touche à quelque chose qu'elle ne devrait pas.

### N3 — Tests d'intégration / API (à chaque push)
Endpoints complets (validation → action → présentation), autorisations, et
**cloisonnement** : chaque nouvelle ressource ajoute son test d'isolation.

🔑 **Sur le vrai moteur de base de données, jamais un substitut en mémoire.** Les
comportements de verrouillage, les contraintes et les types diffèrent — un test
vert sur SQLite ne dit rien d'une application qui tourne sur PostgreSQL.

**Factories uniquement**, jamais de fixtures mutables partagées entre tests.

### N4 — Concurrence & invariants (PR vers `main`)
Le niveau que la plupart des projets n'ont pas, et celui qui trouve les défauts
les plus chers. N opérations parallèles **réelles** (processus, pas boucles) sur
la même ressource → l'invariant tient.

⚠️ **Prouver d'abord la mise en scène.** Un test de concurrence doit démontrer
que les exécutions se sont **recouvertes** — sinon N opérations qui se sont
suivies rendent le même résultat vert, et le test ne prouve rien. Faire
enregistrer sa fenêtre à chaque processus, et exiger un recouvrement.

Invariant global vérifié après chaque suite, s'il y en a un (une somme, un
équilibre, une unicité).

### N5 — Contrat d'interface (PR vers `main`)
Si le projet a plusieurs consommateurs (API + client mobile, service + service) :
la spec est **générée depuis le code**, versionnée, et un écart non commité casse
le build. C'est le seul mécanisme « sans écart » qui tienne dans le temps.

### N6 — Mutation testing (nightly)
Sur le **domaine critique uniquement**. Un test qui passe ne suffit pas : il faut
prouver qu'il **échouerait** si le code était faux. Trop lent par push.

### N7 — Interface : rendu & régression visuelle (à chaque push)
Composants du socle UI en tests de rendu comparés à une référence. Si le projet a
plusieurs langues ou plusieurs sens d'écriture, **chaque sens est vérifié pixel
par pixel**, pas à l'œil.

### N8 — Parcours de bout en bout sur cible réelle (pré-release)
Le parcours critique sur simulateur/navigateur réel, services externes mockés
localement. Puis le même parcours en smoke sur **staging** avant chaque release.

### N9 — Scénarios métier de bout en bout (PR vers `main`)
Le cycle de vie complet de l'objet central du produit, création → fin de vie,
plus les chemins d'échec (annulation, compensation, expiration). **Ces scénarios
sont la spécification exécutable du produit.**

### N10 — Performance (jalon)
Les quelques budgets qui comptent, mesurés en continu (« telle lecture sous telle
charge en moins de tant »). Pas de perf-CI permanente avant d'en avoir besoin :
c'est de la sur-ingénierie.

### N11 — Sécurité (jalon + continu)
Continu : audit des dépendances en N1. Jalon : `/security-review` sur le code
applicatif, plus une revue ciblée sur les classes de risque propres au projet
(autorisation transverse, logique du domaine critique, webhooks, exposition de
secrets).

## 2. Politique de couverture

Pas de pourcentage global fétiche — la couverture se pilote par **criticité** :

| Périmètre | Exigence |
|---|---|
| Domaine critique (cf. `CLAUDE.md`) | 100 % des chemins critiques + concurrence (N4) + mutation (N6) |
| Reste du code | Chaque comportement des critères d'acceptation a son test |
| Interface | Rendu sur le socle, tests sur les écrans à logique, parcours critique de bout en bout |

## 3. Données de test & environnements

- **Factories uniquement.** Jamais de fixtures partagées mutables.
- Seeds dédiés et réalistes pour **staging** — jamais rejoués en production.
- Les tests **ne touchent jamais un service externe réel** : chaque tiers est
  derrière une interface avec un fake.
- La suite de tests ne doit pas pouvoir atteindre la base de développement. Ce
  garde-fou s'écrit, il ne se suppose pas.

## 4. Orchestration CI

| Moment | Contenu | Durée cible |
|---|---|---|
| Chaque push | N1 + N2 + N3 (+ N7) | < 5 min |
| PR vers `main` | + N4 + N5 + N9 | < 15 min |
| Nightly | N6 + audits complets | — |
| Pré-release | N8 + smoke staging | manuel assisté |
| Jalon | N10 + N11 | ponctuel |

**Règle de merge : un merge dans `main` = déployable en staging sans
intervention.**

## 5. Ce qui rend un test recevable

Un test n'est une preuve que si **on l'a vu échouer**. Retire le garde qu'il
prétend couvrir, relance, constate le rouge, restaure. Les huit motifs de fausse
vérification sont énumérés dans `.claude/skills/deliver-story/SKILL.md` — les
lire avant d'écrire « c'est couvert ».

La question qui les résume : *« que devrait voir ce test pour devenir rouge ? »*
Si la réponse n'est pas immédiate et concrète, il ne couvre rien.
