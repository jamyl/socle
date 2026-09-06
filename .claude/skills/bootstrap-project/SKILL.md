---
name: bootstrap-project
description: Transforme ce template « socle » en projet réel — interviewe l'utilisateur (nom, but, personas, contraintes, modules), passe /dejavu sur l'architecture cible, remplit tous les placeholders, puis se supprime. À lancer UNE SEULE FOIS, dans la toute première session d'un repo créé depuis le template.
argument-hint: "<nom du projet, optionnel>"
---

# Amorcer un nouveau projet depuis le socle

Tu transformes ce template en **projet réel**. Une seule exécution, dans la
première session. À la fin, ce skill n'existe plus — c'est voulu : un projet
amorcé ne se ré-amorce pas.

## 0. Refuser si le repo est déjà amorcé

```bash
ls scripts/bootstrap.sh 2>/dev/null && grep -rl "{{PROJET}}" . --exclude-dir=.git | head -3
```

Si `scripts/bootstrap.sh` est absent ou qu'aucun placeholder `{{…}}` ne subsiste,
**arrête-toi** : le projet est déjà amorcé, relancer écraserait du travail réel.
Dis-le et propose `/deliver-story` à la place.

## 1. Interview

Utilise **AskUserQuestion**, par lots — jamais une question à la fois en prose.
Tu as besoin de tout ce qui suit ; ne devine rien d'important.

**Lot 1 — identité du projet**
- **Nom** (`{{PROJET}}`) : celui qui apparaîtra dans les titres. Si un argument a
  été passé au skill, propose-le en premier choix.
- **Slug** (`{{SLUG}}`) : kebab-case, sert au nom de conteneur, à la base de
  données et au dossier. Déduis-le du nom et fais valider.
- **But en une phrase** (`{{BUT}}`) : ce que le produit fait, pour qui. C'est la
  phrase qui ouvrira `CLAUDE.md` — elle doit tenir en une ligne.

**Lot 2 — produit**
- **Personas** : qui utilise le produit, et pour quoi (2 à 4).
- **Périmètre du premier jalon** : ce qui doit marcher pour dire « ça existe ».
- **Ce qui est explicitement hors périmètre** — aussi utile que le périmètre.

**Lot 3 — contraintes**
- **Contraintes réglementaires ou légales** (données personnelles, secteur
  régulé, juridiction) — s'il n'y en a pas, le dire explicitement.
- **Contraintes techniques imposées** (hébergeur, langue d'interface, offline,
  accessibilité, multi-tenant…).
- **Modules** : `stack-laravel` ? `mobile-flutter` ? Aucun (cœur seul) ?

**Lot 4 — les règles qui coûtent le plus cher à violer** (`{{REGLES}}`)

C'est **la question la plus importante du bootstrap**, et celle que l'utilisateur
n'a pas l'habitude qu'on lui pose. Demande 3 à 5 invariants du domaine : les
règles dont la violation coûte de l'argent, de la confiance ou une mise en
conformité — pas des préférences de style.

Propose des exemples **du domaine décrit**, pas des exemples génériques. Formule
chaque règle de façon **testable** : « aucun code hors de X n'écrit dans Y »,
« telle somme vaut exactement zéro », « telle table n'est jamais mise à jour, on
contre-passe ». Si l'utilisateur reste vague, **repose la question sur un cas
concret** de son domaine (« que se passe-t-il si un utilisateur annule après
paiement ? ») jusqu'à obtenir une clause vérifiable — pas de deviner.

Ces règles deviennent trois choses à la fois : la section « règles » de
`CLAUDE.md`, la liste d'invariants du nœud `domain-expert` de la revue en
fan-out, et le prompt de l'agent `domain-expert`. **Une règle molle ici produit
une revue molle pendant tout le projet.**

## 2. Antériorité — `/dejavu`

**Avant** de proposer une architecture, cherche si le problème dur est déjà
résolu et publié.

D'abord vérifier que l'outil est là :

```bash
ls ~/.claude/skills/dejavu/SKILL.md 2>/dev/null || echo "ABSENT"
echo "DEJAVU_CONTACT=[${DEJAVU_CONTACT:-non défini}]"
```

- **Absent** → dis-le, donne la commande (`npx github:jamyl/dejavu install`),
  et **continue sans** : l'absence d'un outil ne bloque pas un bootstrap. Note
  dans `prior-art.md` que la recherche reste à faire.
- **`DEJAVU_CONTACT` non défini** → signale-le (les APIs le demandent), continue.

Puis **juge s'il y a matière**. `/dejavu` a son propre pre-flight et te dira
ABORT s'il n'y a rien à chercher — respecte-le, ne force pas. Il y a matière si
l'architecture porte un mécanisme dont « la version naïve casse à l'échelle » :
cohérence, concurrence, cache, protocole, intégrité cryptographique, scale-out,
scoring, recherche. Il n'y en a pas pour du CRUD, un back-office, du glue code.

