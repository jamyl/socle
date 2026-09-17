#!/usr/bin/env node
//
// socle — enregistrement et notation des essais d'une story.
//
// Ce script ne décide rien à ta place : il exécute les commandes que
// `docs/engineering/stack.md` §5 déclare, note le résultat sur des dimensions
// binaires, et garde la trace de chaque essai dans `.socle/runs/<story>/`.
//
// Il existe parce que la mémoire d'une itération ne survit pas à la suivante :
// sans cache, une boucle d'agent réessaie la même fausse piste indéfiniment.
// La règle est dans `.claude/rules/exploration-policy.md`.
//
// Aucune dépendance : bibliothèque standard de Node uniquement.
//
//   eval-run.mjs attempt   <US-XXX> [--hypothesis "…"] [--abandon "…"]
//   eval-run.mjs preflight <US-XXX>
//   eval-run.mjs retro     <US-XXX>
//
// Codes de sortie de `attempt` : 0 = tout vert · 1 = au moins une dimension
// rouge · 2 = usage · 3 = REFUSÉ, l'hypothèse a déjà deux strikes.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'

const USAGE = `Usage :
  eval-run.mjs attempt   <US-XXX> [--hypothesis "H1 : …"] [--abandon "pourquoi c'était faux"]
  eval-run.mjs preflight <US-XXX>
  eval-run.mjs retro     <US-XXX>

Surcharges de commande (les tests du script, et un projet sans stack.md rempli) :
  --test-cmd <c>  --lint-cmd <c>  --secrets-cmd <c>
  --racine <dir>  racine du projet (défaut : le dépôt git courant)
`

// --- Lecture des arguments. Aucune dépendance, aucune magie : une option
// --- inconnue est une erreur d'usage, pas un argument positionnel.

function lireArgs (argv) {
  const opts = {}
  const positionnels = []
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a.startsWith('--')) {
      const cle = a.slice(2)
      const permises = ['hypothesis', 'abandon', 'test-cmd', 'lint-cmd', 'secrets-cmd', 'racine']
      if (!permises.includes(cle)) sortir(2, `✗ option inconnue : « ${a} »\n\n${USAGE}`)
      if (i + 1 >= argv.length) sortir(2, `✗ ${a} attend une valeur.\n\n${USAGE}`)
      opts[cle] = argv[++i]
    } else {
      positionnels.push(a)
    }
  }
  return { opts, positionnels }
}

function sortir (code, message) {
  process.stderr.write(message.endsWith('\n') ? message : message + '\n')
  process.exit(code)
}

// --- Le dépôt. Tout chemin est relatif à la racine du projet, jamais au
// --- répertoire courant : le script est appelé depuis n'importe où.

function trouverRacine (surcharge) {
  if (surcharge) return path.resolve(surcharge)
  const r = spawnSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8' })
  if (r.status !== 0) sortir(2, '✗ pas un dépôt git, et --racine absent.')
  return r.stdout.trim()
}

// --- Les commandes viennent de stack.md §5, jamais d'une devinette.
//
// Le tableau est du Markdown : `| Intention | Commande |`. On cherche la ligne
// dont la première cellule contient l'intention, insensible à la casse et aux
// accents décoratifs — le libellé du cœur est « Lancer la suite de tests »,
// celui du module Laravel « Suite de tests ». Les deux doivent marcher.
//
// 🔑 On ne lit QUE la section « Commandes ». Chercher dans tout le fichier
// paraissait plus tolérant et donnait une fausse commande : le tableau « Vue
// d'ensemble » du module Laravel porte une ligne `| Analyse statique |
// Larastan |`, qui matchait avant §5 — le scorer lançait alors `Larastan` et
// rapportait « command not found » comme une erreur d'analyse statique. Défaut
// réel, trouvé en lançant le scorer sur un projet amorcé.
//
// Une cellule vide ou « À COMPLÉTER » n'est PAS une commande : la dimension
// devient `skipped` avec son motif. Deviner ici serait pire que ne rien faire,
// parce que la sortie aurait l'air d'une mesure.

