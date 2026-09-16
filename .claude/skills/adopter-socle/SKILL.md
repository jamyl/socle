---
name: adopter-socle
description: Installe la méthode socle dans un projet qui a DÉJÀ du code — déduit la stack en lisant le dépôt au lieu de l'interviewer, n'interroge que sur le produit et les règles du domaine, rapproche un CLAUDE.md existant, écrit le backlog à partir de ce qui reste à faire, puis se supprime. À lancer UNE SEULE FOIS, après scripts/adopt.sh.
argument-hint: "<rien — tout se déduit du dépôt>"
---

# Adopter la méthode dans un projet existant

`scripts/adopt.sh` a copié les fichiers. Toi, tu les rends vrais.

La différence avec `/bootstrap-project` tient en une phrase : **la stack ne se
demande pas, elle se lit.** Le code est là, il fait autorité, et une interview
qui redemanderait le framework produirait une documentation qui contredit le
dépôt dès la première session.

Une seule exécution. À la fin, ce skill n'existe plus.

## 0. Refuser si ce n'est pas le bon cas

```bash
ls .claude/skills/deliver-story/SKILL.md scripts/adopt.sh 2>/dev/null
ls modules 2>/dev/null && echo "MODULES PRÉSENTS"
git log --oneline | wc -l
```

- **`modules/` présent** → ce dépôt vient du template, pas d'un projet existant.
  Arrête-toi : c'est `/bootstrap-project` qu'il faut.
- **Un seul commit, aucun code applicatif** → même chose, ce projet n'a rien à
  déduire.
- **Aucun placeholder `{{…}}` restant** → déjà adopté. Propose `/deliver-story`.

## 1. Lire le dépôt avant de parler

Ne pose aucune question tant que tu n'as pas fait ça. Une question dont la
réponse est dans le dépôt fait perdre du crédit à toutes les suivantes.

**Les manifestes** — c'est eux qui nomment la stack et les commandes :

```bash
ls package.json composer.json pyproject.toml requirements.txt Gemfile go.mod \
   Cargo.toml pubspec.yaml Makefile justfile docker-compose.yml 2>/dev/null
```

Pour chacun de ceux qui existent, lis-le en entier. Tu cherches :

- **Le langage et sa version**, le framework et **sa version exacte** — celle du
  verrou (`composer.lock`, `package-lock.json`, `poetry.lock`), pas celle de la
  contrainte. `^13.0` ne dit pas ce qui est installé.
- **Les commandes réelles** : la section `scripts`, les cibles du `Makefile`, les
  binaires de `vendor/bin` ou `node_modules/.bin`. Ce sont elles qui iront dans
  `stack.md` §5, telles quelles.
- **Le moteur de base de données et le cache**, depuis `docker-compose.yml` ou la
  configuration.
- **Le formateur, l'analyseur statique, le runner de tests**, et leur niveau de
  sévérité s'il est configuré.

**La CI existante** — elle dit ce qui bloque déjà un merge :

```bash
ls -R .github/workflows .gitlab-ci.yml .circleci 2>/dev/null
```

**La forme du code** — pour l'agent `developer` et pour `stack.md` §3 :

```bash
git ls-files | sed 's|/[^/]*$||' | sort -u | head -40
git ls-files | wc -l
```

**L'état de santé** — et c'est le point dur :

```bash
git log --oneline -15
git ls-files | grep -icE '(test|spec)' || true
```

⚠️ **Lance la suite de tests avant d'écrire quoi que ce soit**, avec la commande
que tu viens de trouver. Rapporte sa **sortie réelle**.

- **Verte** → tu as une base. Note le nombre de tests.
- **Rouge** → ne l'écris pas comme verte, et n'essaie pas de la réparer
  maintenant. C'est la **première story** du backlog que tu vas écrire.
- **Inexistante** → dis-le franchement. C'est aussi une story, et c'est la plus
  importante : la méthode entière repose sur « on l'a vu échouer », qui n'a aucun
  sens sans suite de tests.

## 2. Interviewer seulement ce que le code ne dit pas

Par lots, avec **AskUserQuestion**, quatre questions maximum par appel.

**Lot 1 — ce que le dépôt ne porte pas**
- **Nom du projet** (`{{PROJET}}`) : propose celui du dépôt ou du manifeste.
- **But en une phrase** (`{{BUT}}`) : le code dit *comment*, jamais *pour qui*.
- **Personas** : 2 à 4.
- **Périmètre du jalon en cours** : ce qui doit marcher pour la prochaine étape,
  pas pour la version 1 qui est peut-être déjà passée.

