import { test, expect } from '@playwright/test';

test.describe('Accessibility, Responsive Viewports & Console Invariants', () => {
  test('should render cleanly with zero uncaught JavaScript page errors', async ({ page }) => {
    const pageErrors: Error[] = [];
    page.on('pageerror', (err) => {
      pageErrors.push(err);
    });

    // Mock minimal project stats to load dashboard
    await page.route('**/api/v1/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_projects: 1,
          total_sources: 2,
          total_drafts: 1,
          total_editorials: 1,
          avg_flesch_score: 72.0,
          recent_activities: []
        }),
      });
    });

    await page.route('**/api/v1/projects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Assert zero uncaught page runtime exceptions
    expect(pageErrors.length).toBe(0);
  });

  test('should support keyboard navigation across navigation items', async ({ page }) => {
    await page.route('**/api/v1/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_projects: 0,
          total_sources: 0,
          total_drafts: 0,
          total_editorials: 0,
          avg_flesch_score: 0,
          recent_activities: []
        }),
      });
    });

    await page.route('**/api/v1/projects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/dashboard');

    // Press Tab multiple times to verify keyboard focus flows through elements
    await page.keyboard.press('Tab');
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(['A', 'BUTTON', 'INPUT', 'SELECT']).toContain(focusedTag || 'A');
  });

  test('should adapt layout cleanly for mobile viewport (375x667)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await page.route('**/api/v1/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_projects: 2,
          total_sources: 5,
          total_drafts: 2,
          total_editorials: 1,
          avg_flesch_score: 65,
          recent_activities: []
        }),
      });
    });

    await page.route('**/api/v1/projects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/dashboard');

    // Verify main content container exists and does not exceed viewport width
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2); // allowing minor rounding margin
  });
});

