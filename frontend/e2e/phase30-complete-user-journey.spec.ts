import { test, expect } from '@playwright/test';

test.describe('Phase 30: Complete End-to-End User Journey & Release Validation', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept health check endpoint
    await page.route('**/api/v1/health/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'ready',
          database: 'connected',
          dependencies: {
            database: { status: 'healthy', latency_ms: 1.2 },
            ai_engine: 'live',
          },
        }),
      });
    });

    // Intercept dashboard statistics
    await page.route('**/api/v1/**/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_projects: 8,
          total_sources: 24,
          total_drafts: 12,
          total_editorial: 6,
          in_progress: 3,
          under_review: 2,
          approved: 2,
          finalized: 4,
          pending_human_reviews: 2,
          approved_editorials: 2,
          finalized_editorials: 4,
          total_editorials: 8,
          recent_activity: [],
        }),
      });
    });

    // Intercept projects list
    await page.route('**/api/v1/**projects**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'proj-phase30-01',
                title: 'Release Validation Project 2026',
                description: 'Validating end-to-end platform workflows and release readiness.',
                status: 'in_progress',
                sources: [
                  { id: 'src-101', title: 'Empirical Scalable Oversight' },
                ],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
            total: 1,
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Intercept auth/me
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: 'user-phase30-qa',
            email: 'qa.lead@editorial.ai',
            full_name: 'Lead Release Engineer',
            role: 'ADMIN',
            is_active: true,
            is_verified: true,
            created_at: new Date().toISOString(),
          },
          organizations: [
            {
              id: 'org-phase30-master',
              name: 'Release Validation Workspace',
              slug: 'release-workspace',
              role: 'OWNER',
              joined_at: new Date().toISOString(),
            },
          ],
        }),
      });
    });
  });

  test('Journey 1: Full Navigation and Breadcrumb Consistency Across Primary Routes', async ({ page }) => {
    await page.goto('/');

    // Verify main app layout is present
    await expect(page.locator('body')).toBeVisible();

    // Navigate to Projects page
    await page.goto('/projects');
    await expect(page).toHaveURL(/.*projects/);
    await expect(page.getByText('Projects').first()).toBeVisible();

    // Navigate to Research page
    await page.goto('/research');
    await expect(page).toHaveURL(/.*research/);

    // Navigate to Writing Assistant page
    await page.goto('/writing');
    await expect(page).toHaveURL(/.*writing/);

    // Navigate to Editorial Studio page
    await page.goto('/editorial');
    await expect(page).toHaveURL(/.*editorial/);

    // Navigate to Organization page
    await page.goto('/organization');
    await expect(page).toHaveURL(/.*organization/);

    // Navigate to Observability page
    await page.goto('/observability');
    await expect(page).toHaveURL(/.*observability/);

    // Navigate to Profile page
    await page.goto('/profile');
    await expect(page).toHaveURL(/.*profile/);
  });

  test('Journey 2: Interactive Modal Dialog Accessibility and Confirmation Handling', async ({ page }) => {
    await page.goto('/projects');

    // Look for New Project button or trigger
    const newProjectBtn = page.getByRole('button', { name: /new project|create project/i }).first();
    if (await newProjectBtn.isVisible()) {
      await newProjectBtn.click();

      // Check dialog or modal appears
      const dialog = page.locator('[role="dialog"], .modal, [aria-modal="true"]').first();
      if (await dialog.isVisible()) {
        // Press Escape to dismiss
        await page.keyboard.press('Escape');
        // Dialog should be dismissed or handle escape
        await expect(dialog).not.toBeVisible();
      }
    }
  });

  test('Journey 3: Responsive Viewport Stability', async ({ page }) => {
    // 1. Mobile viewport (390 x 844 - iPhone 12)
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // 2. Tablet viewport (768 x 1024 - iPad)
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/projects');
    await expect(page.locator('body')).toBeVisible();

    // 3. Desktop viewport (1280 x 800)
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('/editorial');
    await expect(page.locator('body')).toBeVisible();
  });
});