**Lot 2 — les règles qui coûtent le plus cher à violer** (`{{REGLES}}`)

Même exigence que `/bootstrap-project`, mais tu as un avantage : **tu as lu le
code**. Propose 3 à 5 invariants **déduits de ce que tu as vu** — une contrainte
en base, un état modélisé par un type énuméré, un service qui semble être le seul
à écrire quelque part — et demande confirmation ou correction.

Formule chaque règle de façon testable. Si l'utilisateur reste vague, repose la
question sur un cas concret **de son propre code** : « que se passe-t-il
aujourd'hui si deux requêtes arrivent en même temps sur telle route ? »

Ces règles deviennent la section « règles » de `CLAUDE.md`, la liste du nœud
`domain-expert` de la revue, et le prompt de cet agent. **Une règle molle ici
produit une revue molle pendant tout le projet.**

**Lot 3 — la dette qu'on assume**

Ce lot n'existe pas dans un bootstrap, et c'est le plus utile ici. Montre ce que
tu as trouvé — suite rouge, absence de tests, absence de CI, absence d'analyse
statique, secrets en clair — et demande, pour chaque point : **story maintenant,
ou dette assumée et écrite ?**

Une dette assumée qui est écrite quelque part n'est pas un problème. Une dette
que la documentation passe sous silence en devient un dans trois mois, quand
quelqu'un croira que la suite est verte.

## 3. Proposer, et attendre

En moins d'une page :

1. **La stack observée**, versions comprises, et **d'où tu la tiens** (quel
   fichier, quelle ligne). Si un verrou contredit une contrainte, dis-le.
2. **Les commandes trouvées**, telles qu'elles iront dans `stack.md` §5.
3. **L'état de santé** : sortie réelle de la suite de tests, gates de la CI
   existante.
4. **Les règles du lot 2** et, pour chacune, **où elle vit déjà dans le code** ou
   le fait qu'elle ne soit tenue par rien.
5. **Ce que tu proposes d'écrire** : les fichiers, et pour `CLAUDE.md` le plan de
   fusion (voir §5).
6. **Le backlog de départ** : les stories de dette retenues au lot 3.

**Attends la validation explicite avant d'écrire quoi que ce soit.**

## 4. Le mécanisme dur, si le projet en a un

Même règle que `/bootstrap-project` §2 : s'il y a un mécanisme dont « la version
naïve casse à l'échelle » — concurrence, cohérence, cache, protocole, intégrité
cryptographique, scale-out, recherche — **nomme-le**, propose `/dejavu` dessus en
annonçant son coût, et **attends**.

Sur un projet existant la question se pose différemment, et la formulation compte :
ce n'est plus « comment le construire » mais **« ce qui est déjà construit
tient-il ? »**. Une recherche qui confirme l'approche en place est un résultat ;
une recherche qui la contredit est une story, pas une réécriture immédiate.

Refus ou absence de matière : consigne-le daté dans
`docs/engineering/prior-art.md`. `/dejavu` appelé par son nom saute son propre
pre-flight — le filtre, c'est toi.

## 5. Rédiger

Dans cet ordre.

1. **`docs/engineering/stack.md`** — retire le bandeau « 🔧 Squelette ». §1 le
   tableau de ce que tu as **observé**, versions des verrous. §2 « Pourquoi ces
   choix » : ici tu ne justifies pas, tu **constates** — dis-le, et note les
   arbitrages que le dépôt révèle. §3 les huit familles de règles instanciées
   avec les noms de cette stack, plus les règles du domaine. §4 les gates de la
   CI **existante**, et ce qui manque. §5 les commandes trouvées, **jamais
   devinées** : une commande absente du dépôt s'écrit
   `À COMPLÉTER (story de dette)`.

2. **`docs/engineering/testing-strategy.md`** — retire le bandeau. Nomme les
   outils réels en N1 à N3. Les niveaux que le projet n'a pas ne se suppriment
   pas : ils restent, et **le fait qu'ils manquent devient une story**. C'est
   toute la valeur du document pour un projet en cours.

