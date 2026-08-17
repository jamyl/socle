# Style de code — backend PHP/Laravel

Référencé par plusieurs sous-agents. Complète `docs/engineering/stack.md` §3.

## Non négociable

- `declare(strict_types=1);` **dans chaque fichier**.
- Types explicites partout : paramètres, retours, propriétés. Larastan est au
  **niveau 8**, sans baseline d'exceptions.
- `final` par défaut sur les classes ; on ouvre à l'héritage quand on en a la
  raison, pas l'inverse.
- `Model::query()` plutôt que les méthodes statiques ; `getKey()` plutôt que
  `->id`.
- Un état = un **enum PHP** avec matrice de transitions explicite. Jamais une
  chaîne libre, jamais un booléen qui devient trois états six mois plus tard.

## Où vit quoi

```
FormRequest  → validation de la forme
Action       → une intention métier, une classe, un __invoke
Service      → coordination de plusieurs actions, accès à un tiers
Resource     → forme de la réponse
Model        → relations, casts, scopes. PAS de logique métier
```

**Aucune logique métier dans un contrôleur ni dans une ressource Filament.**

## Commentaires

Les commentaires de ce dépôt sont denses **et c'est assumé** : ils expliquent
*pourquoi*, jamais *quoi*. Deux règles qui viennent d'une leçon coûteuse :

1. **Ne jamais affirmer un mécanisme.** Écrire « ce verrou sérialise les
   écritures concurrentes », pas « ce verrou EST ce qui garantit l'unicité ».
   Sur le projet d'origine, quatre docblocks affirmant une garantie se sont
   révélés **faux** — dont un que la contre-épreuve a démenti. Un commentaire
   qui affirme et qui mente est **pire que pas de commentaire** : on cesse de le
   vérifier.
2. **Un commentaire qui décrit un invariant nomme le test qui le tient.** Sinon
   c'est un souhait.

## Nommage

Code, identifiants et messages de commit en **anglais**. Les commentaires et la
documentation suivent la langue du projet (voir `CLAUDE.md`).