Lance-le sur **la question d'architecture**, pas sur le produit. « Comment
garantir l'unicité d'une réservation sous concurrence » se cherche ; « plateforme
de réservation pour salles de sport » ne se cherche pas.

Consigne la conclusion dans `docs/engineering/prior-art.md` **avec ses
identifiants** (arXiv, DOI) — sans eux la recherche est à refaire à la session
suivante. Si `/dejavu` conclut ABORT ou ne trouve rien, **écris-le aussi** :
« zéro antériorité pertinente » est un résultat, pas un vide.

## 3. Proposer l'architecture, et attendre

Présente en **moins d'une page** :

1. **Stack retenue** — versions incluses. Si le module `stack-laravel` est
   activé, elle est déjà fixée : dis-le, ne la rediscute pas.
2. **Modèle de domaine** — les 5 à 8 entités qui portent le sens, leurs
   relations, et **où vit l'invariant** de chaque règle du lot 4.
3. **Les mécanismes non triviaux** et ce que l'antériorité en dit.
4. **Les questions ouvertes** que tu ne peux pas trancher seul.

**Attends la validation explicite avant d'écrire quoi que ce soit.** Un bootstrap
part sur un malentendu ou ne part pas.

## 4. Exécution mécanique

Une fois validé :

```bash
./scripts/bootstrap.sh "<slug>" [stack-laravel] [mobile-flutter]
```

Le script fait **uniquement du mécanique** : substitution des placeholders, copie
des modules choisis à la racine, suppression de `modules/`, de ce skill et de
lui-même. Il ne rédige rien — c'est ton travail.

Lis sa sortie. S'il refuse (argument manquant, module inconnu, repo déjà amorcé),
**corrige l'appel** ; ne contourne pas le script à la main.

## 5. Rédaction

Dans cet ordre, parce que chaque fichier s'appuie sur le précédent :

1. **`docs/product/vision.md`** — remplis chaque section du squelette avec
   l'interview. Les sections que tu ne peux pas remplir restent, marquées
   `À COMPLÉTER` : un trou visible vaut mieux qu'un trou comblé par de la prose.
2. **`docs/engineering/stack.md`** — le tableau des technologies, puis les règles
   d'architecture. Le module `stack-laravel` en fournit une version remplie :
   **ajoute** les règles du domaine, ne réécris pas les règles techniques.
3. **`CLAUDE.md`** — la section « règles qui coûtent le plus cher à violer » avec
   les invariants du lot 4, et le tableau d'outillage réduit à ce qui est
   réellement installé. ⚠️ **Ce tableau est une liste blanche** : n'y mets rien
   que le projet n'a pas.
4. **`.claude/workflows/review-story.js`** — remplace `{{INVARIANTS}}` par les
   règles du lot 4, une par ligne, formulées comme des clauses vérifiables.
5. **`.claude/agents/domain-expert.md`** — spécialise le squelette : le domaine,
   son vocabulaire, ses invariants, ses pièges de conformité.
6. **`docs/backlog/README.md`** — la roadmap et la liste des epics prévus.
7. **`docs/backlog/E01-fondations.md`** — l'epic qui rend le projet démarrable.
   Le module `stack-laravel` en livre un pré-écrit : **adapte-le** (nom du repo,
   slug, ports) plutôt que d'en écrire un nouveau.

**N'écris que E01.** Les epics suivants s'écrivent quand le produit est clair —
un backlog complet rédigé au bootstrap est un backlog à réécrire.

## 6. Statuts honnêtes dès le départ

Toute story qui exige une action humaine — créer un compte, obtenir une clé,
installer Xcode, demander un avis juridique — part **`bloqué (motif précis)`**,
pas `à faire`. Sinon la première itération de `/deliver-story` la prend, découvre
le mur, et perd un tour.

## 7. Clôture

```bash
git add -A && git commit -m "bootstrap: <nom du projet>"
```

Puis termine par un rapport court :

- **Ce qui est en place** : modules activés, fichiers rédigés.
- **La conclusion d'antériorité**, avec ses identifiants — ou franchement
  « recherche non faite » et pourquoi.
- **Ce qui est attendu de l'utilisateur** : les prérequis manquants, chacun avec
  sa commande.
- **Les stories déjà `bloqué`** et ce qui les débloque.
- **La commande suivante** : `/deliver-story`, ou `/loop 10m /deliver-story E01`
  pour enchaîner en autonomie.

### Puis, toujours : « comment tu peux le vérifier toi-même »

Même exigence que `deliver-story`, et elle commence ici :

```bash
grep -rn "{{" . --exclude-dir=.git
```

→ **aucune ligne**. Un placeholder qui survit est un endroit où le projet parle
encore du template.

Donne aussi la commande qui prouve que l'environnement démarre (celle du module
activé), ce qu'il doit voir, et ce qui signalerait un problème.
