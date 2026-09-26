---
name: bootstrap-project
description: Transforme ce template « socle » en projet réel — interviewe l'utilisateur (nom, but, personas, contraintes, architecture), découvre la stack (mini-interview, `/dejavu` sur le mécanisme dur uniquement, `codesearch` sur les écosystèmes), active un module ou génère les agents de stack, remplit tous les placeholders, puis se supprime. À lancer UNE SEULE FOIS, dans la toute première session d'un repo créé depuis le template.
argument-hint: "<nom du projet, optionnel>"
---

# Amorcer un nouveau projet depuis le socle

Tu transformes ce template en **projet réel**. Une seule exécution, dans la
première session. À la fin, ce skill n'existe plus — c'est voulu : un projet
amorcé ne se ré-amorce pas.

**Tu ne connais pas la stack en entrant.** Le template n'en impose aucune : tu la
découvres en §2 et tu la fais valider en §3. Un module de stack s'active parce que
la découverte y aboutit, jamais parce qu'il est là.

## 0. Refuser si le repo est déjà amorcé

```bash
ls scripts/bootstrap.sh 2>/dev/null && grep -rl "{{PROJET}}" . --exclude-dir=.git | head -3
```

Si `scripts/bootstrap.sh` est absent ou qu'aucun placeholder `{{…}}` ne subsiste,
**arrête-toi** : le projet est déjà amorcé, relancer écraserait du travail réel.
Dis-le et propose `/deliver-story` à la place.

## 1. Interview

Utilise **AskUserQuestion**, par lots — jamais une question à la fois en prose.
L'outil accepte quatre questions par appel : respecte ce plafond, quitte à faire
deux appels. Propose des options fermées ; « Autre » est ajouté automatiquement.

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

**Lot 3a — contraintes** (un appel, quatre questions)

- **Données et régulation** : données personnelles · santé, finance ou paiement ·
  secteur régulé avec juridiction de stockage imposée · aucune donnée sensible.
  *Discrimine* la région d'hébergement, la piste d'audit, et les contraintes qui
  vivent en base — ce qui écarte d'emblée un stockage sans contrainte d'intégrité.
- **Préférence de stack existante** : imposée (laquelle) · interdits (lesquels) ·
  **aucune préférence**. *Discrimine* tout le reste : une stack imposée réduit §2 à
  vérifier les briques dans cet écosystème, sans la rediscuter.
- **Cible d'hébergement** : PaaS managé · VPS avec conteneurs · serverless ·
  on-prem imposé. *Discrimine* des familles entières — le serverless exclut les
  workers résidents, l'on-prem exclut la base managée.
- **Module `dejavu`** : embarquer la recherche d'antériorité dans le projet, oui
  ou non. **Ne le propose pas si le poste l'a déjà** en global —
  `ls ~/.claude/skills/dejavu/SKILL.md` — sinon deux skills porteraient le même
  nom. Dis-le à l'utilisateur plutôt que de choisir à sa place.

**Lot 3b — architecture** (un second appel, quatre questions)

- **Compétences de l'équipe** : le ou les deux langages maîtrisés **en
  production**, ou « aucune préférence ». *Discrimine* : c'est la liste des
  écosystèmes candidats de §2.3. Une stack que l'équipe ne sait pas déboguer en
  production est un mauvais choix quelles que soient ses qualités.
- **Échelle à douze mois** : moins de 1 000 utilisateurs · 1 000 à 100 000 ·
  au-delà, ou fort volume d'écriture. *Discrimine* monolithe contre scale-out, et
  le palier haut déclenche le gate « mécanisme dur » de §2.1.
- **Temps réel, hors-ligne, mobile** (choix multiple) : notifications temps réel ·
  hors-ligne d'abord avec synchronisation · application native · PWA · rien de
  tout ça. *Discrimine* les briques à vérifier ; la synchronisation hors-ligne est
  un mécanisme dur ; le natif appelle le module `mobile-flutter`.
- **Interface web** : aucune · écrans d'administration seulement · interface
  publique ou produit. *Discrimine* le module `frontend-web` : « aucune » ou
  « administration seulement » ne l'appellent pas.
