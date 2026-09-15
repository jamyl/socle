# Contribuer à {{PROJET}}

> Ce fichier appartient au **projet engendré**, pas au template. Pour contribuer
> à `socle` lui-même, voir la section « Contribuer » de son README.

## Convention de commits

Un commit = **une story livrée**, format court :

```
US-XXX: sujet à l'impératif
```

Hors story (outillage, correctif, doc) — préfixe par un type :

```
fix: corrige <le comportement>
chore: met à jour les digests des images Docker
docs: précise <le point>
```

## Branches

Trunk-based : branches courtes, **PR obligatoire**, CI verte avant merge,
**jamais de push direct sur `main`**.

```bash
git checkout -b us-201-sujet-court
```

Aucune branche ne survit à sa PR (`gh pr merge --squash --delete-branch`). Une
branche qui traîne signale une story non clôturée.

## Avant d'ouvrir une PR

Les commandes exactes vivent dans
[`docs/engineering/stack.md`](docs/engineering/stack.md) §5 — formatage, analyse
statique, suite de tests.

Une story n'est `fait` que si ces commandes passent **réellement**, et le rapport
cite leur **sortie réelle**. Jamais « ça devrait passer ».

Et un cran au-dessus : **le test doit avoir été vu échouer.** Retire le garde
qu'il prétend couvrir, relance, constate le rouge, restaure. Une vérification qui
reste verte ne prouve rien — et vaut moins que rien, car on cessera de la
regarder. Les huit motifs de fausse vérification sont dans
[`.claude/skills/deliver-story/SKILL.md`](.claude/skills/deliver-story/SKILL.md).

## Règles non négociables

Les règles **techniques** vivent dans
[`docs/engineering/stack.md`](docs/engineering/stack.md) §3.

Les règles **du domaine** — celles qui coûtent le plus cher à violer — vivent
dans [`CLAUDE.md`](CLAUDE.md), et sont reprises par le nœud `domain-expert` de la
revue en fan-out. Quand l'une bouge, les deux bougent.

## Livrer une story

Le backlog vit dans [`docs/backlog/`](docs/backlog/). La commande
`/deliver-story` livre la prochaine story actionnable en TDD et tient
[`docs/backlog/JOURNAL.md`](docs/backlog/JOURNAL.md).
