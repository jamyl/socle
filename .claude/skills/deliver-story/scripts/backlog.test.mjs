// Banc de tests de la machine à états du backlog.
// `node --test .claude/skills/deliver-story/scripts/backlog.test.mjs`
//
// Chaque test écrit un ou deux backlogs jetables, lance le script et lit son
// code de sortie.

import { spawnSync } from 'node:child_process'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { after, test } from 'node:test'
import { fileURLToPath } from 'node:url'

const ICI = path.dirname(fileURLToPath(import.meta.url))
const RACINE = path.resolve(ICI, '../../../..')
const jetables = []
after(() => { for (const d of jetables) fs.rmSync(d, { recursive: true, force: true }) })

function story (id, statut, { deps = '', criteres = ['- [ ] **Un critère**'] } = {}) {
  return `## ${id} — Titre\n**Priorité** P0 · **Estimation** S · **Statut** ${statut}\n` +
    (deps ? `**Dépend de** : ${deps}\n` : '') + `\nCritères d'acceptation :\n${criteres.join('\n')}\n\n`
}

function backlog (...stories) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'socle-backlog-'))
  jetables.push(dir)
  fs.writeFileSync(path.join(dir, 'E01-x.md'), `# E01 — x\n\n${stories.join('')}`)
  fs.writeFileSync(path.join(dir, 'README.md'), story('US-999', 'n\'importe quoi'))
  return dir
}

function check (...args) {
  const r = spawnSync(process.execPath, [path.join(ICI, 'backlog.mjs'), 'check', ...args], { encoding: 'utf8' })
  return { code: r.status, out: r.stdout + r.stderr }
}

const FAIT = { criteres: ['- [x] **Un critère**'] }

test('un backlog cohérent passe, et le décompte se lit', () => {
  const dir = backlog(story('US-101', 'fait', FAIT), story('US-102', 'à faire', { deps: 'US-101' }),
    story('US-103', 'en cours'), story('US-104', 'bloqué (clé d\'API attendue du propriétaire)'))
  const r = check('--dossier', dir)
  assert.equal(r.code, 0, r.out)
  assert.match(r.out, /4 stories — à faire 1 · en cours 1 · fait 1 · bloqué 1/)
})

test('les epics réels des modules passent', { skip: !fs.existsSync(path.join(RACINE, 'modules')) && 'projet amorcé : plus de modules/' }, () => {
  const dir = backlog()
  for (const m of fs.readdirSync(path.join(RACINE, 'modules'))) {
    const d = path.join(RACINE, 'modules', m, 'docs/backlog')
    if (!fs.existsSync(d)) continue
    for (const f of fs.readdirSync(d).filter((x) => /^E\d+.*\.md$/.test(x))) fs.copyFileSync(path.join(d, f), path.join(dir, `E9-${m}-${f}`))
  }
  const r = check('--dossier', dir)
  assert.equal(r.code, 0, r.out)
  assert.doesNotMatch(r.out, / 0 stories/)
})

test('statut absent, inconnu, ou bloqué sans motif : refusé', () => {
  const dir = backlog(story('US-101', 'en revue'), story('US-102', 'bloqué'), story('US-103', 'bloqué ( )'),
    '## US-104 — Sans statut\n\n')
  const r = check('--dossier', dir)
  assert.equal(r.code, 1)
  assert.match(r.out, /US-101 : statut « en revue » inconnu/)
  assert.match(r.out, /US-102 : « bloqué » sans motif/)
  assert.match(r.out, /US-103 : « bloqué \( \) » sans motif/)
  assert.match(r.out, /US-104 : pas de \*\*Statut\*\*/)
})

test('dépendance absente, fait sur une dépendance pas faite, fait avec un critère ouvert, doublon : refusé', () => {
  const dir = backlog(story('US-101', 'à faire', { deps: 'US-404' }), story('US-102', 'fait', { ...FAIT, deps: 'US-101' }),
    story('US-103', 'à faire'), story('US-103', 'à faire'), story('US-104', 'fait'))
  const r = check('--dossier', dir)
  assert.equal(r.code, 1)
  assert.match(r.out, /US-101 dépend de US-404, qui n'existe pas/)
  assert.match(r.out, /US-102 est fait, mais sa dépendance US-101 est « à faire »/)
  assert.match(r.out, /US-104 est fait avec 1 critère\(s\) non coché\(s\)/)
  assert.match(r.out, /US-103 est défini deux fois/)
})

test('un fait ne revient pas en arrière et ne disparaît pas', () => {
  const avant = backlog(story('US-101', 'fait', FAIT), story('US-102', 'fait', FAIT))
  const apres = backlog(story('US-101', 'à faire'))
  const r = check('--dossier', apres, '--avant', avant, '--branche', 'docs-x')
  assert.equal(r.code, 1)
  assert.match(r.out, /US-101 était fait, il est maintenant « à faire »/)
  assert.match(r.out, /US-102 était fait, et a disparu/)
})

test('seule la story de la branche passe à fait, sous-stories et casse comprises', () => {
  const avant = backlog(story('US-101', 'à faire'), story('US-101a', 'à faire'), story('US-102', 'à faire'))
  const apres = backlog(story('US-101', 'fait', FAIT), story('US-101a', 'fait', FAIT), story('US-102', 'à faire'))
  assert.equal(check('--dossier', apres, '--avant', avant, '--branche', 'us-101-env').code, 0)
  assert.equal(check('--dossier', apres, '--avant', avant, '--branche', 'US-101-env').code, 0)
  let r = check('--dossier', apres, '--avant', avant, '--branche', 'us-102-autre')
  assert.equal(r.code, 1)
  assert.match(r.out, /US-101 passe à fait hors de sa propre PR \(branche de US-102\)/)
  r = check('--dossier', apres, '--avant', avant)
  assert.equal(r.code, 1)
  assert.match(r.out, /pas une branche de story/)
  const autre = backlog(story('US-1011', 'fait', FAIT))
  assert.equal(check('--dossier', autre, '--avant', backlog(story('US-1011', 'à faire')), '--branche', 'us-101-x').code, 1)
})

test('avec --avant, une story que la PR ne touche pas ne la fait pas rougir', () => {
  const ancienne = story('US-100', 'fait', { criteres: ['- [ ] reste en texte libre'] })
  const avant = backlog(ancienne)
  const apres = backlog(ancienne, story('US-101', 'à faire', { deps: 'US-100' }))
  assert.equal(check('--dossier', apres, '--avant', avant, '--branche', 'docs-cadrage').code, 0)
  assert.equal(check('--dossier', apres).code, 1)
  const cassee = backlog(ancienne, story('US-101', 'à faire', { deps: 'US-404' }))
  assert.equal(check('--dossier', cassee, '--avant', avant).code, 1)
})

test('usage : dossier introuvable, option inconnue', () => {
  assert.equal(check('--dossier', '/nulle/part').code, 2)
  assert.equal(check('--story', 'US-1').code, 2)
  assert.equal(spawnSync(process.execPath, [path.join(ICI, 'backlog.mjs')]).status, 2)
})
