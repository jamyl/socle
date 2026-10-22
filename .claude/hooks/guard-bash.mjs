#!/usr/bin/env node
//
// socle — hook PreToolUse sur Bash. Trois règles de
// `.claude/rules/git-operations.md` tenues par un garde plutôt que par la
// mémoire de l'agent : une règle en prose se lit, puis s'oublie au 40e tour.
//
//   1. aucun push vers `main`, aucun push forcé ;
//   2. aucun `--no-verify` ;
//   3. aucun `gh pr merge` sur une branche `us-XXX-*` dont le dernier essai
//      consigné par `eval-run.mjs` n'est pas `pass`, ou dont le verdict de
//      revue (`eval-run.mjs verdict`) n'est pas MERGE pour le HEAD courant ;
//   3 bis. aucun commentaire `VERDICT: MERGE` (celui qui déclenche le robot
//      `fusion.yml` en mode organisation) sans ce même verdict consigné ;
//   4. aucun `gh pr create` sur une telle branche sans ses preuves dans le
//      corps : la rétrospective de `eval-run.mjs` et le verdict `approuve` de
//      la revue (`.claude/skills/deliver-story/SKILL.md` §5) ;
//   5. aucun mot-clé de fermeture (`Fixes #12`) dans un commit ou une PR : au
//      merge, GitHub fermerait l'issue, et l'alarme de merge en est une ;
//   6. aucun `rm` ni `mv` sur l'état local que git ne suit pas (`.socle/`,
//      `.git`, `.env`, `.claude/settings.local.json`), aucun `git clean -x`.
//      `.socle/` tient les strikes et le verdict : l'effacer remettrait les
//      deux strikes à zéro et rouvrirait une seconde revue sur le même commit ;
//   7. aucun nom de `.socle/interdits.txt` dans un commit (message et diff
//      ajouté) ni dans une PR : une liste locale, que git ignore ;
//   8. aucune commande qui ne rend jamais la main (`gh run watch` sans run,
//      `docker compose up` sans `-d`, `logs -f`, `tail -f`), sauf bornée.
//
// Code 2 = refus : Claude Code annule la commande et montre stderr à l'agent.
//
// Ce n'est pas un contrôle de sécurité, pas plus que la liste `deny` : une
// commande écrite pour le contourner (script intermédiaire, refspec entre
// guillemets, `gh pr merge <n>` lancé depuis une autre branche) passe. Il
// rattrape l'agent qui oublie, pas celui qui triche — voir
// `docs/engineering/config-locale.md`.

import fs from 'node:fs'
import path from 'node:path'
import { dernierEssai, git, lireEntree, lireVerdict, refuser, storyDeBranche } from './etat-story.mjs'

const { entree, cwd, racine, branche } = lireEntree()
const brut = entree.tool_input?.command ?? ''

