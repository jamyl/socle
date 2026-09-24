#!/usr/bin/env node
//
// socle — hook PreToolUse sur Bash. Trois règles de
// `.claude/rules/git-operations.md` tenues par un garde plutôt que par la
// mémoire de l'agent : une règle en prose se lit, puis s'oublie au 40e tour.
//
//   1. aucun push vers `main`, aucun push forcé ;
//   2. aucun `--no-verify` ;
//   3. aucun `gh pr merge` sur une branche `us-XXX-*` dont le dernier essai
//      consigné par `eval-run.mjs` n'est pas `pass`.
//
// Code 2 = refus : Claude Code annule la commande et montre stderr à l'agent.
//
// Ce n'est pas un contrôle de sécurité, pas plus que la liste `deny` : une
// commande écrite pour le contourner (script intermédiaire, refspec entre
// guillemets, `gh pr merge <n>` lancé depuis une autre branche) passe. Il
// rattrape l'agent qui oublie, pas celui qui triche — voir
// `docs/engineering/config-locale.md`.

import { dernierEssai, lireEntree, refuser, storyDeBranche } from './etat-story.mjs'

const { entree, racine, branche } = lireEntree()

// Les chaînes entre guillemets ne portent ni séparateur ni option : un message
// de commit qui contient « -n » ou « ; » ne doit rien déclencher.
const segments = (entree.tool_input?.command ?? '')
  .replace(/"(?:[^"\\]|\\.)*"|'[^']*'/g, 'Q')
  .split(/&&|\|\||[;|\n]/)
  .map((s) => s.trim().split(/\s+/).filter(Boolean))

const AVEC_VALEUR = new Set(['-o', '--push-option', '--repo', '--receive-pack', '--exec'])

function sousCommande (mots, nom) {
  const i = mots.indexOf('git')
  if (i < 0) return null
  let j = i + 1
  while (mots[j] === '-C' || mots[j] === '-c') j += 2
  return mots[j] === nom ? mots.slice(j + 1) : null
}

function verifierPush (args) {
  const positionnels = []
  for (let k = 0; k < args.length; k++) {
    const a = args[k]
    if (AVEC_VALEUR.has(a)) { k++; continue }
    if (a === '--force' || a.startsWith('--force-with-lease') || /^-[a-zA-Z]*f[a-zA-Z]*$/.test(a)) {
      refuser(`⛔ push forcé refusé (${a}). Règle : .claude/rules/git-operations.md « Interdits ».`)
    }
    if (a === '--all' || a === '--mirror') {
      refuser(`⛔ git push ${a} pousse aussi main. Pousse la branche de la story, puis une PR.`)
    }
    if (!a.startsWith('-')) positionnels.push(a)
  }
  const refs = positionnels.slice(1)
  for (const ref of refs.length ? refs : [branche ?? '']) {
    if (ref.startsWith('+')) refuser(`⛔ refspec forcée refusée (${ref}).`)
    const dest = ref.includes(':') ? ref.split(':').pop() : (ref === 'HEAD' ? branche : ref)
    if ((dest ?? '').replace(/^refs\/heads\//, '') === 'main') {
      refuser('⛔ push vers main refusé. Une story = une branche = une PR, CI verte, merge squash.\n' +
        '   Règle : .claude/rules/git-operations.md « Jamais de push direct sur main ».')
    }
  }
}

for (const mots of segments) {
  const push = sousCommande(mots, 'push')
  if (push) verifierPush(push)

  if (sousCommande(mots, 'commit')?.some((a) => /^-[a-zA-Z]*n[a-zA-Z]*$/.test(a)) || (mots.includes('git') && mots.includes('--no-verify'))) {
    refuser('⛔ --no-verify refusé : un hook qui gêne se discute, il ne se saute pas.\n' +
      '   Règle : .claude/rules/exploration-policy.md §3.')
  }

  const g = mots.indexOf('gh')
  if (g >= 0 && mots[g + 1] === 'pr' && mots[g + 2] === 'merge') {
    const story = storyDeBranche(branche)
    if (!story) continue
    const essai = dernierEssai(racine, story)
    if (!essai?.pass) {
      refuser(`⛔ merge refusé : ${essai ? `le dernier essai de ${story} (n° ${essai.n}) n'est pas vert` : `aucun essai consigné pour ${story}`}.\n` +
        `   Lance la preuve avant le merge :\n` +
        `     .claude/skills/deliver-story/scripts/eval-run.mjs attempt ${story} --hypothesis "…"`)
    }
  }
}