const A_COMPLETER = /à compléter|a completer|todo/i

function sectionCommandes (texte) {
  const lignes = texte.split('\n')
  const debut = lignes.findIndex((l) => /^#{2,4}\s.*commandes/i.test(l))
  if (debut === -1) return null
  const suite = lignes.slice(debut + 1)
  const fin = suite.findIndex((l) => /^#{1,4}\s/.test(l))
  return (fin === -1 ? suite : suite.slice(0, fin)).join('\n')
}

function commandeDepuisStack (texte, motif) {
  if (texte === null) {
    return { statut: 'skipped', motif: 'aucune section « Commandes » dans docs/engineering/stack.md' }
  }
  if (!texte) return { statut: 'skipped', motif: 'docs/engineering/stack.md absent' }
  for (const ligne of texte.split('\n')) {
    if (!ligne.trim().startsWith('|')) continue
    const cellules = ligne.split('|').slice(1, -1).map((c) => c.trim())
    if (cellules.length < 2) continue
    if (!motif.test(cellules[0])) continue
    const cmd = cellules[1].replace(/`/g, '').trim()
    if (!cmd) return { statut: 'skipped', motif: `stack.md §5 : « ${cellules[0]} » n'a pas de commande` }
    if (A_COMPLETER.test(cmd)) return { statut: 'skipped', motif: `stack.md §5 : « ${cellules[0]} » est encore à compléter` }
    return { statut: 'ok', cmd }
  }
  return { statut: 'skipped', motif: 'aucune ligne correspondante dans stack.md §5' }
}

function resoudreCommandes (racine, opts) {
  const chemin = path.join(racine, 'docs/engineering/stack.md')
  const brut = fs.existsSync(chemin) ? fs.readFileSync(chemin, 'utf8') : ''
  const texte = brut ? sectionCommandes(brut) : ''

  const tests = opts['test-cmd']
    ? { statut: 'ok', cmd: opts['test-cmd'] }
    : commandeDepuisStack(texte, /suite de tests|test suite/i)

  const lint = opts['lint-cmd']
    ? { statut: 'ok', cmd: opts['lint-cmd'] }
    : commandeDepuisStack(texte, /analyse statique|static analysis/i)

  let secrets
  if (opts['secrets-cmd']) {
    secrets = { statut: 'ok', cmd: opts['secrets-cmd'] }
  } else {
    const scanner = path.join(racine, '.github/scan-secrets.sh')
    secrets = fs.existsSync(scanner)
      ? { statut: 'ok', cmd: './.github/scan-secrets.sh' }
      : { statut: 'skipped', motif: '.github/scan-secrets.sh absent' }
  }

  return { tests, lint, secrets }
}

// --- Exécution. `shell: true` parce que les commandes de stack.md sont des
// --- lignes de shell complètes (`docker compose exec -T app …`), pas des argv.

const LIGNES_GARDEES = 40

function executer (racine, spec) {
  if (spec.statut !== 'ok') return { statut: 'skipped', motif: spec.motif, sortie: '' }
  const r = spawnSync(spec.cmd, { cwd: racine, shell: true, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 })
  const brut = `${r.stdout ?? ''}${r.stderr ?? ''}`
  const sortie = brut.split('\n').slice(0, LIGNES_GARDEES).join('\n')
  return { statut: r.status === 0 ? 'vert' : 'rouge', code: r.status, cmd: spec.cmd, sortie }
}

// --- Le score. Volontairement grossier et documenté : il ne sert qu'à répondre
// --- « est-ce que ça progresse ? », et une seule décision en dépend (continuer
// --- ou pivoter). Un score raffiné donnerait l'illusion d'une mesure.
//
//   secrets propres      50   — un secret commité coûte une révocation, rien ne passe avant
//   tests verts          40   — la condition du passage à `fait`
//   analyse statique     10 − nombre d'erreurs, plancher 0
//
// Une dimension `skipped` vaut 0 et rend `pass` faux : « pas mesuré » n'est pas
// « vert ». C'est ce qui empêche un projet sans commande déclarée de se croire
// couvert.

function compterErreursLint (dim) {
  if (dim.statut !== 'rouge') return 0
  const n = dim.sortie.split('\n').filter((l) => /error/i.test(l)).length
  return Math.max(1, n)
}

function noter (dims) {
  const erreursLint = compterErreursLint(dims.lint)
  // Trois états, trois valeurs — et `skipped` vaut 0, pas 10. Écrire
  // `statut === 'vert' ? 10 : 10 - erreurs` donnait le plein score à une
  // dimension JAMAIS EXÉCUTÉE, parce que `erreurs` y vaut zéro. Défaut réel,
  // attrapé par le test « stack.md absent ».
  const pointsLint =
    dims.lint.statut === 'vert' ? 10
      : dims.lint.statut === 'rouge' ? Math.max(0, 10 - erreursLint)
        : 0
  const score =
    (dims.secrets.statut === 'vert' ? 50 : 0) +
    (dims.tests.statut === 'vert' ? 40 : 0) +
    pointsLint
  const pass = dims.secrets.statut === 'vert' && dims.tests.statut === 'vert' && dims.lint.statut === 'vert'
  return { score, pass, erreursLint }
}

// --- La signature d'échec. Deux essais qui produisent la même signature n'ont
// --- rien déplacé : c'est la définition d'un strike.
//
// On normalise avant de hacher, sinon un numéro de ligne ou un chemin de
// répertoire temporaire suffirait à faire passer deux échecs identiques pour
// deux échecs différents — et le garde des deux strikes ne déclencherait jamais.

function signature (dims) {
  const rouges = ['tests', 'lint'].filter((n) => dims[n].statut === 'rouge')
  if (!rouges.length) return null

  let lignes = []
  for (const nom of rouges) {
    for (const l of dims[nom].sortie.split('\n')) {
      if (/error|fail|exception|assert|refus/i.test(l)) lignes.push(l)
    }
  }
  // 🔑 Repli sur la sortie brute. Tous les échecs ne disent pas « error » :
  // « service "app" is not running » et « cannot find symbol » n'ont aucun de
  // ces mots. Sans ce repli, ces échecs-là ne produisaient AUCUNE signature,
  // donc aucun strike — et le garde ne se déclenchait jamais sur eux. Défaut
  // trouvé en lançant le scorer sur un projet amorcé sans Docker démarré.
  if (!lignes.length) {
    lignes = rouges
      .flatMap((nom) => dims[nom].sortie.split('\n'))
      .filter((l) => l.trim())
      .slice(-5)
  }
  // Une commande rouge qui n'écrit rien du tout : la signature reste stable,
  // c'est son code de retour qui la porte.
  if (!lignes.length) lignes = rouges.map((nom) => `${nom} code ${dims[nom].code}`)
  const normalisees = lignes
    .slice(0, 5)
    .map((l) => l.toLowerCase().replace(/\/[^\s:]+\//g, '/').replace(/\d+/g, '#').replace(/\s+/g, ' ').trim())
  return {
    hash: createHash('sha256').update(normalisees.join('\n')).digest('hex').slice(0, 16),
    extrait: lignes[0].trim().slice(0, 120),
  }
}

// --- L'empreinte de l'arbre de travail. Deux essais à la même empreinte, c'est
// --- un essai relancé sans avoir rien changé — le cas le plus pur de boucle.

function empreinteDiff (racine) {
  const diff = spawnSync('git', ['diff', 'HEAD'], { cwd: racine, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
  // `-x .socle/` : sans lui, l'essai précédent — écrit dans `.socle/runs/` —
  // compte comme un fichier nouveau et change l'empreinte. Deux essais
  // rigoureusement identiques passaient alors pour deux essais différents, et
  // la détection de boucle ne déclenchait jamais. `.socle/` est dans le
  // .gitignore du template, mais l'empreinte ne doit pas en dépendre : un projet
  // qui adopte la méthode peut avoir oublié la ligne.
  const nouveaux = spawnSync('git', ['ls-files', '--others', '--exclude-standard', '-x', '.socle/'], { cwd: racine, encoding: 'utf8' })
  return createHash('sha256').update(`${diff.stdout ?? ''}\n${nouveaux.stdout ?? ''}`).digest('hex').slice(0, 16)
}

function head (racine) {
  const r = spawnSync('git', ['rev-parse', '--short', 'HEAD'], { cwd: racine, encoding: 'utf8' })
  return r.status === 0 ? r.stdout.trim() : '(sans commit)'
}

// --- Le cache.

function dossierStory (racine, story) {
  return path.join(racine, '.socle/runs', story)
}

function lireEssais (racine, story) {
  const dir = dossierStory(racine, story)
  if (!fs.existsSync(dir)) return []
  return fs.readdirSync(dir)
    .filter((f) => /^attempt-\d+\.json$/.test(f))
    .sort()
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')))
}

function valider (story) {
  if (!story) sortir(2, `✗ identifiant de story manquant.\n\n${USAGE}`)
  if (!/^US-[A-Za-z0-9]+$/.test(story)) sortir(2, `✗ story « ${story} » : attendu US-XYZ.`)
  return story
}

// --- attempt

function attempt (racine, story, opts) {
  const essais = lireEssais(racine, story)
  const hypothese = opts.hypothesis ?? '(non nommée)'

  // Le garde. Il tourne AVANT toute exécution : un troisième essai sur une
  // hypothèse à deux strikes ne mérite pas qu'on lance la suite de tests.
  // `--abandon` est la sortie prévue : elle consigne pourquoi et libère la
  // boucle, elle ne contourne pas le garde pour la même hypothèse.
  if (!opts.abandon) {
    const bloquant = essais.find((e) => e.hypothesis === hypothese && e.strikes >= 2 && !e.abandon)
    if (bloquant) {
      process.stdout.write(
        `⛔ « ${hypothese} » a ${bloquant.strikes} strikes (essai ${bloquant.n}) — rien n'a été exécuté.\n` +
        `   Rollback puis abandon écrit, et une hypothèse DIFFÉRENTE :\n` +
        `     git restore .\n` +
        `     eval-run.mjs attempt ${story} --hypothesis "${hypothese}" \\\n` +
        `       --abandon "pourquoi « ${hypothese} » était fausse"\n` +
        `   Règle : .claude/rules/exploration-policy.md §1\n`)
      process.exit(3)
    }
  }

  const specs = resoudreCommandes(racine, opts)
  const dims = {
    secrets: executer(racine, specs.secrets),
    tests: executer(racine, specs.tests),
    lint: executer(racine, specs.lint),
  }
  const { score, pass, erreursLint } = noter(dims)
  const sig = signature(dims)

  const diffHash = empreinteDiff(racine)
  const precedent = essais[essais.length - 1]

  // Strikes : essais consécutifs, en remontant, portant la même signature.
  // Un abandon remet le compteur à zéro — c'est le point de la règle.
  let strikes = sig ? 1 : 0
  if (sig) {
    for (let i = essais.length - 1; i >= 0; i--) {
      if (essais[i].abandon) break
      if (essais[i].signature?.hash !== sig.hash) break
      strikes++
    }
  }

  const identique = essais.find((e) => e.diffHash === diffHash)

  const n = essais.length + 1
  const enregistrement = {
    story,
    n,
    timestamp: new Date().toISOString(),
    head: head(racine),
    diffHash,
    hypothesis: hypothese,
    abandon: opts.abandon ?? null,
    dims: {
      secrets: { statut: dims.secrets.statut, cmd: dims.secrets.cmd ?? null, motif: dims.secrets.motif ?? null, code: dims.secrets.code ?? null },
      tests: { statut: dims.tests.statut, cmd: dims.tests.cmd ?? null, motif: dims.tests.motif ?? null, code: dims.tests.code ?? null },
      lint: { statut: dims.lint.statut, cmd: dims.lint.cmd ?? null, motif: dims.lint.motif ?? null, code: dims.lint.code ?? null, erreurs: erreursLint },
    },
    score,
    pass,
    signature: sig,
    strikes,
    identiqueA: identique ? identique.n : null,
  }

  const dir = dossierStory(racine, story)
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(
    path.join(dir, `attempt-${String(n).padStart(3, '0')}.json`),
    JSON.stringify(enregistrement, null, 2) + '\n')

  // Décision. Elle n'a que deux valeurs, et c'est voulu : « continuer » n'est
  // dû qu'à un progrès MESURÉ. Un score qui stagne n'est pas un progrès lent,
  // c'est le signal qu'on tourne en rond.
  let decision
  if (pass) decision = 'terminé'
  else if (strikes >= 2) decision = 'pivoter'
  else if (!precedent || score > precedent.score) decision = 'continuer'
  else decision = 'pivoter'

  process.stdout.write(
    `essai ${n} · ${story} · hypothèse : ${hypothese}\n` +
    `  secrets : ${etiquette(dims.secrets)}\n` +
    `  tests   : ${etiquette(dims.tests)}\n` +
    `  statique: ${etiquette(dims.lint)}${erreursLint ? ` (${erreursLint} erreur(s))` : ''}\n` +
    `  score   : ${score}/100${precedent ? ` (précédent : ${precedent.score})` : ''}` +
    `${pass ? ' — tout vert' : ''}\n` +
    (sig ? `  signature : ${sig.hash} · strikes : ${strikes}\n    ${sig.extrait}\n` : '') +
    (identique ? `  ⚠️ arbre de travail IDENTIQUE à l'essai ${identique.n} : rien n'a changé entre les deux.\n` : '') +
    `  → DÉCISION : ${decision}\n` +
    (decision === 'pivoter'
      ? `     git restore . puis --abandon "…" et une hypothèse différente (exploration-policy.md §1)\n`
      : ''))

  if (!pass) {
    for (const nom of ['secrets', 'tests', 'lint']) {
      if (dims[nom].statut === 'rouge') {
        process.stdout.write(`\n--- sortie réelle de « ${dims[nom].cmd} » ---\n${dims[nom].sortie}\n`)
      }
    }
  }

  process.exit(pass ? 0 : 1)
}

function etiquette (d) {
  if (d.statut === 'skipped') return `non mesuré (${d.motif})`
  return d.statut
}

// --- preflight

function preflight (racine, story) {
  const essais = lireEssais(racine, story)
  if (!essais.length) {
    process.stdout.write(`${story} : aucun essai consigné. Première tentative.\n`)
    return
  }

  process.stdout.write(`${story} — ${essais.length} essai(s) consigné(s).\n\n`)

  process.stdout.write('Hypothèses déjà tentées :\n')
  const parHypothese = new Map()
  for (const e of essais) {
    const cle = e.hypothesis
    const v = parHypothese.get(cle) ?? { essais: [], strikes: 0, abandon: null, pass: false }
    v.essais.push(e.n)
    v.strikes = Math.max(v.strikes, e.strikes ?? 0)
    if (e.abandon) v.abandon = e.abandon
    if (e.pass) v.pass = true
    parHypothese.set(cle, v)
  }
  for (const [h, v] of parHypothese) {
    const etat = v.pass ? 'a réussi' : v.abandon ? 'ABANDONNÉE' : v.strikes >= 2 ? 'BLOQUÉE (2 strikes)' : `${v.strikes} strike(s)`
    process.stdout.write(`  · ${h} — essais ${v.essais.join(', ')} — ${etat}\n`)
    if (v.abandon) process.stdout.write(`      pourquoi c'était faux : ${v.abandon}\n`)
  }

  const sigs = new Map()
  for (const e of essais) {
    if (!e.signature) continue
    const v = sigs.get(e.signature.hash) ?? { n: 0, extrait: e.signature.extrait }
    v.n++
    sigs.set(e.signature.hash, v)
  }
  if (sigs.size) {
    process.stdout.write('\nSignatures d\'échec déjà vues :\n')
    for (const [h, v] of sigs) process.stdout.write(`  · ${h} ×${v.n} — ${v.extrait}\n`)
  }

  process.stdout.write(
    '\n⚠️ Ne reproduis aucune syntaxe ni hypothèse marquée ABANDONNÉE ou BLOQUÉE.\n' +
    '   Cite cette sortie dans ton plan de correction (exploration-policy.md §2).\n')
}

// --- retro

function retro (racine, story) {
  const essais = lireEssais(racine, story)
  if (!essais.length) {
    process.stdout.write(`${story} : aucun essai consigné — rien à rétrospecter.\n`)
    return
  }

  const total = essais.length
  const reussis = essais.filter((e) => e.pass).length
  const ratio = reussis === 0 ? '∞' : (total / reussis).toFixed(1)
  const abandons = essais.filter((e) => e.abandon)

  const sigs = new Map()
  for (const e of essais) {
    if (!e.signature) continue
    const v = sigs.get(e.signature.hash) ?? { n: 0, extrait: e.signature.extrait }
    v.n++
    sigs.set(e.signature.hash, v)
  }
  const impasses = [...sigs.entries()].filter(([, v]) => v.n >= 2)

  process.stdout.write(
    `${story} — rétrospective\n` +
    `  essais           : ${total}\n` +
    `  réussis (pass)   : ${reussis}\n` +
    `  ratio essais/réussite : ${ratio}${reussis === 0 ? ' (aucun essai vert)' : ''}\n` +
    `  hypothèses abandonnées : ${abandons.length}\n` +
    `  impasses récurrentes   : ${impasses.length}\n`)

  if (abandons.length) {
    process.stdout.write('\nCe qui a été appris (tel que tu l\'as écrit) :\n')
    for (const e of abandons) process.stdout.write(`  · essai ${e.n} — ${e.abandon}\n`)
  }
  if (impasses.length) {
    process.stdout.write('\nSignatures rencontrées au moins deux fois :\n')
    for (const [h, v] of impasses) process.stdout.write(`  · ${h} ×${v.n} — ${v.extrait}\n`)
  }

  const dernierVert = [...essais].reverse().find((e) => e.pass)
  process.stdout.write(
    '\n--- à coller dans docs/backlog/JOURNAL.md (complète les <…>) ---\n' +
    `- [<date réelle via \`date\`>] ${story} <titre> — fait — tests : ` +
    `${dernierVert?.dims?.tests?.cmd ?? '<commande>'} → <sortie réelle> — ` +
    `essais : ${total}, ratio : ${ratio} — suivante : <US-YYY>\n`)

  if (abandons.length || impasses.length) {
    const ecartee = abandons.length
      ? `${abandons[abandons.length - 1].hypothesis} — ${abandons[abandons.length - 1].abandon}`
      : '<hypothèse écartée>'
    process.stdout.write(
      '\n--- une impasse a été rencontrée : ligne pour docs/backlog/DECISIONS.md ---\n' +
      `| D<n> | <date> | ${story} | <la question tranchée> | ` +
      `${dernierVert?.hypothesis ?? '<ce qui a marché>'} | ${ecartee} | <À COMPLÉTER> |\n` +
      '\nRelis-la avant de l\'écrire : le coût du revirement ne se déduit d\'aucun\n' +
      'fichier, et une décision sans ce coût n\'est pas relisible.\n')
  } else {
    process.stdout.write('\nAucune impasse : rien à écrire dans DECISIONS.md.\n')
  }
}

// --- Point d'entrée

const { opts, positionnels } = lireArgs(process.argv.slice(2))
const [sousCommande, storyArg] = positionnels
const racine = trouverRacine(opts.racine)

switch (sousCommande) {
  case 'attempt': attempt(racine, valider(storyArg), opts); break
  case 'preflight': preflight(racine, valider(storyArg)); break
  case 'retro': retro(racine, valider(storyArg)); break
  default: sortir(2, sousCommande ? `✗ sous-commande inconnue : « ${sousCommande} »\n\n${USAGE}` : USAGE)
}
