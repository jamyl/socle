#!/usr/bin/env node
//
// socle — hook Stop, opt-in (`SOCLE_STOP_GATE=1`). Sur une branche de story,
// l'agent ne s'arrête pas avec un dernier essai rouge ou un diff non commité :
// le code 2 le renvoie au travail avec la raison.
//
// Une seule relance par arrêt : quand `stop_hook_active` est vrai, l'agent a
// déjà été renvoyé une fois et on le laisse s'arrêter. La borne dure reste le
// garde à deux strikes de `eval-run.mjs`, et l'humain.

import { dernierEssai, git, lireEntree, refuser, storyDeBranche } from './etat-story.mjs'

if (process.env.SOCLE_STOP_GATE !== '1') process.exit(0)

const { entree, cwd, racine, branche } = lireEntree()
const story = storyDeBranche(branche)
if (entree.stop_hook_active || !story) process.exit(0)

const essai = dernierEssai(racine, story)
if (essai && !essai.pass) {
  refuser(`⛔ ${story} non livrée : le dernier essai (n° ${essai.n}) est rouge.\n` +
    '   Continue, ou consigne l\'abandon (exploration-policy.md §1) avant de t\'arrêter.')
}
if (git(cwd, ['status', '--porcelain'])) {
  refuser(`⛔ ${story} : modifications non commitées. Commite, ou restaure et consigne l'abandon.`)
}