// Les chaînes entre guillemets ne portent ni séparateur ni option : un message
// de commit qui contient « -n » ou « ; » ne doit rien déclencher.
// Le corps d'un heredoc non plus : c'est du texte (message de commit, corps de
// PR), et il cite volontiers les commandes mêmes que ce hook refuse.
const segments = brut
  .replace(/<<-?\s*(['"]?)(\w+)\1[^\n]*\n[\s\S]*?\n\s*\2\s*(?=\n|$)/g, 'H')
  .replace(/"(?:[^"\\]|\\.)*"|'[^']*'/g, 'Q')
  .split(/&&|\|\||[;|\n]/)
  .map((s) => s.trim().split(/\s+/).filter(Boolean))

const AVEC_VALEUR = new Set(['-o', '--push-option', '--repo', '--receive-pack', '--exec'])
const FERMETURE = /\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?):?\s+(?:[\w.-]+\/[\w.-]+#|https?:\/\/\S+\/issues\/|#)\d+/i
const PROTEGE = /(^|\/)(\.socle|\.git)(\/|$)|(^|\/)\.env(\.(?!example$)[^/]+)?$|(^|\/)\.claude\/settings\.local\.json$/
const LANCEURS = new Set(['sudo', 'xargs', 'command', 'exec', 'nohup', 'git'])

// Le texte d'un message : la commande (guillemets, heredoc) et le fichier
// qu'elle désigne (`--body-file`, `-F`, `--file`).
function texte () {
  const fichier = /(?:--body-file|--file|-F)[= ]+['"]?([^\s'"]+)/.exec(brut)?.[1]
  const chemin = fichier && path.resolve(cwd, fichier)
  return brut + (chemin && fs.existsSync(chemin) ? fs.readFileSync(chemin, 'utf8') : '')
}

// Les noms qui ne doivent jamais être publiés : un projet source, un client.
// La liste est locale (`.socle/` est ignoré par git) : commitée, elle
// publierait elle-même ce qu'elle protège. Un terme par ligne, `#` commente.
function nomInterdit (textes) {
  const f = path.join(racine, '.socle/interdits.txt')
  if (!fs.existsSync(f)) return null
  const termes = fs.readFileSync(f, 'utf8').split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'))
  for (const t of termes) {
    const re = new RegExp(`(?<![\\p{L}\\p{N}])${t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\p{L}\\p{N}])`, 'iu')
    for (const [ou, contenu] of textes) {
      const ligne = contenu.split('\n').find((l) => re.test(l))
      if (ligne !== undefined) return { t, ou, ligne: ligne.trim().slice(0, 120) }
    }
  }
  return null
}

// Les lignes ajoutées d'un diff, fichier par fichier.
function ajouts (args) {
  const parFichier = new Map()
  let f = null
  for (const l of (git(racine, ['diff', ...args, '-U0', '--no-color']) ?? '').split('\n')) {
    if (l.startsWith('+++ ')) f = l.slice(4).replace(/^b\//, '')
    else if (l.startsWith('+') && f) parFichier.set(f, (parFichier.get(f) ?? '') + l.slice(1) + '\n')
  }
  return [...parFichier]
}

// Une commande qui ne rend jamais la main coûte, dans une boucle sans
// surveillance, le délai d'expiration de l'outil, puis revient au tour
// suivant. Bornée par `timeout`, un `&` final ou `run_in_background`, elle passe.
function sansFin (mots) {
  if (mots[0] === 'timeout' || mots.includes('&')) return null
  const apres = (mot) => mots.slice(mots.indexOf(mot) + 1)
  const g = mots.indexOf('gh')
  if (g >= 0 && mots[g + 1] === 'run' && mots[g + 2] === 'watch' && !mots.slice(g + 3).some((a) => /^\d+$/.test(a))) {
    return '`gh run watch` sans numéro de run demande lequel, et attend une réponse. Utilise `gh pr checks --watch --fail-fast`.'
  }
  if (mots.includes('docker') || mots.includes('docker-compose')) {
    if (mots.includes('up') && !apres('up').some((a) => a === '--detach' || a === '--wait' || /^-[a-zA-Z]*d/.test(a))) {
      return '`docker compose up` sans `-d` garde le terminal tant que les conteneurs tournent. Utilise `docker compose up -d`, puis `logs --tail 50`.'
    }
    if (mots.includes('logs') && apres('logs').some((a) => a.startsWith('--follow') || /^-[a-zA-Z]*f/.test(a))) {
      return '`logs -f` suit le journal sans fin. Utilise `--tail 50`.'
    }
  }
  if (mots.includes('tail') && apres('tail').some((a) => a.startsWith('--follow') || /^-[a-zA-Z]*[fF]/.test(a))) {
    return '`tail -f` suit le fichier sans fin. Utilise `tail -n 50`.'
  }
  return null
}

function cibleProtegee (mots) {
  const i = mots.findIndex((m) => /^(?:\S*\/)?(?:rm|mv|unlink)$/.test(m))
  if (i < 0 || !mots.slice(0, i).every((m) => LANCEURS.has(m) || m.startsWith('-'))) return null
  return mots.slice(i + 1).find((a) => PROTEGE.test(a)) ?? null
}

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
  const fin = entree.tool_input?.run_in_background ? null : sansFin(mots)
  if (fin) refuser(`⛔ commande sans fin : ${fin}\n   Ou borne-la (\`timeout 60 …\`), ou lance-la en arrière-plan.`)

  const push = sousCommande(mots, 'push')
  if (push) verifierPush(push)

  if (sousCommande(mots, 'commit')?.some((a) => /^-[a-zA-Z]*n[a-zA-Z]*$/.test(a)) || (mots.includes('git') && mots.includes('--no-verify'))) {
    refuser('⛔ --no-verify refusé : un hook qui gêne se discute, il ne se saute pas.\n' +
      '   Règle : .claude/rules/exploration-policy.md §3.')
  }

  const cible = cibleProtegee(mots)
  if (cible) {
    refuser(`⛔ ${cible} : état local que git ne suit pas, rien ne le rend. .socle/ tient les essais et le verdict de revue.\n` +
      '   Règle : .claude/rules/git-operations.md « Interdits ».')
  }
  const clean = sousCommande(mots, 'clean')
  if (clean?.some((a) => /^-[a-zA-Z]*[xX]/.test(a)) && !clean.some((a) => a === '--dry-run' || /^-[a-zA-Z]*n/.test(a))) {
    refuser('⛔ git clean -x efface aussi les fichiers ignorés : .socle/, .env, .claude/settings.local.json.\n' +
      '   git clean -fd suffit pour les fichiers non suivis.')
  }

  const g = mots.indexOf('gh')
  const commit = sousCommande(mots, 'commit')
  if (commit || (g >= 0 && mots[g + 1] === 'pr' && ['create', 'edit', 'comment'].includes(mots[g + 2]))) {
    const textes = [['le message', texte()]]
    if (commit) {
      textes.push(...ajouts(['--cached']))
      if (commit.some((a) => a === '--all' || /^-[a-zA-Z]*a[a-zA-Z]*$/.test(a))) textes.push(...ajouts([]))
    }
    const n = nomInterdit(textes)
    if (n) {
      refuser(`⛔ nom interdit « ${n.t} » dans ${n.ou} : ${n.ligne}\n` +
        '   Liste locale : .socle/interdits.txt. Reformule de façon générique (« un projet réel », « la source »).')
    }
  }
  if (commit || (g >= 0 && mots[g + 1] === 'pr' && ['create', 'edit'].includes(mots[g + 2]))) {
    const m = FERMETURE.exec(texte())
    if (m) {
      refuser(`⛔ mot-clé de fermeture refusé (« ${m[0]} ») : au merge, GitHub fermerait l'issue, et l'alarme de merge en est une.\n` +
        `   Écris « réf. #${/\d+$/.exec(m[0])[0]} ». Règle : .claude/rules/git-operations.md « Interdits ».`)
    }
  }
  if (g >= 0 && mots[g + 1] === 'pr' && mots[g + 2] === 'create' && storyDeBranche(branche)) {
    const corps = texte()
    const manque = [['rétrospective', 'la sortie de eval-run.mjs retro'], ['approuve', 'le verdict approuve de review-story']]
      .filter(([m]) => !corps.includes(m)).map(([, quoi]) => quoi)
    if (manque.length) {
      refuser(`⛔ PR refusée : le corps ne porte pas ${manque.join(' ni ')}.\n` +
        '   Gabarit : .claude/skills/deliver-story/SKILL.md §5. La preuve vit dans la PR, pas dans .socle/.')
    }
  }
  if (g >= 0 && mots[g + 1] === 'pr' && mots[g + 2] === 'comment' && brut.includes('VERDICT: MERGE') && storyDeBranche(branche)) {
    const story = storyDeBranche(branche)
    const v = lireVerdict(racine, story)
    if (v?.verdict !== 'MERGE' || v.head !== git(racine, ['rev-parse', 'HEAD'])) {
      refuser(`⛔ commentaire refusé : « VERDICT: MERGE » déclenche le robot de fusion, et ${story} n'a pas de verdict MERGE consigné pour le HEAD courant.\n` +
        `   .claude/skills/deliver-story/scripts/eval-run.mjs verdict ${story} --verdict <MERGE|HUMAIN>`)
    }
  }
  if (g >= 0 && mots[g + 1] === 'pr' && mots[g + 2] === 'merge') {
    const story = storyDeBranche(branche)
    if (!story) continue
    const essai = dernierEssai(racine, story)
    if (!essai?.pass) {
      refuser(`⛔ merge refusé : ${essai ? `le dernier essai de ${story} (n° ${essai.n}) n'est pas vert` : `aucun essai consigné pour ${story}`}.\n` +
        `   Lance la preuve avant le merge :\n` +
        `     .claude/skills/deliver-story/scripts/eval-run.mjs attempt ${story} --hypothesis "…"`)
    }
    const v = lireVerdict(racine, story)
    const tete = git(racine, ['rev-parse', 'HEAD'])
    if (!v) refuser(`⛔ merge refusé : aucun verdict de revue consigné pour ${story}.\n` +
      `   .claude/skills/deliver-story/scripts/eval-run.mjs verdict ${story} --verdict <MERGE|HUMAIN>`)
    // Après la revue, la clôture ne commite que la tenue du backlog (statut,
    // journal) : ce n'est pas du code à relire. Tout autre fichier, si.
    const depuis = v.head === tete ? '' : git(racine, ['diff', '--name-only', v.head, 'HEAD'])
    const nonRelus = depuis === null ? ['(commit du verdict introuvable)'] : depuis.split('\n').filter((f) => f && !f.startsWith('docs/backlog/'))
    if (nonRelus.length) refuser(`⛔ merge refusé : le verdict porte sur ${v.head.slice(0, 7)}, HEAD est ${tete?.slice(0, 7)}.\n` +
      `   Pas relu depuis : ${nonRelus.join(', ')}. Relance review-story sur le nouveau diff.`)
    if (v.verdict !== 'MERGE') refuser(`⛔ merge refusé : verdict ${v.verdict}. La PR attend le propriétaire.`)
  }
}
