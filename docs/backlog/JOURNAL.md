# Journal des livraisons — {{PROJET}}

Une ligne par story livrée, écrite par `/deliver-story` à la clôture. Format :

```
- [AAAA-MM-JJ HH:MM] US-XXX <titre> — fait|bloqué(motif) — tests : <commande> → <résultat réel> — essais : <N> — suivante : US-YYY
```

**La date vient de la commande `date`**, jamais d'une estimation. Le résultat est
la **sortie réelle** de la commande, pas une paraphrase. Le nombre d'essais est
celui que compte `eval-run.mjs retro` : il dit ce que la story a coûté à
trouver, ce qu'aucune autre colonne ne montre.

Ce fichier est le premier que lit `/deliver-story` : il y trouve le contexte des
itérations passées, la story annoncée comme suivante, et les blocages connus.
C'est aussi la raison pour laquelle il reste **court** — une ligne par story. Le
récit détaillé vit dans le corps de la PR, où il est lu avec le diff.

---

*Aucune livraison pour l'instant.*
