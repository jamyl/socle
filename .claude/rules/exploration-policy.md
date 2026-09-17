# Règles d'exploration — quand un test reste rouge

Référencé par plusieurs sous-agents. Fait autorité sur ce dépôt.

Ce fichier ne parle **pas** du cas nominal : un test rouge qui devient vert à la
première implémentation, c'est le TDD de `/deliver-story` §3, il n'y a rien de
plus à faire. Ce fichier parle du cas où **le rouge résiste** — et où la boucle
d'un agent, laissée à elle-même, patche le même bloc jusqu'à épuisement du
budget sans jamais changer d'idée.

## 1. Deux strikes, puis on change d'idée

Un **strike** = un essai dont la signature d'échec est **la même** que celle de
l'essai précédent sur la même story. Même erreur, même endroit : le micro-patch
n'a rien déplacé.

Au **deuxième strike**, trois gestes, dans cet ordre :

```bash
git restore .                                    # ou : git checkout -- <fichiers>
${CLAUDE_SKILL_DIR}/scripts/eval-run.mjs attempt US-XXX \
  --hypothesis "H1 : <celle qu'on abandonne, au mot près>" \
  --abandon "H1 supposait que <…> ; l'erreur montre que <…>"
```

L'hypothèse est **renommée à l'identique** dans l'abandon : c'est ce qui relie la
leçon à la piste, dans le pré-vol comme dans la rétrospective.

puis **une autre hypothèse** — pas une variante de la même. Changer un nom, un
ordre d'arguments ou une valeur de temporisation n'est pas une autre hypothèse :
c'est le troisième micro-patch sous un autre nom.

> ⚠️ **Ce n'est pas une consigne, c'est un garde.** Un troisième essai sur une
> hypothèse déjà à deux strikes est **refusé** par le scorer, qui sort en code 3
> sans rien exécuter. Le rollback et l'abandon écrit sont la seule façon de
> repartir.

Le rollback est **propre et complet** : on ne garde pas « la moitié qui avait
l'air d'aider ». Ce qui a l'air d'aider sans faire passer le test est exactement
ce qui rendra le prochain diagnostic illisible.

**Ce que coûte le fait de s'en passer** : un `/loop` sans surveillance peut
enchaîner quinze essais sur la même fausse piste. La règle plafonne à deux, puis
force un changement de direction.

## 2. Pré-vol : lire les échecs avant d'écrire

Avant d'écrire la moindre ligne pour corriger un rouge :

```bash
${CLAUDE_SKILL_DIR}/scripts/eval-run.mjs preflight US-XXX
```

Il imprime, pour cette story, les hypothèses déjà tentées avec leurs strikes, les
raisons d'abandon telles qu'elles ont été écrites, et les signatures d'échec déjà
rencontrées.

**Ne jamais reproduire une syntaxe, un motif ou une hypothèse que le pré-vol
montre déjà invalidés.** Le cache existe précisément parce que la mémoire d'une
itération ne survit pas à la suivante : tout l'état vit dans les fichiers.

Ce que le pré-vol imprime **se cite** dans le plan de correction : « le pré-vol
montre que H1 a échoué sur <signature>, j'attaque donc par <autre angle> ». Un
plan qui ne cite rien n'a pas lu le cache.

## 3. Intégrité du processus

Un test ne se contourne pas. Interdits, sans exception :

- **Désactiver ou sauter** : `--skip`, `--no-verify`, `--exclude`, `.skip()`,
  `.only()` laissé en place, `xit`, `@group` d'exclusion, un marqueur d'ignore
  posé sur le test qui gêne.
- **Modifier un test existant pour le faire passer**, sauf si la story demande
  explicitement ce changement de comportement — et alors c'est un critère
  d'acceptation, pas un ajustement au passage.
- **Supprimer un test.** Un test devenu faux se journalise et fait l'objet d'une
  décision dans `docs/backlog/DECISIONS.md` ; il ne disparaît pas d'un commit.
- **Asserter sur une valeur mockée** produite par le code sous test, ou comparer
  la sortie d'un générateur à sa propre entrée : le test reste vert et ne prouve
  rien. Les huit motifs de fausse vérification sont dans
  `.claude/skills/deliver-story/SKILL.md` §4.
- **Baisser un seuil** d'analyse statique, ajouter une ligne de *baseline*, ou
  élargir une exclusion de *linter* pour verdir un gate.

Un gate qui gêne se **discute** — en PR, sur le fichier qui le déclare
(`docs/engineering/stack.md` §4, `testing-strategy.md`). Il ne se désarme jamais
dans le commit qui en avait besoin.

## 4. Ce que la boucle écrit

Chaque essai laisse un fichier dans `.socle/runs/<US-XXX>/attempt-<n>.json` :
horodatage, `HEAD`, empreinte du diff, hypothèse, dimensions mesurées, score,
signature d'échec, strikes. Ce dossier est **local** — il est dans le
`.gitignore` : c'est le chemin d'une story, pas son résultat. Le résultat vit
dans la PR et dans `JOURNAL.md`.

À la clôture, `eval-run.mjs retro US-XXX` en tire le ratio essais/réussites et
les impasses rencontrées. Un ratio élevé n'est pas une faute : c'est le signal
qu'une leçon mérite d'être écrite dans `DECISIONS.md` pendant qu'on s'en
souvient encore.
