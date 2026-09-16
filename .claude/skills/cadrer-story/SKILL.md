---
name: cadrer-story
description: Transforme un requis brut — une phrase, une décision consignée, un finding d'audit, une contrainte reçue d'un tiers — en stories `à faire` prêtes pour /deliver-story : critères en Étant donné/Quand/Alors, décisions consignées, priorité et dépendances posées. Écrit dans un fichier d'epic, ne code jamais.
argument-hint: "<le requis brut, et l'epic cible si tu le sais>"
---

# Cadrer un requis en stories livrables

Tu transformes **un requis brut** en **2 à 5 user stories `à faire`** dans un
fichier d'epic. Tu n'écris aucun code, tu ne livres rien : `/deliver-story` prend
le relais ensuite, sans avoir à te relire.

**Le cadrage est séparé de la livraison exprès.** Une story mal cadrée découverte
par `/deliver-story` coûte une branche déjà ouverte, un plan déjà écrit et une
itération perdue. Ici, elle ne coûte qu'une relecture.

`/bootstrap-project` n'écrit que E01. Tout le reste du backlog passe par ce skill.

## Ce que tu NE changes pas

Ce cycle a déjà son vocabulaire. Ne lui en ajoute pas un deuxième.

| Ce que la littérature appelle | Ce que ce projet utilise déjà |
|---|---|
| MoSCoW (Must / Should / Could / Won't) | **P0 / P1 / P2 / P3** de `docs/backlog/README.md`. Won't = « Hors périmètre, délibérément » (`docs/product/vision.md` §5) |
| Ordonnancement, WSJF, RICE | Le **graphe `Dépend de`**, seule source d'ordonnancement de `/deliver-story` §1 |
| Format Connextra | `**En tant que** … **je veux** … **afin de** …`, déjà le gabarit du backlog |
| Validation avec les parties prenantes | **`docs/backlog/DECISIONS.md`** : on tranche, on consigne `D<n>`, l'utilisateur valide en fin de cycle |
| Hypothèses (Lean, validées par une expérience) | `docs/product/vision.md` §8, `H<n>` — **réservé au produit**. Ici on tranche des **décisions** `D<n>` ; ne mélange pas les deux numérotations |
| Découpage d'une story trop grosse | Sous-stories `US-XXXa`, `US-XXXb` dans le fichier d'epic |

Et surtout : **les stories déjà `fait` ne se réécrivent pas.** Le gabarit
Étant donné/Quand/Alors s'applique à ce que tu crées, jamais rétroactivement.
Convertir des critères historiques coûte cher et ne prouve rien de plus.

## Entrée

Un requis brut, sous n'importe quelle forme : une phrase de l'utilisateur, une
ligne de `DECISIONS.md`, une contrainte reçue d'un tiers, un finding d'audit ou
de `/security-review`. Et un epic cible. Si l'epic n'est pas évident, choisis-le
et dis pourquoi en une phrase.

Si l'epic n'existe pas encore, crée le fichier `docs/backlog/E0X-<slug>.md` et
ajoute sa ligne au tableau des epics de `docs/backlog/README.md` — un epic absent
de l'index est un epic que `/deliver-story` ne balaiera pas.

## 1. Fiche d'exigence

*BABOK, domaine « Elicitation & Collaboration » ; IREB, critères de qualité d'une
exigence : non ambiguë, complète, vérifiable, atomique, cohérente, nécessaire,
traçable.*

Produis une fiche, dans ta réponse et non dans un fichier :

| Champ | Contenu |
|---|---|
| Énoncé reformulé | Une phrase, sans jargon, sans nom de classe |
| Origine | D'où vient le requis, avec sa date |
| Glossaire | Chaque mot métier nouveau, une définition chacun |
| Questions ouvertes | Tout ce que le requis ne dit pas |
| Décisions | Chaque question ouverte, tranchée |

**Une question ouverte ne se pose pas : elle se tranche.** Chaque question devient
une décision `D<n>` — le numéro suivant du journal — appliquée, et **une ligne
dans `docs/backlog/DECISIONS.md`** au format du fichier : numéro, date, story,
question, ce qui est retenu en gras, l'alternative écartée, le coût du
revirement. Marque `🔴` toute décision qui touche le domaine critique déclaré
dans `CLAUDE.md` — celui qui porte les règles les plus chères à violer.

C'est ce qui permet au cadrage de tourner sans t'arrêter, y compris sous `/loop` :
une boucle ne peut pas attendre une réponse.

⚠️ **Ne jamais inventer une règle métier absente du requis.** Une règle inventée
et non signalée devient un fait dans six mois. Si une décision touche le domaine
critique, passe par l'agent `domain-expert` avant de la trancher.

**Ce qui interrompt encore** : une action humaine ou externe — avis juridique,
compte à créer chez un tiers, clé d'API, arbitrage business, choix de prix. Là, la
story s'écrit quand même mais naît **`bloqué (motif précis)`**, exactement comme
dans `/deliver-story` §1.4. Le motif dit ce qui est attendu, et de qui.

## 2. Décomposition

*Story mapping (Patton) pour trouver les stories ; INVEST pour les valider.*

Trace le parcours dans l'ordre où il se vit — première prise en main, usage
courant, cas d'exception, fin de vie — puis pose une story par étape qui a de la
valeur seule. Deux à cinq stories. Au-delà, tu cadres un epic et non un requis :
dis-le et découpe en deux passes.

Passe chaque story au filtre **INVEST** avant de l'écrire :

| Lettre | La question à laquelle tu dois répondre |
|---|---|
| **I**ndependent | Peut-elle être livrée sans qu'une autre soit livrée en même temps ? |
| **N**egotiable | Décrit-elle un besoin, pas une implémentation ? |
| **V**aluable | Qui est content quand elle est livrée, et pourquoi ? |
| **E**stimable | Peux-tu poser XS/S/M/L sans hésiter ? |
| **S**mall | Tient-elle dans une itération (≤ L) ? |
| **T**estable | Sais-tu dire, en une phrase, ce qui la rendrait rouge ? |

Une story qui échoue à **Small** ou **Testable** se redécoupe **avant** d'être
écrite.

## 3. Gabarit d'écriture

Écris dans le fichier d'epic, à sa place dans l'ordre de lecture :

```markdown
## US-XYZ — Titre court
**En tant que** <rôle>, **je veux** <capacité> **afin de** <bénéfice>.
**Priorité** P0 · **Estimation** S · **Statut** à faire
**Dépend de** : US-ABC

Critères d'acceptation :
- [ ] **Le type est obligatoire à la création**
      Étant donné que je crée le dossier « Atelier Nord »
      Quand je valide le formulaire sans choisir de type
      Alors la création est refusée, et le champ manquant est signalé
- [ ] **Le type est enregistré**
      Étant donné que je crée le dossier « Atelier Nord »
      Quand je choisis le type « externe » et je valide
      Alors la fiche de « Atelier Nord » affiche le type « externe »

> **[D7] Le type reste modifiable après la création.** Le requis ne parlait que
> de la création. Consigné le JJ/MM dans DECISIONS.md.
```

Règles d'écriture des critères — *BDD, Given/When/Then ; Specification by Example
(Adzic)* :

1. **La case à cocher reste une case à cocher.** `/deliver-story` §3 coche `[x]`
   au fur et à mesure : ne casse pas ce format, le scénario vit dessous, indenté.
2. **Le titre en gras est le nom du test.** Un scénario = un test.
3. **Un seul *Quand* par scénario.** Deux actions = deux scénarios.
4. **Des valeurs concrètes et nommées** : « Atelier Nord », « 12 articles », pas
   « un dossier » ni « une quantité ».
5. **Le *Alors* s'observe** : un écran, une valeur, un refus, une ligne de
   journal. Jamais « le système fonctionne correctement ».
6. **Un scénario nominal ET un scénario de refus ou de cas limite** par story.
   Une story qui n'a que du chemin heureux n'a pas été cadrée.
7. **Nommer une bibliothèque dans un critère est un défaut.** Un critère qui cite
   son outil se vérifie en lisant le code, pas en observant le produit. Le choix
   technique vit dans `docs/engineering/stack.md`, pas dans le critère.
8. **Chaque règle du domaine que la story touche a son scénario qui la prouve.**
   Les règles sont celles de `CLAUDE.md` § « les règles qui coûtent le plus cher
   à violer ». C'est le seul endroit où elles deviennent exécutables : si aucun
   scénario ne les cite, la revue en fan-out est le dernier filet, et il est plus
   fin que prévu.

Les décisions se recopient sous la story en blockquote `>`, avec leur `D<n>`. Le récit long va dans
le corps de la PR, pas ici.

## 4. Contrôle qualité

*IREB, validation ; BABOK, « Approve Requirements ».*

La checklist d'entrée au backlog vit dans `docs/backlog/README.md`, section
« Checklist d'entrée au backlog ». Passe-la sur chaque story. **Une story qui
échoue à un item ne s'écrit pas** : corrige-la d'abord.

Trois contrôles se font en commande, pas à l'œil :

```bash
grep -n "Dépend de" docs/backlog/E0X-*.md     # les cibles existent-elles ?
grep -n "Statut" docs/backlog/E0X-*.md         # une dépendance déjà `fait` ?
grep -c "Quand " docs/backlog/E0X-*.md         # autant que de critères créés
```

## 5. Priorité et ordre

*MoSCoW, via l'échelle P0–P3 existante.*

Pose la priorité avec sa justification en une phrase, et vérifie que `Dépend de`
pointe vers des stories qui existent réellement. Règle DSDM utile : si tout est
P0, rien ne l'est — au-delà de deux P0 dans une passe de cadrage, justifie chacun.

Ne touche pas à la roadmap de `docs/backlog/README.md` : elle est indicative, et
`/deliver-story` ne la lit que comme un ordre de préférence.

## 6. Rapport de fin

Termine par :

- **Les stories créées** : numéro, titre, priorité, estimation, dépendances.
- **Les décisions prises**, chacune avec son `D<n>` et sa ligne dans `DECISIONS.md`.
- **Ce qui reste bloqué** sur une action humaine, avec ce qui est attendu de
  l'utilisateur.
- **La commande de contrôle et sa sortie réelle** :

```bash
grep -c "Étant donné" docs/backlog/E0X-*.md
```

Ce nombre doit égaler le nombre de critères que tu viens d'écrire. S'il est plus
petit, un critère a perdu son scénario.

**Ne jamais rapporter un contrôle que tu n'as pas lancé.**

## La chaîne complète

`/cadrer-story` écrit la story · `/deliver-story` la livre · `review-story` relit
le diff · `/security-review` garde le domaine critique.
