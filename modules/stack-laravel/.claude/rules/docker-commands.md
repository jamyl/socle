# Commandes — tout passe par le conteneur

Référencé par plusieurs sous-agents. **Aucun service backend n'est installé sur
le poste** : une commande sans préfixe `docker compose exec` échouera, ou pire,
tapera dans un service système qui n'est pas le nôtre.

`-T` désactive le pseudo-terminal : indispensable dès qu'on lit la sortie.

| Intention | Commande |
|---|---|
| Démarrer | `docker compose up -d` |
| État | `docker compose ps` |
| Logs d'un service | `docker compose logs -f app` |
| Shell | `docker compose exec app sh` |
| Suite de tests | `docker compose exec -T app ./vendor/bin/pest` |
| Un fichier de test | `docker compose exec -T app ./vendor/bin/pest tests/Feature/XTest.php` |
| Un test par son nom | `docker compose exec -T app ./vendor/bin/pest --filter="fragment"` |
| Formatage | `docker compose exec -T app ./vendor/bin/pint` |
| Vérifier le formatage | `docker compose exec -T app ./vendor/bin/pint --test` |
| Analyse statique | `docker compose exec -T app ./vendor/bin/phpstan analyse` |
| Migrations | `docker compose exec -T app php artisan migrate` |
| Une commande artisan | `docker compose exec -T app php artisan <cmd>` |
| Repartir de zéro | `docker compose down -v && docker compose up -d` |

## Ports — décalés volontairement

| Service | Hôte | Pourquoi pas le port standard |
|---|---|---|
| app | **8080** | 8000 est souvent pris |
| PostgreSQL | **5433** | un poste de dev héberge souvent déjà un PostgreSQL |
| Redis | **6380** | idem |
| Mailpit (web) | **8026** | http://localhost:8026 |

⚠️ **Deux services sur le même port, et c'est l'ancien qui répond** — le pire des
symptômes, parce qu'il répond. Si une connexion « marche » mais que les données
n'ont aucun sens, vérifier le port avant le code.

## Pièges

- `vendor/` est un **volume nommé**, pas un bind mount : il n'apparaît pas dans
  le dossier hôte. `composer install` se lance dans le conteneur.
- Tant que Laravel n'est pas scaffoldé (US-104), `app` et `horizon` tournent en
  veille volontaire — ce n'est pas une panne.
- `docker compose down -v` **détruit les volumes**, donc la base de dev. C'est
  voulu pour repartir propre ; ce n'est pas ce qu'on veut par réflexe.
