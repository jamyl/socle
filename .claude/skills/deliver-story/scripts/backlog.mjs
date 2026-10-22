#!/usr/bin/env node
//
// socle — la machine à états du backlog, vérifiée par une machine.
//
// Les statuts vivent dans les fichiers d'epic (`docs/backlog/E*.md`). Ce script
// vérifie qu'ils restent cohérents, et en CI qu'une PR ne les fait passer que
// par les transitions permises. Il lit des dossiers, jamais git : la CI extrait
// la base et la tête, puis l'appelle dans sa version de la BASE
// (`.github/workflows/integrite.yml`, job `backlog`).
//
// Aucune dépendance : bibliothèque standard de Node uniquement.
//
//   backlog.mjs check [--dossier docs/backlog]
//   backlog.mjs check --dossier <tête> --avant <base> [--branche us-XXX-slug]
//
// Codes de sortie : 0 = cohérent · 1 = au moins une violation · 2 = usage.

import fs from 'node:fs'
import path from 'node:path'

const USAGE = 'usage : backlog.mjs check [--dossier <dir>] [--avant <dir>] [--branche <nom>]'

function sortir (code, message) {
  process[code ? 'stderr' : 'stdout'].write(message.endsWith('\n') ? message : message + '\n')
  process.exit(code)
}

// --- Lecture : une story = un titre `## US-XYZ — …` jusqu'au titre suivant.

function lire (dossier) {
  const stories = new Map()
  const doublons = []
  for (const f of fs.readdirSync(dossier).filter((x) => /^E\d+.*\.md$/.test(x)).sort()) {
    const blocs = fs.readFileSync(path.join(dossier, f), 'utf8').split(/^(?=## )/m)
    for (const bloc of blocs) {
      const id = /^## (US-[0-9A-Za-z]+)\b/.exec(bloc)?.[1]
      if (!id) continue
      const cle = id.toUpperCase()
      if (stories.has(cle)) doublons.push(`${id} est défini deux fois (${stories.get(cle).fichier}, ${f})`)
      stories.set(cle, {
        id,
        fichier: f,
        texte: bloc,
        statut: /\*\*Statut\*\*\s*:?\s*(.+)$/m.exec(bloc)?.[1].split(' · ')[0].trim() ?? null,
        deps: (/\*\*Dépend de\*\*\s*:?\s*(.+)$/m.exec(bloc)?.[1].match(/US-[0-9A-Za-z]+/g) ?? []).map((d) => d.toUpperCase()),
        ouverts: (bloc.match(/^\s*- \[ \]/gm) ?? []).length
      })
    }
  }
  return { stories, doublons }
}

// --- Les états permis, et ce que chacun exige.

function genre (statut) {
  if (statut === null) return null
  if (['à faire', 'en cours', 'fait'].includes(statut)) return statut
  return /^bloqué \(.*\S.*\)$/.test(statut) ? 'bloqué' : 'inconnu'
}

function structure (stories) {
  const erreurs = new Map()
  const noter = (cle, m) => erreurs.set(cle, [...(erreurs.get(cle) ?? []), m])
  for (const [cle, s] of stories) {
    const g = genre(s.statut)
    if (g === null) noter(cle, `${s.id} : pas de **Statut**`)
    else if (g === 'inconnu') {
      noter(cle, s.statut.startsWith('bloqué')
        ? `${s.id} : « ${s.statut} » sans motif entre parenthèses — qui doit faire quoi`
        : `${s.id} : statut « ${s.statut} » inconnu (à faire, en cours, fait, bloqué (motif))`)
    }
    for (const d of s.deps) {
      const dep = stories.get(d)
      if (!dep) noter(cle, `${s.id} dépend de ${d}, qui n'existe pas`)
      else if (g === 'fait' && dep.statut !== 'fait') noter(cle, `${s.id} est fait, mais sa dépendance ${dep.id} est « ${dep.statut} »`)
    }
    if (g === 'fait' && s.ouverts) noter(cle, `${s.id} est fait avec ${s.ouverts} critère(s) non coché(s)`)
  }
  return erreurs
}

// `us-101-x` livre US-101, ou une de ses sous-stories (US-101a) : même
// lecture de la branche que `.claude/hooks/etat-story.mjs`.
function storyDeBranche (branche) {
  const m = /^us-([a-z0-9]+)-/i.exec(branche ?? '')
  return m ? `US-${m[1].toUpperCase()}` : null
}

function transitions (avant, apres, branche) {
  const erreurs = []
  const story = storyDeBranche(branche)
  for (const [cle, s] of avant) {
    if (s.statut !== 'fait') continue
    const n = apres.get(cle)
    if (!n) erreurs.push(`${s.id} était fait, et a disparu du backlog`)
    else if (n.statut !== 'fait') erreurs.push(`${s.id} était fait, il est maintenant « ${n.statut} » : un fait ne revient pas en arrière, on écrit une nouvelle story`)
  }
  for (const [cle, s] of apres) {
    if (s.statut !== 'fait' || avant.get(cle)?.statut === 'fait') continue
    const sienne = story && (cle === story || new RegExp(`^${story}[A-Z]$`).test(cle))
    if (!sienne) erreurs.push(`${s.id} passe à fait hors de sa propre PR (${story ? `branche de ${story}` : 'pas une branche de story'})`)
  }
  return erreurs
}

// --- Point d'entrée

const argv = process.argv.slice(2)
if (argv[0] !== 'check') sortir(2, USAGE)
const opts = {}
for (let i = 1; i < argv.length; i += 2) {
  if (!['--dossier', '--avant', '--branche'].includes(argv[i]) || argv[i + 1] === undefined) sortir(2, USAGE)
  opts[argv[i].slice(2)] = argv[i + 1]
}
const dossier = opts.dossier ?? 'docs/backlog'
for (const d of [dossier, opts.avant].filter(Boolean)) {
  if (!fs.existsSync(d)) sortir(2, `✗ ${d} : dossier introuvable.`)
}

const { stories, doublons } = lire(dossier)
const parStory = structure(stories)
let erreurs = doublons
if (opts.avant) {
  // Une PR ne répond que des stories qu'elle touche : une ancienne story en
  // texte libre, que personne ne modifie, ne fait pas rougir la suivante.
  const avant = lire(opts.avant).stories
  for (const [cle, m] of parStory) if (stories.get(cle).texte !== avant.get(cle)?.texte) erreurs.push(...m)
  erreurs.push(...transitions(avant, stories, opts.branche))
} else {
  for (const m of parStory.values()) erreurs.push(...m)
}

if (erreurs.length) sortir(1, erreurs.map((e) => `✗ ${e}`).join('\n'))
const compte = (g) => [...stories.values()].filter((s) => genre(s.statut) === g).length
sortir(0, `Backlog : ${stories.size} stories — à faire ${compte('à faire')} · en cours ${compte('en cours')} · ` +
  `fait ${compte('fait')} · bloqué ${compte('bloqué')}. Rien d'incohérent.`)