- **Délai avant la première release** : quelques semaines · un trimestre · sans
  contrainte. *Discrimine* le poids des compétences existantes et le choix entre
  un framework « batteries incluses » et une stack composée.

> `stack-laravel` **n'est pas une question posée ici.** Il se déduit de la
> découverte en §2.4 et se confirme en §3. Même chose pour `mobile-flutter`, qui
> découle de la réponse « application native », et pour `frontend-web`, qui
> découle de « interface publique ou produit ».

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

## 2. Découverte d'architecture

Quatre étapes, dans cet ordre. Elles produisent la proposition de §3 ; elles ne
décident rien seules.

### 2.1 Le gate — nommer le ou les mécanismes durs

Depuis l'échelle, le temps réel et le hors-ligne, le cloisonnement multi-tenant
s'il y en a un, et les règles du lot 4 : écris **une clause par mécanisme dur**,
ou le mot **« aucun »**.

Un mécanisme est dur quand « la version naïve casse à l'échelle » : cohérence,
concurrence, cache, protocole, intégrité cryptographique, scale-out, scoring,
recherche, synchronisation hors-ligne. Il n'y en a pas pour du CRUD, un
back-office, du glue code entre deux SDK documentés.

⚠️ **Ce gate est le seul filtre.** `/dejavu` invoqué par son nom considère que
l'utilisateur a choisi et **saute son propre pre-flight** : il ne refusera pas à
ta place. Si tu ne filtres pas ici, tu paieras un run pour rien.

« aucun » **se consigne** dans `docs/engineering/prior-art.md` — « pas de matière
à recherche » est une décision documentée, pas un oubli.

### 2.2 S'il y a un mécanisme dur : proposer la recherche, chiffrer, attendre

D'abord localiser le skill et le contact :

```bash
ls ~/.claude/skills/dejavu/SKILL.md .claude/skills/dejavu/SKILL.md \
   modules/dejavu/.claude/skills/dejavu/SKILL.md 2>/dev/null || echo "ABSENT"
echo "DEJAVU_CONTACT=[${DEJAVU_CONTACT:-non défini}]"
```

- **Seul le chemin `modules/…` existe** (module choisi, pas encore copié — la copie
  a lieu en §4) : ne reporte pas la recherche après l'amorçage, sinon §3 se
  décide sans elle. **Lis ce `SKILL.md` et exécute ses phases** avec les scripts
  sous `modules/dejavu/.claude/skills/dejavu/scripts/`. Même résultat, autre chemin.
- **Absent des trois** → dis-le et **continue sans**. L'absence d'un outil ne
  bloque pas un bootstrap. Note dans `prior-art.md` que la recherche reste à faire.
- **`DEJAVU_CONTACT` non défini** → signale-le (les APIs le demandent), continue.

⚠️ **Propose le run et attends la confirmation.** Un run coûte une douzaine à une
vingtaine de lectures isolées plus du HTTP réel : ce n'est pas une décision à
prendre à la place de l'utilisateur. Dis quel mécanisme tu cherches et ce que ça
coûte, puis attends. **Refus** → consigne « recherche refusée le JJ/MM » dans
`prior-art.md` et continue : un refus consigné est un résultat, un refus oublié
est une recherche qu'on croira faite.

Lance-le sur **le mécanisme**, jamais sur le choix de framework. « Comment
garantir l'unicité d'une réservation sous concurrence » se cherche ; « Laravel ou
Django pour ce SaaS » ne se cherche pas — aucun article n'y répond, et c'est §2.3
qui traite cette question-là.

Consigne la conclusion dans `docs/engineering/prior-art.md` **avec ses
identifiants** (arXiv, DOI) — sans eux la recherche est à refaire à la session
suivante. Si la recherche ne trouve rien, **écris-le aussi** : « zéro antériorité
pertinente » est un résultat, pas un vide.

### 2.3 Vérifier les briques dans deux ou trois écosystèmes

Cette étape traite le choix d'écosystème, et elle n'utilise **que**
`codesearch.py` : pas de lectures isolées, pas de modèle dans la boucle, quelques
requêtes HTTP. C'est quasi gratuit — fais-la même quand §2.1 a répondu « aucun ».

