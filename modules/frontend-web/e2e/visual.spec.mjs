import { test, expect } from '@playwright/test'
import { routes } from './routes.mjs'

// N7 : un écran validé ne change plus sans qu'on le veuille. Une différence
// voulue se valide en régénérant la capture (--update-snapshots) dans le même
// commit que le changement — jamais en élargissant la tolérance.
for (const route of routes) {
  test(`capture ${route}`, async ({ page }, info) => {
    await page.goto(route)
    const nom = route === '/' ? 'accueil' : route.replace(/^\/|\/$/g, '').replace(/\//g, '-')
    await expect(page).toHaveScreenshot(`${nom}-${info.project.name}.png`, { fullPage: true })
  })
}