3. **`CLAUDE.md`** — deux cas.

   **Absent** → écris-le depuis le squelette.

   **Présent** (le script a déposé `CLAUDE.socle.md` à côté) → **ne l'écrase
   pas.** Le tien porte du contexte que le socle ignore. Procède section par
   section, et présente le plan avant d'éditer :
   - Les « Sources de vérité » et le tableau d'outillage du socle **s'ajoutent**.
     Le tableau est une **liste blanche** : n'y laisse que ce que le projet a
     réellement installé — vérifie chaque MCP contre un `.mcp.json` réel.
   - La section « règles qui coûtent le plus cher à violer » **s'insère** avec les
     règles du lot 2.
   - La section « Méthode » **remplace** toute description de workflow que ton
     `CLAUDE.md` portait, sinon deux méthodes contradictoires cohabitent.
   - Tout le reste de ton `CLAUDE.md` **reste**.

   Puis `rm CLAUDE.socle.md`. Même traitement pour `CONTRIBUTING.socle.md` s'il
   existe.

4. **`.claude/workflows/review-story.js`** — remplace `{{INVARIANTS}}` par les
   règles du lot 2, une clause vérifiable par ligne.

5. **`.claude/agents/domain-expert.md`** — spécialise le squelette avec le
   domaine réel.

6. **Les agents de stack** — `.claude/agents/developer.md` et `dba.md` si le
   script les a installés. Tu es mieux placé que le bootstrap pour les remplir :
   tu as lu le code. Les pièges que tu y écris sont ceux **observés dans ce
   dépôt**, pas ceux du framework en général. Supprime `dba.md` s'il n'y a pas de
   base relationnelle.

   Si `adopt.sh --stack` a repris les agents d'un module, ils sont déjà écrits :
   n'y touche pas, mais **vérifie qu'ils décrivent bien ce dépôt** et signale
   tout écart.

7. **`docs/product/vision.md`** — depuis le lot 1. Les sections que tu ne peux
   pas remplir restent marquées `À COMPLÉTER`.

8. **`docs/backlog/README.md`** et **`docs/backlog/E01-<slug>.md`** — et c'est ici
   que l'adoption diffère le plus d'un bootstrap. **E01 n'est pas « fondations »**
   : les fondations existent. C'est l'epic de ce qui manque pour que la méthode
   puisse tourner, dans cet ordre :
   - la suite de tests si elle est rouge ou absente ;
   - la CI si elle n'existe pas, ou les gates qui lui manquent ;
   - le garde-fou qui empêche la suite d'atteindre la base de développement ;
   - chaque dette retenue au lot 3.

   Puis l'epic suivant, s'il est clair, avec le jalon en cours du lot 1. Écris les
   stories au gabarit `docs/backlog/README.md`, statut `à faire`, et
   **`bloqué (motif)`** pour tout ce qui attend une action humaine.

9. **`docs/backlog/JOURNAL.md`** et **`docs/backlog/DECISIONS.md`** — leur
   `{{PROJET}}`. Le journal commence vide : les livraisons passées ne s'y
   réécrivent pas, `git log` les porte déjà.

**Ne réécris aucune spécification du code existant.** Le backlog part de
maintenant. Documenter rétroactivement ce qui est livré coûte cher et ne prouve
rien de plus.

## 6. Clôture

```bash
rm -rf .claude/skills/adopter-socle
git add -A && git commit -m "chore: adopter la méthode socle"
```

Ce skill se supprime : une adoption ne se rejoue pas. `scripts/adopt.sh` n'est
pas concerné — il vit dans la copie du template, jamais dans ton dépôt, et tu
peux jeter cette copie.

Puis un rapport court :

- **La stack observée**, avec le fichier d'où elle vient.
- **La sortie réelle de la suite de tests**, et son verdict.
- **Ce qui a été fusionné** dans `CLAUDE.md`, et ce qui a été laissé tel quel.
- **Ce que `adopt.sh` avait sauté** et que tu as rapproché — ou pas.
- **Les stories de E01**, avec les `bloqué` et ce qui les débloque.
- **Ce qui est attendu de l'utilisateur** : `.claude/settings.json` à relire
  (voir `docs/engineering/config-locale.md`), prérequis manquants.
- **La commande suivante** : `/deliver-story`.

### Puis, toujours : « comment tu peux le vérifier toi-même »

```bash
grep -rn '{{[A-Z_]\+}}' . --exclude-dir=.git
ls CLAUDE.socle.md CONTRIBUTING.socle.md .claude/skills/adopter-socle 2>&1
```

→ la première ne rend **aucune ligne** ; la seconde ne rend que des
« No such file or directory ». Un placeholder ou un `.socle.md` qui survit est
une fusion inachevée.

Donne aussi la commande de test du projet avec sa sortie attendue, et ce qui
signalerait un problème. Si la suite est rouge et que c'est assumé, **dis le
nombre d'échecs attendu** : une suite rouge dont on ne connaît pas le compte
exact ne permet plus de détecter une régression.