**Écosystèmes candidats** : les langages maîtrisés par l'équipe, plus la
préférence imposée s'il y en a une, plus un défaut raisonnable pour la cible
d'hébergement. **Plafonne à trois.**

**Briques** : ce que le produit exige réellement — « row level security
multi-tenant », « synchronisation hors-ligne CRDT », « websocket pubsub », « file
de jobs durable », « recherche plein texte ». Une brique par besoin identifié aux
lots 3 et 4.

Une commande par couple (brique, écosystème), **six appels au maximum** :

```bash
<chemin>/scripts/codesearch.py --terms "<brique> <écosystème>" --sources github --limit 5
```

Lis le bloc `diagnostics` **d'abord** : un fournisseur tombé rend une réponse
vide qui ressemble à « rien n'existe ». Puis, pour chaque document, `date` (date
du dernier push) et `extra.archived`. **Maintenu** = poussé il y a moins de douze
mois **et** non archivé.

Rends un tableau brique × écosystème : `nom/du-dépôt (push AAAA-MM)` ou « aucune
implémentation maintenue ». Une case vide est un argument, pas un trou.

### 2.4 Dériver la proposition

- **La stack**, avec ses versions : langage, framework, base de données, cache et
  files d'attente, authentification, interface, environnement de développement,
  CI.
- **Une alternative**, et la phrase qui l'écarte — tirée des compétences, de
  l'hébergement, du délai ou d'une case vide du tableau §2.3.
- **Le mapping module** : PHP/Laravel ⇒ module **`stack-laravel`**. Toute autre
  stack ⇒ **« cœur + agents générés »** (§5 étape 5bis). Application native ⇒
  **`mobile-flutter`** en plus. Interface web publique ou produit ⇒
  **`frontend-web`** en plus, quelle que soit la stack.

## 3. Proposer l'architecture, et attendre

Présente en **moins d'une page** :

1. **Stack retenue** (versions) et **module** : `stack-laravel`, ou « cœur +
   agents générés », plus `mobile-flutter` et `frontend-web` le cas échéant. Si la stack était
   imposée au lot 3a, écris « imposée — non rediscutée ».
2. **L'alternative écartée** et la phrase qui l'écarte.
3. **Les briques vérifiées** : le tableau de §2.3.
4. **Le ou les mécanismes durs** et ce que la recherche en dit : le chemin retenu
   avec ses identifiants, ou « recherche refusée le JJ/MM », ou « aucun mécanisme
   dur — sans objet ». Dans les trois cas, une section existe dans `prior-art.md`.
5. **Modèle de domaine** — les 5 à 8 entités qui portent le sens, leurs relations,
   et **où vit l'invariant** de chaque règle du lot 4, nommé dans la stack
   retenue : « contrainte `CHECK` sur telle table », « transaction sérialisable
   dans tel service ».
6. **Les questions ouvertes** que tu ne peux pas trancher seul.

**Attends la validation explicite avant d'écrire quoi que ce soit.** Un bootstrap
part sur un malentendu ou ne part pas.

## 4. Exécution mécanique

Une fois validé :

```bash
./scripts/bootstrap.sh "<slug>" [stack-laravel] [mobile-flutter] [frontend-web] [dejavu]
```

Le script fait **uniquement du mécanique** : substitution des placeholders, copie
des modules choisis à la racine, mise en place des gabarits d'agents de stack
quand aucun module de stack n'est activé, puis suppression de `modules/`, de ce
skill, du `CHANGELOG.md` et de la CI du template, et de lui-même. Il ne rédige
rien — c'est ton travail.

Lis sa sortie. S'il refuse (argument manquant, module inconnu, repo déjà amorcé),
**corrige l'appel** ; ne contourne pas le script à la main.

## 5. Rédaction

Dans cet ordre, parce que chaque fichier s'appuie sur le précédent :

1. **`docs/product/vision.md`** — remplis chaque section du squelette avec
   l'interview. Les sections que tu ne peux pas remplir restent, marquées
   `À COMPLÉTER` : un trou visible vaut mieux qu'un trou comblé par de la prose.

