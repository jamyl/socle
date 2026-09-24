// socle — ce que les hooks lisent de l'état d'une story.
//
// Aucune source nouvelle : la branche courante (`us-XXX-<slug>`, voir
// `.claude/rules/git-operations.md`) et le dernier essai que `eval-run.mjs`
// a consigné dans `.socle/runs/<US-XXX>/`.

import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

export function git (cwd, args) {
  const r = spawnSync('git', ['-C', cwd, ...args], { encoding: 'utf8' })
  return r.status === 0 ? r.stdout.trim() : null
}

export function storyDeBranche (branche) {
  const m = /^us-([a-z0-9]+)-/i.exec(branche ?? '')
  return m ? `US-${m[1].toUpperCase()}` : null
}

export function dernierEssai (racine, story) {
  const dir = path.join(racine, '.socle/runs', story)
  if (!fs.existsSync(dir)) return null
  const f = fs.readdirSync(dir).filter((x) => /^attempt-\d+\.json$/.test(x)).sort().pop()
  return f ? JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')) : null
}

export function lireEntree () {
  const entree = JSON.parse(fs.readFileSync(0, 'utf8'))
  const cwd = entree.cwd ?? process.cwd()
  const racine = git(cwd, ['rev-parse', '--show-toplevel']) ?? cwd
  const branche = git(cwd, ['branch', '--show-current'])
  return { entree, cwd, racine, branche }
}

export function refuser (message) {
  process.stderr.write(message.endsWith('\n') ? message : message + '\n')
  process.exit(2)
}
