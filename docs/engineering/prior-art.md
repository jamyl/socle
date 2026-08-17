# Antériorité — décisions validées

Journal des recherches `/dejavu`. Une section par recherche. **À lancer avant
toute décision d'architecture structurante** — mécanisme de cohérence ou de
concurrence, schéma de cache, protocole, intégrité cryptographique, scale-out,
scoring ou recherche. Pas pour du CRUD ni du glue code.

Chaque conclusion porte ses **identifiants** (arXiv, DOI) : sans eux, la recherche
est à refaire à la session suivante — et elle le sera, parce que personne ne fait
confiance à une conclusion qu'il ne peut pas rouvrir.

## Ce qu'une section doit contenir

```markdown
## AAAA-MM-JJ — <la question d'architecture, pas le produit>

**Périmètre** : la décision en jeu, et ce qu'elle engage.
**Sources lues** : n documents, sources interrogées, catégories.
**Diagnostics** : ce que le bloc `diagnostics` du script a signalé
  (source en échec, zéro résultat, réponse de cache périmée).

**Conclusion** : une phrase.

**Retenu** :
- <constat> (arXiv XXXX.XXXXX / DOI 10.xxxx/yyyy)

**Écarté** : ce qui ne s'appliquait pas, et pourquoi. Une catégorie qui ne rend
rien d'exploitable se **déclare écartée** — on ne gonfle pas le corpus.

**Réserves** : rétractations ou corrections signalées, affirmations venant d'un
éditeur qui vend la solution, angles morts (aucune source académique n'indexe
les **brevets**, or c'est là que vit une part de l'antériorité réelle d'un
produit).
```

## Règles de tenue

- **Une recherche qui ne trouve rien est un résultat**, à écrire comme tel. Zéro
  antériorité pertinente ≠ problème non résolu : ça peut vouloir dire que le
  sujet n'est pas un sujet de publication.
- **Ne jamais présenter une passe dégradée comme propre.** Si une source est
  tombée ou a rendu zéro, le bloc `diagnostics` le dit — recopier ce qu'il dit.
- **Ce que `/dejavu` ne couvre pas** reste à faire à la main : les brevets
  (Google Patents, Espacenet) et la pratique industrielle hors littérature
  académique.
- Si le pre-flight de `/dejavu` conclut ABORT, **le consigner aussi** : « pas de
  matière à recherche » est une décision documentée, pas un oubli.

---

*Aucune recherche consignée pour l'instant.*
