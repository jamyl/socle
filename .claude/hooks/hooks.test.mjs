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

function verdictConsigne (dir, story, verdict, head) {
  const d = path.join(dir, '.socle/runs', story)
  fs.mkdirSync(d, { recursive: true })
  head ??= spawnSync('git', ['rev-parse', 'HEAD'], { cwd: dir, encoding: 'utf8' }).stdout.trim()
  fs.writeFileSync(path.join(d, 'verdict.json'), JSON.stringify({ head, verdict }))
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

test('gh pr merge accepté sur un essai vert et un verdict MERGE du HEAD, et hors branche de story', () => {
  const dir = depot('us-101-x')
  essai(dir, 'US-101', 1, false)
  essai(dir, 'US-101', 2, true)
  verdictConsigne(dir, 'US-101', 'MERGE')
  assert.equal(bash(dir, 'gh pr merge --squash').code, 0)
  assert.equal(bash(depot('docs-x'), 'gh pr merge --squash').code, 0)
})

test('gh pr merge refusé sur essai vert sans verdict, sur un verdict HUMAIN, ou sur un autre HEAD', () => {
  const dir = depot('us-101-x')
  essai(dir, 'US-101', 1, true)
  let r = bash(dir, 'gh pr merge --squash')
  assert.equal(r.code, 2)
  assert.match(r.err, /aucun verdict/)
  verdictConsigne(dir, 'US-101', 'HUMAIN')
  r = bash(dir, 'gh pr merge --squash')
  assert.equal(r.code, 2)
  assert.match(r.err, /HUMAIN/)
  verdictConsigne(dir, 'US-101', 'MERGE', 'f'.repeat(40))
  r = bash(dir, 'gh pr merge --squash')
  assert.equal(r.code, 2)
  assert.match(r.err, /Pas relu depuis/)
})

test('gh pr merge : un commit de clôture qui ne touche que docs/backlog/ garde le verdict, un commit de code le perd', () => {
  const dir = depot('us-101-x')
  essai(dir, 'US-101', 1, true)
  verdictConsigne(dir, 'US-101', 'MERGE')
  const commiter = (f) => {
    fs.mkdirSync(path.dirname(path.join(dir, f)), { recursive: true })
    fs.writeFileSync(path.join(dir, f), 'x\n')
    for (const argv of [['add', f], ['-c', 'user.email=t@t.invalid', '-c', 'user.name=T', 'commit', '-qm', f]]) spawnSync('git', argv, { cwd: dir })
  }
  commiter('docs/backlog/JOURNAL.md')
  assert.equal(bash(dir, 'gh pr merge --squash').code, 0)
  commiter('src/code.js')
  const r = bash(dir, 'gh pr merge --squash')
  assert.equal(r.code, 2)
  assert.match(r.err, /src\/code\.js/)
})

test('gh pr comment « VERDICT: MERGE » refusé sans verdict MERGE consigné pour HEAD, accepté avec', () => {
  const dir = depot('us-101-x')
  const cmd = 'gh pr comment -R org/p --body "VERDICT: MERGE abc"'
  assert.equal(bash(dir, cmd).code, 2)
  verdictConsigne(dir, 'US-101', 'HUMAIN')
  assert.equal(bash(dir, cmd).code, 2)
  verdictConsigne(dir, 'US-101', 'MERGE')
  assert.equal(bash(dir, cmd).code, 0)
  assert.equal(bash(dir, 'gh pr comment --body "rapport de revue"').code, 0)
})

test('heredoc : un message qui cite une commande refusée ne déclenche rien', () => {
  const dir = depot('us-101-x')
  const msg = "git commit -F - <<'EOF'\nUS-101: x\n\nOn ne fait jamais git push origin main ni gh pr merge ici.\nEOF"
  assert.equal(bash(dir, msg).code, 0)
  assert.equal(bash(dir, `${msg}\ngit push origin main`).code, 2)
})

// --- guard-bash : preuves dans la PR

test('gh pr create sur une story refusé sans rétrospective ni verdict de revue', () => {
  const dir = depot('us-101-x')
  assert.equal(bash(dir, 'gh pr create --title t --body "rien"').code, 2)
  const r = bash(dir, 'gh pr create --title t --body "US-101 — rétrospective"')
  assert.equal(r.code, 2)
  assert.match(r.err, /approuve/)
  assert.equal(bash(dir, `gh pr create --title t --body "$(cat <<'EOF'\nUS-101 — rétrospective\nrevue : approuve: true\nEOF\n)"`).code, 0)
  assert.equal(bash(depot('docs-x'), 'gh pr create --title t --body "rien"').code, 0)
})

test('gh pr create --body-file : le fichier est lu', () => {
  const dir = depot('us-101-x')
  fs.writeFileSync(path.join(dir, 'corps.md'), 'US-101 — rétrospective\napprouve: true\n')
  assert.equal(bash(dir, 'gh pr create --title t --body-file corps.md').code, 0)
  fs.writeFileSync(path.join(dir, 'vide.md'), 'rien\n')
  assert.equal(bash(dir, 'gh pr create --title t --body-file vide.md').code, 2)
})

// --- guard-bash : mots-clés de fermeture

test('mot-clé de fermeture refusé dans un commit ou une PR, sous toutes ses formes', () => {
  const dir = depot('docs-x')
  fs.writeFileSync(path.join(dir, 'msg.txt'), 'docs: x\n\nResolves: #7\n')
  for (const c of ['git commit -m "Fixes #12"', 'git commit -m "docs: x" -m "closes o/r#3"',
    'git commit -F msg.txt', "git commit -F - <<'EOF'\ndocs: x\n\nfixed #4\nEOF",
    'gh pr create --title t --body "Closes https://github.com/o/r/issues/9"', 'gh pr edit 3 --body "resolve #2"']) {
    const r = bash(dir, c)
    assert.equal(r.code, 2, c)
    assert.match(r.err, /réf\. #\d+/, c)
  }
})

test('une référence sans mot-clé de fermeture passe', () => {
  const dir = depot('docs-x')
  for (const c of ['git commit -m "docs: réf. #12"', 'git commit -m "fix: l\'alarme (#18)"',
    'git commit -m "prefix #3 du suffixe"', 'gh pr comment --body "Fixes #12 a été écrit à la main"']) {
    assert.equal(bash(dir, c).code, 0, c)
  }
})

// --- guard-bash : état local

test('rm, mv et git clean -x refusés sur l\'état local que git ne suit pas', () => {
  const dir = depot('us-101-x')
  for (const c of ['rm -rf .socle', 'rm .socle/runs/US-101/verdict.json', 'rm -rf ./.socle/', 'mv .socle /tmp/x',
    'sudo rm -rf .git', 'rm .env', 'rm backend/.env.local', 'rm .claude/settings.local.json',
    'ls && /bin/rm -r .socle/runs', 'git clean -fdx', 'git clean -f -X']) {
    assert.equal(bash(dir, c).code, 2, c)
  }
})

test('rm et git clean ailleurs passent', () => {
  const dir = depot('us-101-x')
  for (const c of ['rm -rf build', 'rm .gitignore', 'rm -r .github/old', 'rm .env.example', 'rm .envrc',
    'git clean -fd', 'git clean -ndx', 'grep -rn rm .socle']) {
    assert.equal(bash(dir, c).code, 0, c)
  }
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
