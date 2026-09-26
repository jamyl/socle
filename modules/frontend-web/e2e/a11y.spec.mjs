import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { routes } from './routes.mjs'

// axe-core trouve environ la moitié des défauts d'accessibilité (Deque : 57 %
// par volume, étude du vendeur). Zéro violation ici ne veut pas dire accessible :
// le reste se relit (docs/engineering/frontend.md §3).
for (const route of routes) {
  test(`a11y ${route}`, async ({ page }) => {
    await page.goto(route)
    const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze()
    const bloquantes = violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
    expect(bloquantes.map((v) => `${v.id} (${v.impact}) : ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`)).toEqual([])
  })
}
