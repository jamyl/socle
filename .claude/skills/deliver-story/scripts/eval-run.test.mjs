// Banc de tests du scorer. `node --test .claude/skills/deliver-story/scripts/`
//
// Chaque test monte un dépôt git jetable avec son propre `stack.md`, appelle le
// scorer comme un agent l'appellerait, et relit les fichiers qu'il a écrits.
// Rien n'est mocké côté scorer : ce sont ses vraies sorties qui sont vérifiées.

import { spawnSync } from 'node:child_process'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { after, test } from 'node:test'
import { fileURLToPath } from 'node:url'

const SCORER = path.join(path.dirname(fileURLToPath(import.meta.url)), 'eval-run.mjs')
const jetables = []

after(() => { for (const d of jetables) fs.rmSync(d, { recursive: true, force: true }) })

// Le tableau minimal de stack.md §5. Le libellé est paramétrable : le cœur écrit
// « Lancer la suite de tests », le module Laravel « Suite de tests ».
function depot ({ testLabel = 'Lancer la suite de tests', testCmd = 'true', lintCmd = 'true', scanner = true } = {}) {
  const dir = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'socle-eval-'))
  jetables.push(dir)
  fs.mkdirSync(path.join(dir, 'docs/engineering'), { recursive: true })
  fs.writeFileSync(path.join(dir, 'docs/engineering/stack.md'),
    '## 5. Commandes\n\n| Intention | Commande |\n|---|---|\n' +
    `| Démarrer l'environnement | \`true\` |\n` +
    `| ${testLabel} | \`${testCmd}\` |\n` +
    `| Analyse statique | \`${lintCmd}\` |\n`)
  if (scanner) {
    fs.mkdirSync(path.join(dir, '.github'), { recursive: true })
    fs.writeFileSync(path.join(dir, '.github/scan-secrets.sh'), '#!/bin/sh\nexit 0\n')
    fs.chmodSync(path.join(dir, '.github/scan-secrets.sh'), 0o755)
  }
  fs.writeFileSync(path.join(dir, 'source.txt'), 'initial\n')
  for (const argv of [['init', '-q'], ['add', '-A'], ['-c', 'user.email=t@t.invalid', '-c', 'user.name=T', 'commit', '-qm', 'base']]) {
    const r = spawnSync('git', argv, { cwd: dir, encoding: 'utf8' })
    assert.equal(r.status, 0, `git ${argv.join(' ')} : ${r.stderr}`)
  }
  return dir
}

function lancer (dir, args) {
  const r = spawnSync(process.execPath, [SCORER, ...args, '--racine', dir], { cwd: dir, encoding: 'utf8' })
  return { code: r.status, out: `${r.stdout}${r.stderr}` }
}

function essai (dir, story, n) {
  return JSON.parse(fs.readFileSync(
    path.join(dir, '.socle/runs', story, `attempt-${String(n).padStart(3, '0')}.json`), 'utf8'))
}

// --- 1. Le score, dimension par dimension.

test('succès total : score 100, pass, sortie 0', () => {
  const dir = depot()
  const { code, out } = lancer(dir, ['attempt', 'US-101', '--hypothesis', 'H1'])
  assert.equal(code, 0, out)
  const e = essai(dir, 'US-101', 1)
  assert.equal(e.score, 100)
  assert.equal(e.pass, true)
  assert.equal(e.signature, null)
  assert.match(out, /DÉCISION : terminé/)
})

test('tests rouges : score 60, pass faux, sortie 1, sortie réelle imprimée', () => {
  const dir = depot()
  const { code, out } = lancer(dir, ['attempt', 'US-101', '--hypothesis', 'H1', '--test-cmd', 'echo "FAIL: 1 assertion failed"; exit 1'])
  assert.equal(code, 1)
  const e = essai(dir, 'US-101', 1)
  assert.equal(e.score, 60)          // secrets 50 + tests 0 + statique 10
  assert.equal(e.pass, false)
  assert.equal(e.dims.tests.statut, 'rouge')
  assert.match(out, /sortie réelle/)
  assert.match(out, /1 assertion failed/)
})

