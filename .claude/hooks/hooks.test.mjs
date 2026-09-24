// Banc de tests des hooks. `node --test .claude/hooks/hooks.test.mjs`
//
// Chaque test monte un dépôt git jetable sur la branche voulue, envoie au hook
// l'entrée JSON que Claude Code lui enverrait, et lit son code de sortie.

import { spawnSync } from 'node:child_process'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { after, test } from 'node:test'
import { fileURLToPath } from 'node:url'

const ICI = path.dirname(fileURLToPath(import.meta.url))
const jetables = []
after(() => { for (const d of jetables) fs.rmSync(d, { recursive: true, force: true }) })

function depot (branche = 'main') {
  const dir = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'socle-hook-'))
  jetables.push(dir)
  fs.writeFileSync(path.join(dir, '.gitignore'), '.socle/\n')
  for (const argv of [['init', '-q', '-b', 'main'], ['add', '-A'],
    ['-c', 'user.email=t@t.invalid', '-c', 'user.name=T', 'commit', '-qm', 'base'],
    ['checkout', '-q', '-B', branche]]) {
    const r = spawnSync('git', argv, { cwd: dir, encoding: 'utf8' })
    assert.equal(r.status, 0, `git ${argv.join(' ')} : ${r.stderr}`)
  }
  return dir
}

function essai (dir, story, n, pass) {
  const d = path.join(dir, '.socle/runs', story)
  fs.mkdirSync(d, { recursive: true })
  fs.writeFileSync(path.join(d, `attempt-${String(n).padStart(3, '0')}.json`), JSON.stringify({ n, pass }))
}

function hook (nom, dir, entree, env = {}) {
  const r = spawnSync(process.execPath, [path.join(ICI, nom)], {
    input: JSON.stringify({ cwd: dir, ...entree }),
    encoding: 'utf8',
    env: { ...process.env, SOCLE_STOP_GATE: '', ...env }
  })
  return { code: r.status, err: r.stderr }
}

const bash = (dir, command) => hook('guard-bash.mjs', dir, { tool_input: { command } })

// --- guard-bash : push

test('push vers main refusé sous ses formes courantes', () => {
  const dir = depot('us-101-x')
  for (const c of ['git push origin main', 'git push origin HEAD:main', 'git push -u origin main',
    'git push origin refs/heads/main', 'git status && git push origin main', 'git -C . push origin main']) {
    assert.equal(bash(dir, c).code, 2, c)
  }
})

test('push nu ou vers HEAD refusé depuis main, accepté depuis une branche', () => {
  const surMain = depot('main')
  assert.equal(bash(surMain, 'git push').code, 2)
  assert.equal(bash(surMain, 'git push origin HEAD').code, 2)
  const surBranche = depot('us-101-x')
  assert.equal(bash(surBranche, 'git push').code, 0)
  assert.equal(bash(surBranche, 'git push -u origin us-101-x').code, 0)
})

test('push forcé refusé', () => {
  const dir = depot('us-101-x')
  for (const c of ['git push --force origin us-101-x', 'git push -f', 'git push -uf origin x',
    'git push --force-with-lease', 'git push origin +us-101-x', 'git push --all']) {
    assert.equal(bash(dir, c).code, 2, c)
  }
})

// --- guard-bash : --no-verify

test('--no-verify et commit -n refusés, pas un -n dans un message', () => {
  const dir = depot('us-101-x')
  assert.equal(bash(dir, 'git commit --no-verify -m x').code, 2)
  assert.equal(bash(dir, 'git commit -n -m x').code, 2)
  assert.equal(bash(dir, 'git commit -m "fix: -n ; git push origin main"').code, 0)
  assert.equal(bash(dir, 'grep -n foo file').code, 0)
})

// --- guard-bash : merge

test('gh pr merge refusé sans essai, ou sur un dernier essai rouge', () => {
  const dir = depot('us-101-x')
  assert.equal(bash(dir, 'gh pr merge --squash --delete-branch').code, 2)
  essai(dir, 'US-101', 1, true)
  essai(dir, 'US-101', 2, false)
  const r = bash(dir, 'gh pr merge --squash')
  assert.equal(r.code, 2)
  assert.match(r.err, /n° 2/)
})

test('gh pr merge accepté sur un dernier essai vert, et hors branche de story', () => {
  const dir = depot('us-101-x')
  essai(dir, 'US-101', 1, false)
  essai(dir, 'US-101', 2, true)
  assert.equal(bash(dir, 'gh pr merge --squash').code, 0)
  assert.equal(bash(depot('docs-x'), 'gh pr merge --squash').code, 0)
})

// --- stop-gate

const stop = (dir, entree = {}, env = { SOCLE_STOP_GATE: '1' }) => hook('stop-gate.mjs', dir, entree, env)

test('stop : inactif sans SOCLE_STOP_GATE', () => {
  const dir = depot('us-101-x')
  essai(dir, 'US-101', 1, false)
  assert.equal(stop(dir, {}, {}).code, 0)
})

test('stop : renvoyé au travail sur un dernier essai rouge ou un diff non commité', () => {
  const rouge = depot('us-101-x')
  essai(rouge, 'US-101', 1, false)
  assert.equal(stop(rouge).code, 2)
  const sale = depot('us-101-x')
  essai(sale, 'US-101', 1, true)
  fs.writeFileSync(path.join(sale, 'x.txt'), 'x')
  assert.equal(stop(sale).code, 2)
})

test('stop : une seule relance, et libre sur un essai vert commité', () => {
  const dir = depot('us-101-x')
  essai(dir, 'US-101', 1, false)
  assert.equal(stop(dir, { stop_hook_active: true }).code, 0)
  const vert = depot('us-101-x')
  essai(vert, 'US-101', 1, true)
  assert.equal(stop(vert).code, 0)
  assert.equal(stop(depot('main')).code, 0)
})
