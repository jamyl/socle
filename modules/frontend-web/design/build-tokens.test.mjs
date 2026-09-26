import { test } from 'node:test'
import assert from 'node:assert/strict'
import { versCss } from './build-tokens.mjs'

test('couleur, dimension, police et alias deviennent des propriétés CSS', () => {
  const css = versCss({
    color: { $type: 'color', accent: { $value: { colorSpace: 'srgb', components: [0, 0, 1], hex: '#0000ff' } }, lien: { $value: '{color.accent}' } },
    espace: { 2: { $value: { value: 8, unit: 'px' } } },
    police: { texte: { $value: ['Source Sans 3', 'sans-serif'] } },
  })
  assert.match(css, /--color-accent: #0000ff;/)
  assert.match(css, /--color-lien: var\(--color-accent\);/)
  assert.match(css, /--espace-2: 8px;/)
  assert.match(css, /--police-texte: "Source Sans 3", sans-serif;/)
})

test('une couleur sans hex garde son espace colorimétrique', () => {
  assert.match(versCss({ c: { $value: { colorSpace: 'oklch', components: [0.7, 0.1, 250] } } }), /--c: color\(oklch 0.7 0.1 250\);/)
})

test('une valeur inconnue fait échouer la génération au lieu d\'écrire du CSS faux', () => {
  assert.throws(() => versCss({ x: { $value: { bizarre: true } } }), /non gérée/)
})