test('analyse statique : chaque erreur retire un point', () => {
  const dir = depot()
  lancer(dir, ['attempt', 'US-101', '--hypothesis', 'H1', '--lint-cmd', 'printf "error a\\nerror b\\n"; exit 1'])
  const e = essai(dir, 'US-101', 1)
  assert.equal(e.dims.lint.erreurs, 2)
  assert.equal(e.score, 98)          // secrets 50 + tests 40 + (10 - 2)
  assert.equal(e.pass, false)
})

test('secret détecté : la dimension la plus chère tombe', () => {
  const dir = depot()
  const { code } = lancer(dir, ['attempt', 'US-101', '--hypothesis', 'H1', '--secrets-cmd', 'echo "Secret potentiel"; exit 1'])
  assert.equal(code, 1)
  const e = essai(dir, 'US-101', 1)
  assert.equal(e.score, 50)          // secrets 0 + tests 40 + statique 10
  assert.equal(e.pass, false)
})

test('commande à compléter dans stack.md : non mesuré, jamais deviné', () => {
  const dir = depot({ testCmd: 'À COMPLÉTER' })
  const { code, out } = lancer(dir, ['attempt', 'US-101', '--hypothesis', 'H1'])
  assert.equal(code, 1)
  const e = essai(dir, 'US-101', 1)
  assert.equal(e.dims.tests.statut, 'skipped')
  assert.match(e.dims.tests.motif, /à compléter/i)
  assert.equal(e.pass, false, 'une dimension non mesurée ne vaut pas vert')
  assert.equal(e.score, 60)          // secrets 50 + tests 0 (non mesuré) + statique 10
  assert.match(out, /non mesuré/)
})

test('scanner absent : dimension secrets non mesurée, avec son motif', () => {
  const dir = depot({ scanner: false })
  lancer(dir, ['attempt', 'US-101', '--hypothesis', 'H1'])
  const e = essai(dir, 'US-101', 1)
  assert.equal(e.dims.secrets.statut, 'skipped')
  assert.match(e.dims.secrets.motif, /scan-secrets\.sh absent/)
  assert.equal(e.score, 50)          // secrets 0 (non mesuré) + tests 40 + statique 10
  assert.equal(e.pass, false)
})

// --- 2. Le cache et la détection de boucle.

test('les essais s\'empilent, numérotés, sans écraser', () => {
  const dir = depot()
  lancer(dir, ['attempt', 'US-102', '--hypothesis', 'H1'])
  fs.writeFileSync(path.join(dir, 'source.txt'), 'modifié\n')
  lancer(dir, ['attempt', 'US-102', '--hypothesis', 'H1'])
  const fichiers = fs.readdirSync(path.join(dir, '.socle/runs/US-102')).sort()
  assert.deepEqual(fichiers, ['attempt-001.json', 'attempt-002.json'])
  assert.equal(essai(dir, 'US-102', 1).n, 1)
  assert.equal(essai(dir, 'US-102', 2).n, 2)
})

