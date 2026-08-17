# {{PROJET}} — Stack technique & règles d'architecture

> Document de référence pour développer **sans écart**. Toute dérogation à ces
> choix se décide ici (PR sur ce fichier), jamais silencieusement dans le code.
> Stratégie de tests : voir [testing-strategy.md](testing-strategy.md).

## 1. Vue d'ensemble

| Couche | Technologie | Version | Rôle |
|---|---|---|---|
| Langage backend | PHP | 8.4 | `declare(strict_types=1)` partout |
| Framework | Laravel | 13 | API REST + jobs + scheduler |
| Base de données | PostgreSQL | 16 | **Source de vérité unique** |
| Cache / files d'attente | Redis + Laravel Horizon | 7.x | Queues, rate limiting, cache |
| Auth API | Laravel Sanctum | — | Tokens |
| Panels web | Filament (Livewire) | 5 | Administration |
| Contrat d'API | OpenAPI généré (Scramble) | 3.1 | Source unique du contrat |
| Tests | Pest | 5 | Unit, feature, concurrence |
| Formatage | Pint | — | `--test` en CI |
| Analyse statique | Larastan | niveau **8** | Aucune baseline d'exceptions |
| Mail de dev | Mailpit | — | http://localhost:8026 |
| Dev local | **Docker Compose intégral** — images pinnées par digest | — | Zéro service installé sur le poste |
| CI | GitHub Actions | — | Gates §4 |
| Observabilité | À COMPLÉTER (Sentry ?) | | |

**Les versions sont verrouillées.** Une montée de version est une story, pas un
effet de bord.

⚠️ **Le scaffold applicatif n'est pas dans le template** : il naît de la première
itération `/deliver-story` (US-104), avec les versions du jour. Un scaffold figé
dans un template pourrit en quelques mois, et personne ne s'en aperçoit avant
d'avoir bâti dessus.

## 2. Pourquoi ces choix

- **PostgreSQL, pas MySQL** : contraintes `CHECK`, triggers, `SELECT FOR UPDATE`
  fiable et types riches. Dès qu'un invariant doit être tenu **par la base** et
  pas seulement par l'application, c'est PostgreSQL qui le tient.
- **Tout en conteneurs** : aucun service sur le poste. La contrepartie est
  assumée — toute commande passe par `docker compose exec`. Le bénéfice est
  qu'un environnement cassé se répare par `down -v && up -d`, pas par une
  archéologie de `brew`.
- **`vendor/` en volume nommé** : les bind mounts macOS s'effondrent sur des
  milliers de petits fichiers. Mesurable, pas théorique.
- **Images pinnées par digest** : un tag seul ne garantit pas un rebuild
  identique — « Docker ne garantit pas la reproductibilité » (arXiv 2601.12811).
- **Larastan niveau 8 sans baseline** : une baseline d'exceptions grossit, et
  personne ne la fait décroître. Une exception se justifie ligne à ligne.

Si `/dejavu` a servi pour un choix d'architecture, renvoyer ici vers la section
correspondante de [prior-art.md](prior-art.md) et ses identifiants.

## 3. Règles d'architecture

> ⚠️ Les règles **techniques** vivent ici. Les règles **du domaine** vivent dans
> `CLAUDE.md` et sont reprises par le nœud `domain-expert` de la revue en
> fan-out. Les deux listes sont distinctes et toutes les deux obligatoires.

1. **La logique métier ne vit jamais dans un contrôleur** ni dans une ressource
   Filament. Chemin unique : `FormRequest` → `Action`/`Service` → `Resource`.
2. **Un état se modélise par un enum PHP** avec une matrice de transitions
   explicite. Jamais une chaîne libre, jamais un booléen qui devient trois états
   six mois plus tard.
3. **Un point d'entrée unique par écriture critique.** Le service qui la porte
   est le seul à écrire dans ses tables ; tout autre code passe par lui. Cette
   règle ne vaut que si un test la vérifie — l'écrire ne suffit pas.
4. **Ce qui est posté ne se modifie pas.** Pas d'`UPDATE` ni de `DELETE` sur une
   écriture engagée : on compense par une écriture inverse.
5. **Migrations additives uniquement** sur toute table portant des données
   réelles. Jamais de `DROP`/`ALTER` destructif. Un `down()` qui ne peut pas être
   honnête **refuse** de tourner plutôt que de prétendre.
6. **Tests sur PostgreSQL, jamais SQLite** — les comportements de verrouillage
   diffèrent, et un test vert sur SQLite ne dit rien de la production.
7. **Cloisonnement fermé par défaut** : portée globale + policies. Chaque
   nouvelle ressource ajoute son test d'isolation.
8. **Un secret n'existe jamais en clair** : ni en base, ni dans les logs, ni dans
   une réponse d'API non authentifiée. Vérifié en CI par `scan-secrets.sh`.
9. **Les valeurs du `docker-compose.yml` sont des valeurs de dev**, jamais un
   secret réel. Les vrais secrets vivent dans `backend/.env`, non commité.
10. À COMPLÉTER — les règles transverses propres au projet (langues obligatoires,
    accessibilité, traçabilité, rétention).

## 4. Gates CI

| Gate | Contenu | Bloque le merge |
|---|---|---|
| Secrets | `.github/scan-secrets.sh` sur les fichiers suivis | oui |
| Statique | `pint --test`, `phpstan analyse` (niveau 8) | oui |
| Migrations | `artisan migrate --force` sur PostgreSQL éphémère | oui |
| Tests | `pest` sur PostgreSQL éphémère | oui |
| Dépendances | `composer audit` | oui |

Détail des niveaux : [testing-strategy.md](testing-strategy.md) §4.

## 5. Commandes

Toutes préfixées par le conteneur — **aucun service backend n'existe sur le
poste** :

| Intention | Commande |
|---|---|
| Démarrer l'environnement | `docker compose up -d` |
| État des services | `docker compose ps` |
| Suite de tests | `docker compose exec -T app ./vendor/bin/pest` |
| Un seul fichier de test | `docker compose exec -T app ./vendor/bin/pest tests/Feature/XTest.php` |
| Formatage | `docker compose exec -T app ./vendor/bin/pint` |
| Vérifier le formatage | `docker compose exec -T app ./vendor/bin/pint --test` |
| Analyse statique | `docker compose exec -T app ./vendor/bin/phpstan analyse` |
| Migrations | `docker compose exec -T app php artisan migrate` |
| Repartir de zéro | `docker compose down -v && docker compose up -d` |

**Ports** — décalés volontairement, un poste de dev héberge souvent déjà ces
services : app **8080**, PostgreSQL **5433**, Redis **6380**, Mailpit **8026**.

> Ces commandes sont celles que `/deliver-story` exécutera et **dont il citera la
> sortie réelle**. Si une commande n'est pas ici, il n'a pas à la deviner.
