# `/dejavu` — recherche d'antériorité embarquée

Ce fichier vient du module `dejavu`, activé à l'amorçage. Il documente un skill
qui vit désormais dans `.claude/skills/dejavu/`.

## À quoi ça sert

Avant de bâtir un mécanisme non trivial, lire ce qui a déjà été publié dessus.
Le skill interroge arXiv, OpenAlex, Crossref et Europe PMC par des scripts
déterministes, fait lire **un document par sous-agent isolé** — pour qu'aucune
source n'ancre les autres — note et regroupe les lectures, vérifie les
rétractations, puis converge sur **un seul** chemin recommandé, cité, avec un
premier pas concret et les pièges déjà connus.

Ce n'est pas un moteur de recherche : une recherche rend des sources, `/dejavu`
force une décision fondée sur elles.

Quand l'utiliser : cohérence, concurrence, cache, protocole, intégrité
cryptographique, scale-out, scoring, recherche — tout ce dont « la version naïve
casse à l'échelle ». Le skill a son propre pre-flight et **refuse de tourner**
sur du CRUD, du glue code ou une approche déjà tranchée. Respecter ce refus.

Les conclusions se consignent dans `docs/engineering/prior-art.md` **avec leurs
identifiants** (arXiv, DOI). Sans eux, la recherche est à refaire à la session
suivante — et elle le sera, parce que personne ne fait confiance à une conclusion
qu'il ne peut pas rouvrir.

## Prérequis

| Quoi | Vérification | Si absent |
|---|---|---|
| `python3` | `python3 --version` | Les scripts sont en **bibliothèque standard seule** : rien à installer avec `pip`, mais l'interpréteur est requis |
| `DEJAVU_CONTACT` | `echo $DEJAVU_CONTACT` | `echo 'export DEJAVU_CONTACT="Ton Nom ton@email"' >> ~/.zshrc` puis **rouvre le terminal** |

Aucune clé d'API pour aucune des quatre sources.

⚠️ **`DEJAVU_CONTACT` doit être dans ton `~/.zshrc`, pas seulement exporté dans
un terminal.** Un `export` à la main n'est pas visible depuis Claude Code : son
processus a démarré avant. Les APIs académiques réclament ce contact.

Le cache vit dans `~/.cache/dejavu`, **hors du dépôt** : il ne se commite pas et
il se partage entre projets — un run ici réchauffe le cache d'ailleurs.
`DEJAVU_CACHE_DIR` le déplace.

```bash
.claude/skills/dejavu/scripts/search.py --terms x --cache-stats
```

`--terms` est obligatoire même pour lire les statistiques : c'est une exigence de
l'analyseur d'arguments en amont, pas une faute de frappe ici.

## Ce que ça coûte

Un run = 1 catégorisation + N lectures isolées (typiquement 12 à 20) + 1 notation
+ 1 regroupement + jusqu'à 3 lectures de texte intégral + 1 convergence, plus du
HTTP réel. Ce n'est pas gratuit : à réserver aux décisions dont l'erreur coûte
une réécriture, pas une correction.

## Ne pas l'installer deux fois

Si `~/.claude/skills/dejavu/` existe déjà sur le poste — installation globale par
`npx github:jamyl/dejavu install` — **ne pas activer ce module** : deux skills
portant le même nom coexisteraient, et lequel gagne n'est pas une chose à
découvrir en cours de projet. Vérifier avant :

```bash
ls ~/.claude/skills/dejavu/SKILL.md 2>/dev/null && echo "DÉJÀ GLOBAL — ne pas activer le module"
```

Le module a un avantage sur l'installation globale : il est **versionné avec le
projet**. Tout le monde qui clone le dépôt a la même version du skill, et un
changement de comportement se lit dans un diff.

## Mettre à jour

Le contenu de `.claude/skills/dejavu/` est une **copie intacte** de l'amont. Il
ne se modifie pas ici : un correctif se fait en amont, puis se recopie.

```bash
git clone https://github.com/jamyl/dejavu /tmp/dejavu
rsync -a --delete --exclude '__pycache__' --exclude '*.pyc' \
  /tmp/dejavu/skills/dejavu/ .claude/skills/dejavu/
python3 -m compileall -q .claude/skills/dejavu/scripts && echo OK
```

Version embarquée : **v0.2.0**, commit `7c9fded` de `jamyl/dejavu`.

## Licence et provenance

MIT. `dejavu` est un fork de
[neuroarxiv](https://github.com/UditAkhourii/neuroarxiv) d'Udit Akhouri, qui a
apporté la boucle diverger-puis-converger et la méthode d'évaluation. Les avis
de copyright des deux projets s'appliquent à cette copie :

```
Copyright (c) 2026 Jamyl                    — dejavu
Copyright (c) Udit Akhouri                  — neuroarxiv, dont dejavu est un fork
```

Le fork ajoute l'abstraction des fournisseurs, la couche de récupération
déterministe compatible proxy, le cache partagé, la vérification des
rétractations, l'escalade en texte intégral, la recherche d'antériorité dans le
code, et la taxonomie arXiv complète.

## Ce que le module n'embarque pas

`dejavu-finance` — le même moteur sur les dépôts SEC — n'est **pas** inclus. Il
n'a d'objet que sur une pratique de marché américaine, et son script est un
lanceur qui cherche le skill de base en voisin. Pour l'ajouter, l'installer
globalement : `npx github:jamyl/dejavu install`.

Le moteur TypeScript de la CLI autonome (`dejavu "<problème>"` hors de Claude
Code) n'est pas inclus non plus : il demande `npm install` et le SDK Anthropic.
Les scripts embarqués ici sont utilisables seuls, sans LLM dans la boucle :

```bash
.claude/skills/dejavu/scripts/search.py --terms "cache invalidation" --categories cs.DB
.claude/skills/dejavu/scripts/fulltext.py --id 2311.02384
.claude/skills/dejavu/scripts/codesearch.py --terms "cache invalidation" --limit 5
```