test('arbre de travail inchangé entre deux essais : identiqueA pointe le premier', () => {
  const dir = depot()
  lancer(dir, ['attempt', 'US-102', '--hypothesis', 'H1'])
  const { out } = lancer(dir, ['attempt', 'US-102', '--hypothesis', 'H1'])
  assert.equal(essai(dir, 'US-102', 2).identiqueA, 1)
  assert.match(out, /IDENTIQUE à l'essai 1/)
})

test('même erreur deux fois : la signature est stable et le strike monte', () => {
  const dir = depot()
  const rouge = 'echo "Error: undefined method at line 42"; exit 1'
  lancer(dir, ['attempt', 'US-103', '--hypothesis', 'H1', '--test-cmd', rouge])
  fs.writeFileSync(path.join(dir, 'source.txt'), 'micro-patch\n')
  lancer(dir, ['attempt', 'US-103', '--hypothesis', 'H1', '--test-cmd', rouge])
  const a = essai(dir, 'US-103', 1)
  const b = essai(dir, 'US-103', 2)
  assert.equal(a.signature.hash, b.signature.hash)
  assert.equal(a.strikes, 1)
  assert.equal(b.strikes, 2)
})

test('la signature ignore les numéros de ligne : deux échecs équivalents comptent comme un strike', () => {
  const dir = depot()
  lancer(dir, ['attempt', 'US-103', '--hypothesis', 'H1', '--test-cmd', 'echo "Error: undefined method at line 42"; exit 1'])
  lancer(dir, ['attempt', 'US-103', '--hypothesis', 'H1', '--test-cmd', 'echo "Error: undefined method at line 87"; exit 1'])
  assert.equal(essai(dir, 'US-103', 1).signature.hash, essai(dir, 'US-103', 2).signature.hash)
  assert.equal(essai(dir, 'US-103', 2).strikes, 2)
})

// --- 3. La régression qui compte : le 3e micro-patch est refusé.

test('deux strikes puis refus du 3e essai, jusqu\'à un abandon écrit', () => {
  const dir = depot()
  const rouge = 'echo "Error: still broken"; exit 1'
  const H1 = 'H1 : le cache renvoie une valeur périmée'
  const H2 = 'H2 : la transaction n\'est pas encore commitée'

  const un = lancer(dir, ['attempt', 'US-104', '--hypothesis', H1, '--test-cmd', rouge])
  assert.equal(un.code, 1)
  assert.equal(essai(dir, 'US-104', 1).strikes, 1)
  assert.match(un.out, /DÉCISION : continuer/)

  fs.writeFileSync(path.join(dir, 'source.txt'), 'micro-patch 1\n')
  const deux = lancer(dir, ['attempt', 'US-104', '--hypothesis', H1, '--test-cmd', rouge])
  assert.equal(deux.code, 1)
  assert.equal(essai(dir, 'US-104', 2).strikes, 2)
  assert.match(deux.out, /DÉCISION : pivoter/)

  // Le 3e micro-patch sur la même hypothèse : refusé, rien exécuté, rien écrit.
  fs.writeFileSync(path.join(dir, 'source.txt'), 'micro-patch 2\n')
  const trois = lancer(dir, ['attempt', 'US-104', '--hypothesis', H1, '--test-cmd', rouge])
  assert.equal(trois.code, 3)
  assert.match(trois.out, /2 strikes/)
  assert.match(trois.out, /rien n'a été exécuté/)
  assert.equal(fs.existsSync(path.join(dir, '.socle/runs/US-104/attempt-003.json')), false,
    'un essai refusé ne laisse pas de trace d\'exécution')

  // L'abandon écrit est la seule sortie : il passe, et il remet le compteur à zéro.
  const abandon = lancer(dir, ['attempt', 'US-104', '--hypothesis', H1,
    '--abandon', 'le cache n\'était pas en cause : l\'erreur survient avant sa lecture',
    '--test-cmd', rouge])
  assert.equal(abandon.code, 1)
  assert.equal(essai(dir, 'US-104', 3).abandon,
    'le cache n\'était pas en cause : l\'erreur survient avant sa lecture')

  // Une autre hypothèse repart à un strike, malgré la même erreur.
  const quatre = lancer(dir, ['attempt', 'US-104', '--hypothesis', H2, '--test-cmd', rouge])
  assert.equal(quatre.code, 1)
  assert.equal(essai(dir, 'US-104', 4).strikes, 1, 'un abandon remet le compteur à zéro')
})

test('une hypothèse à deux strikes reste refusée même plus tard', () => {
  const dir = depot()
  const rouge = 'echo "Error: still broken"; exit 1'
  lancer(dir, ['attempt', 'US-105', '--hypothesis', 'H1', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-105', '--hypothesis', 'H1', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-105', '--hypothesis', 'H1', '--abandon', 'faux', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-105', '--hypothesis', 'H2', '--test-cmd', rouge])
  const retour = lancer(dir, ['attempt', 'US-105', '--hypothesis', 'H1', '--test-cmd', rouge])
  assert.equal(retour.code, 3, 'une piste morte ne se rouvre pas')
})

// --- 4. Le pré-vol lit ce que le cache a gardé.

test('le pré-vol nomme les hypothèses mortes et les signatures vues', () => {
  const dir = depot()
  const rouge = 'echo "Error: still broken"; exit 1'
  lancer(dir, ['attempt', 'US-106', '--hypothesis', 'H1 : le cache', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-106', '--hypothesis', 'H1 : le cache', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-106', '--hypothesis', 'H1 : le cache', '--abandon', 'pas le cache', '--test-cmd', rouge])
  const { code, out } = lancer(dir, ['preflight', 'US-106'])
  assert.equal(code, 0)
  assert.match(out, /H1 : le cache/)
  assert.match(out, /ABANDONNÉE/)
  assert.match(out, /pas le cache/)
  assert.match(out, /Signatures d'échec déjà vues/)
})

test('pré-vol sans essai : le dit, et ne plante pas', () => {
  const dir = depot()
  const { code, out } = lancer(dir, ['preflight', 'US-199'])
  assert.equal(code, 0)
  assert.match(out, /aucun essai consigné/)
})

// --- 5. La rétrospective.

test('la rétro donne le ratio, la leçon écrite, et les lignes à coller', () => {
  const dir = depot()
  const rouge = 'echo "Error: still broken"; exit 1'
  lancer(dir, ['attempt', 'US-107', '--hypothesis', 'H1', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-107', '--hypothesis', 'H1', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-107', '--hypothesis', 'H1', '--abandon', 'H1 supposait un cache, il n\'y en a pas', '--test-cmd', rouge])
  lancer(dir, ['attempt', 'US-107', '--hypothesis', 'H2'])          // vert
  const { code, out } = lancer(dir, ['retro', 'US-107'])
  assert.equal(code, 0)
  assert.match(out, /essais\s+: 4/)
  assert.match(out, /réussis \(pass\)\s+: 1/)
  assert.match(out, /ratio essais\/réussite : 4\.0/)
  assert.match(out, /H1 supposait un cache/)
  assert.match(out, /essais : 4, ratio : 4\.0/)      // la ligne de JOURNAL.md
  assert.match(out, /DECISIONS\.md/)                  // une impasse a été rencontrée
  assert.match(out, /H2/)                             // ce qui a marché
})

test('aucune impasse : la rétro ne fabrique pas de décision', () => {
  const dir = depot()
  lancer(dir, ['attempt', 'US-108', '--hypothesis', 'H1'])
  const { out } = lancer(dir, ['retro', 'US-108'])
  assert.match(out, /ratio essais\/réussite : 1\.0/)
  assert.match(out, /Aucune impasse/)
  assert.doesNotMatch(out, /\| D<n> \|/)
})

test('aucun essai vert : le ratio le dit au lieu de diviser par zéro', () => {
  const dir = depot()
  lancer(dir, ['attempt', 'US-109', '--hypothesis', 'H1', '--test-cmd', 'exit 1'])
  const { out } = lancer(dir, ['retro', 'US-109'])
  assert.match(out, /ratio essais\/réussite : ∞ \(aucun essai vert\)/)
})

// --- 6. Les commandes viennent de stack.md, quel que soit le libellé.

test('les deux libellés de stack.md donnent la même commande', () => {
  for (const label of ['Lancer la suite de tests', 'Suite de tests']) {
    const dir = depot({ testLabel: label, testCmd: 'echo marqueur-unique' })
    lancer(dir, ['attempt', 'US-110', '--hypothesis', 'H1'])
    assert.equal(essai(dir, 'US-110', 1).dims.tests.cmd, 'echo marqueur-unique',
      `libellé « ${label} » : commande non trouvée dans stack.md §5`)
  }
})

test('stack.md absent : tout est non mesuré, rien n\'est inventé', () => {
  const dir = depot()
  fs.rmSync(path.join(dir, 'docs/engineering/stack.md'))
  lancer(dir, ['attempt', 'US-111', '--hypothesis', 'H1'])
  const e = essai(dir, 'US-111', 1)
  assert.equal(e.dims.tests.statut, 'skipped')
  assert.equal(e.dims.lint.statut, 'skipped')
  assert.equal(e.score, 50)          // seul le scanner de secrets a pu tourner
  assert.equal(e.pass, false)
})

// --- 7. Usage.

test('story mal formée et sous-commande inconnue sortent en 2', () => {
  const dir = depot()
  assert.equal(lancer(dir, ['attempt', 'nawak']).code, 2)
  assert.equal(lancer(dir, ['danser', 'US-101']).code, 2)
  assert.equal(lancer(dir, ['attempt', 'US-101', '--inventé', 'x']).code, 2)
})
