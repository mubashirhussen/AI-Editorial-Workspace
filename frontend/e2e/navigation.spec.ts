import { test, expect } from '@playwright/test';

test.describe('Navigation and Workspace Shell', () => {
  test.beforeEach(async ({ page }) => {
    // Mock dashboard stats and projects
    await page.route('**/api/v1/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_projects: 3,
          total_sources: 12,
          total_drafts: 4,
          total_editorials: 2,
          avg_flesch_score: 68.4,
          recent_activities: []
        }),
      });
    });

    await page.route('**/api/v1/projects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'proj-1',
            title: 'AI Compute Clusters 2026',
            description: 'Investigating next-gen accelerators',
            created_at: new Date().toISOString(),
            sources_count: 4,
          }
        ]),
      });
    });

    await page.route('**/api/v1/writing/drafts', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route('**/api/v1/editorial', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });
  });

  test('should load the workspace shell and navigate across modules', async ({ page }) => {
    await page.goto('/');

    // Verify redirected to dashboard
    await expect(page).toHaveURL(/.*\/dashboard/);

    // Verify branding in sidebar
    await expect(page.locator('text=Editorial AI')).toBeVisible();
    await expect(page.locator('text=This Week in AI')).toBeVisible();

    // Verify navigation links are visible
    const researchNav = page.locator('nav a', { hasText: 'Research Assistant' });
    const writingNav = page.locator('nav a', { hasText: 'Writing Assistant' });
    const editorialNav = page.locator('nav a', { hasText: 'Editorial Studio' });
    const projectsNav = page.locator('nav a', { hasText: 'Research Projects' });
    const settingsNav = page.locator('nav a', { hasText: 'Settings' });

    await expect(researchNav).toBeVisible();
    await expect(writingNav).toBeVisible();
    await expect(editorialNav).toBeVisible();
    await expect(projectsNav).toBeVisible();
    await expect(settingsNav).toBeVisible();

    // Navigate to Writing Assistant
    await writingNav.click();
    await expect(page).toHaveURL(/.*\/writing/);
    await expect(page.locator('text=Writing Assistant & Auditor')).toBeVisible();

    // Navigate to Editorial Studio
    await editorialNav.click();
    await expect(page).toHaveURL(/.*\/editorial/);

    // Navigate to Settings
    await settingsNav.click();
    await expect(page).toHaveURL(/.*\/settings/);
  });
});