2. **`docs/engineering/stack.md`** — deux cas.

   **Module `stack-laravel` activé** : le module en fournit une version remplie.
   **Ajoute** les règles du domaine à §3, ne réécris pas les règles techniques.

   **Sans module de stack** : retire le bandeau « 🔧 Squelette » en tête, puis
   remplis depuis §2.4 et le tableau de §2.3.
   - **§1** le tableau des technologies, versions comprises. « Observabilité »
     peut rester `À COMPLÉTER`.
   - **§2 « Pourquoi ces choix »** : un paragraphe par arbitrage non évident, avec
     l'alternative écartée et sa raison. Les sources sont les réponses des lots 3a
     et 3b, le tableau des briques, et un renvoi vers `prior-art.md`.
   - **§3** instancie les huit familles de règles avec les noms concrets de la
     stack : où vit la logique métier **dans ce framework** et où elle est
     interdite, comment un état se modélise avec le type énuméré du langage, quel
     outil porte les migrations. Puis **ajoute** les règles du domaine.
   - **§4 Gates CI** : N1 à N3 avec les outils nommés, et lesquels bloquent le merge.
   - **§5 Commandes** : les intentions avec les **commandes réelles** de la
     toolchain. Si le scaffold n'existe pas encore, écris
     `À COMPLÉTER (story de scaffold E01)` plutôt qu'une commande devinée — c'est
     `/deliver-story` qui les exécutera et citera leur sortie.

2bis. **`docs/engineering/testing-strategy.md`** — sans module de stack, retire le
   bandeau « 🔧 Version agnostique » et nomme les outils : N1 le formateur,
   l'analyseur statique et l'audit de dépendances ; N2 le runner et son dossier ;
   N3 le runner et le **moteur de base réel**. Garde N5 si le produit a plusieurs
   consommateurs. N7 et N8 : « module `mobile-flutter` », « module `frontend-web` »
   ou « sans objet ». Le
   reste du fichier est agnostique et ne bouge pas.

3. **`CLAUDE.md`** — la section « règles qui coûtent le plus cher à violer » avec
   les invariants du lot 4, et le tableau d'outillage réduit à ce qui est
   réellement installé. ⚠️ **Ce tableau est une liste blanche** : n'y mets rien
   que le projet n'a pas.
4. **`.claude/workflows/review-story.js`** — remplace `{{INVARIANTS}}` par les
   règles du lot 4, **une chaîne par règle** dans le tableau `regles`
   (une clause vérifiable chacune), comme les deux nœuds au-dessus. Contrôle :
   autant d'éléments dans `regles` que de règles dans `CLAUDE.md`.
5. **`.claude/agents/domain-expert.md`** — spécialise le squelette : le domaine,
   son vocabulaire, ses invariants, ses pièges de conformité.

5bis. **Les agents de stack**, seulement si aucun module de stack n'est activé.
   Le script a déplacé les gabarits de `.claude/templates/agent-stack-*.md` vers
   `.claude/agents/`. Spécialise-les comme `domain-expert` : `{{PROJET}}`,
   `{{STACK}}` (une ligne du genre « PHP 8.4 · Laravel 13 · PostgreSQL 16 ») et
   chaque bloc « À REMPLIR ».
   - **`developer.md`** : où vit la logique métier dans ce framework, comment un
     état se modélise, l'arborescence du code, et trois à cinq pièges de cette
     stack. Ne recopie pas `stack.md` §5 : l'agent le **lit**.
   - **`dba.md`** : à garder si la stack a une base relationnelle, à **supprimer**
     sinon (`rm .claude/agents/dba.md`). Un agent qui parle d'un moteur absent est
     pire qu'un agent manquant.

   Contrôle : `grep -n '{{\|À REMPLIR' .claude/agents/*.md` ne doit rien rendre.

