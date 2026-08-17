# Règles de test — Pest / PostgreSQL

Référencé par plusieurs sous-agents. La stratégie complète est dans
`docs/engineering/testing-strategy.md` ; ceci en est le rappel opérationnel.

## Non négociable

- **PostgreSQL, jamais SQLite.** Les verrous et les contraintes diffèrent : un
  test vert sur SQLite ne dit rien de la production. ⚠️ Le `phpunit.xml` par
  défaut de Laravel pointe sur SQLite — le basculer fait partie d'US-104.
- **Factories uniquement.** Jamais de fixture mutable partagée entre tests.
- **Aucun appel à un service externe réel.** Chaque tiers vit derrière une
  interface avec un fake.
- Un test par comportement des critères d'acceptation. Un test qui vérifie trois
  choses ne dit pas laquelle a cassé.

## Arborescence

```
tests/Unit/         logique pure, sans base ni réseau (< 30 s la suite)
tests/Feature/      endpoints complets, policies, isolation inter-tenants
tests/Concurrency/  N processus RÉELS (pcntl_fork), pas de RefreshDatabase
```

## Les pièges de cette stack, vécus

- **`->throws()` à deux appels** : le premier lève, le second n'est jamais
  atteint. **Un seul** appel par assertion d'exception.
- **La queue est `sync` en test**, et Laravel fait partir les jobs `afterCommit`
  sous `RefreshDatabase` : un job dispatché s'exécute **en ligne** pendant le
  test. Mesurer un **delta**, jamais un compte absolu.
- **Le guard d'auth met en cache l'utilisateur résolu** par instance
  d'application : `app('auth')->forgetGuards()` après un changement d'identité.
- **`RefreshDatabase` ouvre une transaction** : y insérer en masse rend les
  lignes invisibles au collecteur de statistiques. Une mesure de performance
  absurde vient des statistiques du moteur avant de venir du code
  (`ANALYZE` explicite après le chargement).
- **Un test de concurrence doit prouver sa mise en scène** : chaque processus
  enregistre sa fenêtre, le test **exige un recouvrement**. Sans ça, N
  opérations qui se sont suivies rendent le même vert.

## Ce qui rend un test recevable

**On l'a vu échouer.** Retire le garde, relance, constate le rouge, restaure.
Les huit motifs de fausse vérification sont dans
`.claude/skills/deliver-story/SKILL.md`.

*« Que devrait voir ce test pour devenir rouge ? »* — si la réponse n'est pas
immédiate et concrète, il ne couvre rien.
