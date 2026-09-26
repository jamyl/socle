#!/usr/bin/env node
// design/tokens.json (DTCG 2025.10) → design/tokens.css (propriétés CSS).
// Le JSON est la source ; le CSS est généré et commité. `--check` sort en 1 si
// le CSS commité ne correspond plus au JSON : un écart casse le build, comme
// toute sortie générée (testing-strategy.md).
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { pathToFileURL } from 'node:url'

const ici = new URL('.', import.meta.url)
const source = new URL('tokens.json', ici)
const cible = new URL('tokens.css', ici)

const nomCss = (chemin) => `--${chemin.join('-')}`

function valeurCss(v) {
  if (typeof v === 'string') return v.replace(/^\{(.+)\}$/, (_, ref) => `var(${nomCss(ref.split('.'))})`)
  if (typeof v === 'number') return String(v)
  if (Array.isArray(v)) return v.map((f) => (/\s/.test(f) ? `"${f}"` : f)).join(', ')
  if (v.hex) return v.hex
  if (v.colorSpace) return `color(${v.colorSpace} ${v.components.join(' ')})`
  if ('unit' in v) return `${v.value}${v.unit}`
  throw new Error(`valeur de token non gérée : ${JSON.stringify(v)}`)
}

export function versCss(arbre) {
  const lignes = []
  const parcourir = (noeud, chemin) => {
    for (const [cle, val] of Object.entries(noeud)) {
      if (cle.startsWith('$')) continue
      if (val && typeof val === 'object' && '$value' in val) lignes.push(`  ${nomCss([...chemin, cle])}: ${valeurCss(val.$value)};`)
      else if (val && typeof val === 'object') parcourir(val, [...chemin, cle])
    }
  }
  parcourir(arbre, [])
  return `/* Généré depuis design/tokens.json — ne pas éditer à la main. */\n:root {\n${lignes.join('\n')}\n}\n`
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const css = versCss(JSON.parse(readFileSync(source, 'utf8')))
  if (process.argv.includes('--check')) {
    if (!existsSync(cible) || readFileSync(cible, 'utf8') !== css) {
      console.error('✗ design/tokens.css ne correspond pas à design/tokens.json — lance `npm run tokens` dans e2e/ et commite.')
      process.exit(1)
    }
    console.log('✓ design/tokens.css à jour')
  } else {
    writeFileSync(cible, css)
    console.log('→ design/tokens.css écrit')
  }
}