5ter. **L'interface**, seulement si `frontend-web` est activé.
   - **`DESIGN.md`** : chaque section depuis la maquette, la référence ou
     l'interview. Une section sans règle vérifiable reste `À REMPLIR`.
   - **`design/tokens.json`** : les valeurs de `DESIGN.md`, puis
     `cd e2e && npm run tokens` pour régénérer `tokens.css`.
   - **`e2e/routes.json`** : `preparation`, `serveur` et `baseURL` si le scaffold
     existe ; sinon vides, et la story de scaffold les remplit. Tant que
     `serveur` est vide, la CI saute les gates UI.
   - **`stack.md` §5** : la commande « Lancer la suite de tests » **inclut**
     `(cd e2e && npm run gates)` — c'est ce qui fait compter les gates UI par
     `eval-run.mjs`.

6. **`docs/backlog/README.md`** — la roadmap et la liste des epics prévus.
7. **`docs/backlog/E01-fondations.md`** — l'epic qui rend le projet démarrable.
   Le module `stack-laravel` en livre un pré-écrit : **adapte-le** (nom du repo,
   slug, ports) plutôt que d'en écrire un nouveau. Sans module, il n'existe pas :
   écris-le, et vérifie que le lien de `docs/backlog/README.md` pointe dessus.
   La trame reste la même quelle que soit la stack : environnement local
   reproductible, dépôt et conventions, assets Claude Code, **scaffold applicatif
   et CI du projet** (la CI du template a été supprimée, celle du projet naît
   ici), secrets et environnements, garde-fou qui empêche la suite de tests
   d'atteindre la base de développement.
8. **`docs/backlog/JOURNAL.md`**, **`docs/backlog/DECISIONS.md`** et
   **`CONTRIBUTING.md`** — trois fichiers courts qui portent chacun un
   `{{PROJET}}` dans leur première ligne. Faciles à oublier parce qu'on ne les
   rouvre jamais ; le contrôle final les attrape.

**N'écris que E01.** Les epics suivants s'écrivent quand le produit est clair —
un backlog complet rédigé au bootstrap est un backlog à réécrire. Et ils ne
s'écrivent pas à la main : `/cadrer-story` est fait pour ça.

Les placeholders de rédaction que tu dois avoir consommés en sortant :
`{{PROJET}}`, `{{BUT}}`, `{{REGLES}}`, `{{INVARIANTS}}`, et `{{STACK}}` quand des
agents de stack ont été générés.

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

- **Ce qui est en place** : stack retenue, modules activés, agents générés,
  fichiers rédigés.
- **La conclusion d'antériorité**, avec ses identifiants — ou franchement
  « recherche non faite » / « refusée le JJ/MM », et pourquoi.
- **Ce qui est attendu de l'utilisateur** : les prérequis manquants, chacun avec
  sa commande.
- **Les stories déjà `bloqué`** et ce qui les débloque.
- **La commande suivante** : `/deliver-story`, ou `/loop 10m /deliver-story E01`
  pour enchaîner en autonomie. Et `/cadrer-story <requis>` pour écrire les epics
  suivants, quand le produit sera assez clair pour les mériter.

### Puis, toujours : « comment tu peux le vérifier toi-même »

Même exigence que `deliver-story`, et elle commence ici :

```bash
grep -rn '{{[A-Z_]\+}}' . --exclude-dir=.git
```

→ **aucune ligne**. Un placeholder qui survit est un endroit où le projet parle
encore du template.

Le motif est resserré sur la forme réelle d'un placeholder — deux accolades, des
majuscules, deux accolades — et non sur `{{` tout court. Un `grep -rn "{{"`
attrape aussi les accolades doublées d'un f-string Python dans les scripts du
module `dejavu`. Et n'écris jamais un exemple de placeholder en toutes lettres
dans un document du projet : il se ferait attraper par son propre contrôle. Un
contrôle qui crie au loup cesse d'être lu.

Donne aussi la commande qui prouve que l'environnement démarre : celle de
`docs/engineering/stack.md` §5, ligne « Démarrer l'environnement ». Si elle porte
encore `À COMPLÉTER`, dis-le franchement — la preuve arrivera avec la story de
scaffold, et promettre une commande qui n'existe pas est pire que reconnaître
qu'elle manque.
