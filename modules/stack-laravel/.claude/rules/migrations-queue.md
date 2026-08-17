# Migrations & files d'attente

Référencé par plusieurs sous-agents.

## Migrations

- `declare(strict_types=1);`, classe anonyme (`return new class extends Migration`).
- **Additives uniquement** sur toute table portant des données réelles : jamais
  de `DROP`, jamais d'`ALTER` destructif. Sur une table de référence, une
  mauvaise migration n'est pas un bug — c'est une preuve détruite.
- 🔑 **Un `down()` qui ne peut pas être honnête refuse de tourner.** Il lève une
  exception explicite plutôt que de prétendre annuler ce qu'il ne peut pas
  annuler. Un `down()` qui promet l'irréversibilité sans la faire respecter est
  un piège pour la personne suivante.
- ⚠️ **PostgreSQL emporte toute contrainte portant sur une colonne détruite.**
  Un `dropColumn()` en `down()` supprime aussi les `CHECK` qui **préexistaient** à
  la migration : il faut les **recréer dans leur forme d'avant**. Défaut réel,
  trouvé en revue.
- Le DDL de PostgreSQL est **transactionnel** : un `DROP CONSTRAINT` suivi d'un
  `ADD CONSTRAINT` dans la même migration ne laisse aucune fenêtre sans borne.
- Une contrainte `CHECK` régénérée depuis un enum doit rester **réconciliée**
  avec le code — un test d'architecture qui refuse toute CHECK non déclarée vaut
  mieux qu'une revue humaine.

## Files d'attente (Horizon / Redis)

- Un job est **idempotent** : il sera rejoué. Poser une clé d'idempotence sur
  l'effet, pas sur le job.
- `ShouldBeUnique` + `uniqueId()` quand deux exemplaires du même job ne doivent
  pas coexister.
- `$tries` et `$backoff` explicites. Un job qui réessaie indéfiniment masque une
  panne au lieu de la signaler.
- `failed()` implémenté : un job mort laisse un état cohérent, ou compense.
- Un job **ouvre son propre contexte** (tenant, locale) : il ne l'hérite pas de
  la requête qui l'a dispatché.
- ⚠️ En test, la queue est `sync` : le job part **en ligne**. Un test qui compte
  des effets doit mesurer un **delta**.
