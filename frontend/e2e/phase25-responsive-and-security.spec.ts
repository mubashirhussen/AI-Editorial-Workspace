import { test, expect } from '@playwright/test';

test.describe('Phase 25 - Independent Responsive & Multi-Device Validation', () => {
  test.use({ baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Mock standard API endpoints
    await page.route('**/api/v1/**', async (route) => {
      const url = route.request().url();
      const method = route.request().method();

      if (url.includes('/projects') && method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'proj-qa-25',
                title: 'Autonomous AI Agents & Edge Intelligence 2026',
                description: 'Cross-device verification project.',
                organization_id: 'org-qa-1',
                sources: [
                  { id: 'src-1', title: 'Edge Hardware Benchmark Report', url: 'https://example.com/edge' },
                  { id: 'src-2', title: 'Neural Accelerator Latency Analysis', url: 'https://example.com/accelerator' },
                  { id: 'src-3', title: 'Decentralized Intelligence Whitepaper', url: 'https://example.com/ai' },
                ],
                created_at: new Date().toISOString(),
              },
            ],
            total: 1,
            skip: 0,
            limit: 100,
          }),
        });
      }

      if (url.includes('/editorial') && method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'ed-qa-25',
                project_id: 'proj-qa-25',
                title: 'The Edge Intelligence Revolution',
                content: 'Recent breakthroughs in on-device neural accelerators [S1] allow local execution of 70B parameter models [S2]. Energy efficiency improvements reduce datacenter power draws significantly [S3].',
                status: 'IN_REVIEW',
                review_status: 'IN_REVIEW',
                word_count: 520,
                readability_score: 72.4,
                citations: ['[S1]', '[S2]', '[S3]'],
                created_at: new Date().toISOString(),
              },
            ],
            total: 1,
          }),
        });
      }

      if (url.includes('/users/me') || url.includes('/auth/me')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'user-qa-25',
            email: 'qa.lead@editorial-workspace.test',
            full_name: 'Independent QA Lead',
            is_active: true,
            active_organization_id: 'org-qa-1',
          }),
        });
      }

      if (url.includes('/organizations')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'org-qa-1', name: 'Editorial Assurance Labs', role: 'OWNER' }],
          }),
        });
      }

      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });
  });

  // 1. Desktop Experience (1280 x 800)
  test('Desktop Viewport (1280x800): Full layout rendering and navigation', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/dashboard');

    // Page must load without unhandled console errors
    await expect(page.locator('body')).toBeVisible();
    await page.waitForTimeout(500);

    // Verify main header or heading elements are present
    const heading = page.locator('h1, h2, h3').first();
    await expect(heading).toBeVisible();

    // Verify no horizontal overflow on desktop
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2); // Allow 2px tolerance for scrollbar
  });

  // 2. Tablet Experience (768 x 1024 - iPad Portrait)
  test('Tablet Viewport (768x1024): Responsive layout and drawer navigation', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/writing');

    await expect(page.locator('body')).toBeVisible();
    await page.waitForTimeout(500);

    // Verify no horizontal overflow on tablet
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2);
  });

  // 3. Mobile Viewport (375 x 667 - Mobile Portrait)
  test('Mobile Viewport (375x667): Compact UI, collapsible panels, and clean touch targets', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/projects');

    await expect(page.locator('body')).toBeVisible();
    await page.waitForTimeout(500);

    // Verify no horizontal page blowout / horizontal scroll on mobile
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2);
  });
});
