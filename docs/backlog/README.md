# {{PROJET}} — Backlog produit (index)

Un fichier par epic, des user stories numérotées `US-XYZ` (X = numéro d'epic).
Cadrage : [../product/vision.md](../product/vision.md).

## Légende

**Priorités**
- **P0** — bloquant : sans ça, pas de premier jalon.
- **P1** — important : livrable pendant le jalon si nécessaire.
- **P2** — après le premier jalon.
- **P3** — vision long terme.

**Estimations** (jours de dev effectif avec Claude Code)
- **XS** ≤ 0,5 j · **S** = 1 j · **M** = 2-3 j · **L** = 5 j ·
  **XL** = à découper **avant** de démarrer.

**Statuts** : `à faire` → `en cours` → `fait`, ou `bloqué (motif précis)` quand
une action externe est attendue. Mise à jour directement dans les fichiers
d'epic. Le fil des livraisons est tenu dans [JOURNAL.md](JOURNAL.md) — une ligne
par story, écrite par `/deliver-story`.

> ⚠️ **Un statut `bloqué` porte toujours son motif entre parenthèses**, et ce
> motif dit ce qui est attendu et **de qui**. « bloqué » seul fait perdre un tour
> à chaque itération de la boucle.

## Epics

| Epic | Titre | Priorité | Fichier |
|---|---|---|---|
| E01 | Fondations projet & environnement | P0 | [E01-fondations.md](E01-fondations.md) |
| E02 | À COMPLÉTER | | |

## Roadmap indicative

| Jalon | Contenu | Sortie observable |
|---|---|---|
| J1 | E01 | Environnement opérationnel, CI verte |
| J2 | À COMPLÉTER | |

> La roadmap n'est qu'un **ordre de préférence**. La source unique
> d'ordonnancement est le graphe des dépendances (« Dépend de » de chaque story) :
> une story dont une dépendance vit dans un epic plus loin est sautée, puis
> redevient candidate quand sa dépendance est livrée. Aucune exception n'a besoin
> d'être codée en dur.

## Definition of Done (toutes les stories)

1. Critères d'acceptation couverts par des tests automatisés au niveau prévu par
   [la stratégie de tests](../engineering/testing-strategy.md).
2. La commande de test est **passée** et sa sortie réelle rapportée — jamais
   « ça devrait passer ».
3. Le test a été vu **échouer** : garde retiré, rouge constaté, garde restauré.
4. Aucune règle de `CLAUDE.md` § « règles qui coûtent le plus cher à violer »
   contournée ; aucune donnée sensible en clair dans les logs.
5. La spec de l'epic mise à jour si le comportement livré diffère du prévu.
6. À COMPLÉTER — les exigences transverses du projet (langues, accessibilité,
   traçabilité…).

## Méthode de travail

- **Une story = un cycle** : `/deliver-story`. Branche → plan → TDD → tests verts
  → revue en fan-out → `/security-review` si le domaine critique est touché → PR
  → CI verte → merge squash.
- Commencer chaque session en lisant le fichier de l'epic en cours, **pas tout le
  backlog**.
- Les questions métier passent par l'agent `domain-expert`.
- Les décisions d'architecture structurantes passent par `/dejavu`, et leur
  conclusion se consigne dans
  [../engineering/prior-art.md](../engineering/prior-art.md).
