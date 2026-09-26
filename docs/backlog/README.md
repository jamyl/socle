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
par story, écrite par `/deliver-story`. Les choix tranchés sans arbitrage humain
sont dans [DECISIONS.md](DECISIONS.md), à relire en fin de cycle.

> ⚠️ **Un statut `bloqué` porte toujours son motif entre parenthèses**, et ce
> motif dit ce qui est attendu et **de qui**. « bloqué » seul fait perdre un tour
> à chaque itération de la boucle.

## Epics

| Epic | Titre | Priorité | Fichier |
|---|---|---|---|
| E01 | Fondations projet & environnement | P0 | [E01-fondations.md](E01-fondations.md) |
| E02 | À COMPLÉTER | | |

> `E01-fondations.md` est écrit à l'amorçage : le module `stack-laravel` en livre
> un pré-écrit, sinon `/bootstrap-project` le rédige. **Tant que ce fichier
> n'existe pas, le lien ci-dessus est mort et le backlog n'a aucune story
> actionnable** — c'est le symptôme d'un amorçage inachevé, pas d'un bug.

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

## Gabarit d'une story

`/cadrer-story` le produit. Il vaut pour tout ce qui s'écrit désormais ; les
stories déjà `fait` restent en texte libre — les convertir coûterait cher et ne
prouverait rien de plus.

```markdown
## US-XYZ — Titre court
**En tant que** <rôle>, **je veux** <capacité> **afin de** <bénéfice>.
**Priorité** P0 · **Estimation** S · **Statut** à faire
**Dépend de** : US-ABC
**Référence visuelle** : docs/maquettes/dossier.png   ← optionnel, story d'interface seulement

Critères d'acceptation :
- [ ] **Le type est obligatoire à la création**
      Étant donné que je crée le dossier « Atelier Nord »
      Quand je valide le formulaire sans choisir de type
      Alors la création est refusée, et le champ manquant est signalé
```

Le titre en gras **est** le nom du test : un scénario, un test. La case à cocher
reste une case à cocher, `/deliver-story` la coche `[x]` en livrant.

`Référence visuelle` (maquette, capture, URL) déclenche la boucle visuelle de
`/deliver-story` §4 : capture de l'écran livré, comparaison, écarts corrigés.
Sans elle, l'étape est sautée — une story sans interface n'a rien à comparer.

## Checklist d'entrée au backlog

À passer sur chaque story **avant** qu'elle prenne le statut `à faire`. Une story
qui échoue à un item ne s'écrit pas : on la corrige d'abord. La source de chaque
règle est citée entre parenthèses.

- [ ] Le requis est reformulé en une phrase, sans jargon (BABOK, *Elicitation*)
- [ ] Un exemple concret et nommé accompagne l'énoncé (*Specification by Example*)
- [ ] Chaque mot métier nouveau a une définition, une seule (IREB, non ambiguë)
- [ ] Toute question ouverte est tranchée, datée et écrite dans [DECISIONS.md](DECISIONS.md) comme décision `D<n>`, avec l'alternative écartée et le coût du revirement ; aucune règle métier inventée sans sa ligne (IREB, complète et traçable)
- [ ] La story ne contredit pas une story déjà `fait` (IREB, cohérente)
- [ ] Elle passe les six lettres d'INVEST, en particulier *Small* et *Testable*
- [ ] Chaque critère a un scénario nominal, et la story au moins un scénario de refus ou de cas limite (BDD)
- [ ] Chaque *Alors* est observable : un écran, une valeur, un refus. Jamais « correctement » ni « rapidement » (IREB, vérifiable)
- [ ] Aucun critère ne nomme une bibliothèque — le choix technique vit dans [stack.md](../engineering/stack.md)
- [ ] Chaque règle de `CLAUDE.md` § « règles qui coûtent le plus cher à violer » que la story touche a son scénario qui la prouve
- [ ] Priorité P0–P3 posée avec sa justification, estimation XS–L, `Dépend de` vérifié contre les statuts réels (MoSCoW)

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

- **La chaîne** : `/cadrer-story` écrit la story · `/deliver-story` la livre ·
  `review-story` relit le diff · `/security-review` garde le domaine critique. Le
  cadrage est séparé de la livraison parce qu'une story mal cadrée coûte une
  branche déjà ouverte.
- **Une story = un cycle** : `/deliver-story`. Branche → plan → TDD → tests verts
  → revue en fan-out → `/security-review` si le domaine critique est touché → PR
  → CI verte → merge squash.
- Commencer chaque session en lisant le fichier de l'epic en cours, **pas tout le
  backlog**.
- Les questions métier passent par l'agent `domain-expert`.
- Les décisions d'architecture structurantes passent par `/dejavu`, et leur
  conclusion se consigne dans
  [../engineering/prior-art.md](../engineering/prior-art.md).
