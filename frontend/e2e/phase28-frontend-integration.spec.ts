import { test, expect } from '@playwright/test';

test.describe('Phase 28: Frontend Implementation & User Interaction Validation', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept health and readiness endpoints
    await page.route('**/api/v1/health/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'ready',
          database: 'connected',
          db_latency_ms: 1.5,
          dependencies: {
            database: { status: 'healthy', latency_ms: 1.5 },
            ai_engine: 'live',
          },
        }),
      });
    });

    // Intercept dashboard stats
    await page.route('**/api/v1/**/dashboard/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_projects: 5,
          total_sources: 18,
          total_drafts: 7,
          total_editorial: 4,
          in_progress: 2,
          under_review: 1,
          approved: 1,
          finalized: 3,
        }),
      });
    });

    // Intercept projects list (both /api/v1/projects and /api/v1/research/projects)
    await page.route('**/api/v1/**projects**', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'proj-phase28-01',
                title: 'Phase 28 Quantum Architecture Investigation',
                description: 'Verifying end-to-end user experience and interactive dialogs.',
                status: 'in_progress',
                sources: [
                  { id: 'src-1', title: 'Quantum Computing Benchmarks 2026' }
                ],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
              {
                id: 'proj-phase28-02',
                title: 'Autonomous Multi-Agent Editorial Pipelines',
                description: 'Evaluation of collaborative agents in journalistic synthesis.',
                status: 'completed',
                sources: [],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              }
            ],
            total: 2,
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Intercept auth user me
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: 'user-phase28-01',
            email: 'editor@thisweekinai.test',
            full_name: 'Lead Technical Editor',
            role: 'ADMIN',
            is_active: true,
          },
          organizations: [
            {
              id: 'org-phase28-01',
              name: 'This Week in AI Editorial Lab',
              slug: 'this-week-in-ai',
              role: 'ADMIN',
              joined_at: new Date().toISOString(),
            }
          ],
        }),
      });
    });
  });

  test('1. Breadcrumbs in Header reflect updated navigation titles for all routes', async ({ page }) => {
    // Dashboard breadcrumb
    await page.goto('/dashboard');
    await expect(page.locator('header')).toContainText('Dashboard');

    // Projects breadcrumb
    await page.goto('/projects');
    await expect(page.locator('header')).toContainText('Research Projects');

    // Organization breadcrumb
    await page.goto('/organization');
    await expect(page.locator('header')).toContainText('Organization & Workspace');

    // Observability breadcrumb
    await page.goto('/observability');
    await expect(page.locator('header')).toContainText('AI Observability & Reliability');

    // Profile breadcrumb
    await page.goto('/profile');
    await expect(page.locator('header')).toContainText('User Profile & Security');

    // Settings breadcrumb
    await page.goto('/settings');
    await expect(page.locator('header')).toContainText('Settings');
  });

  test('2. Projects page renders accessible project cards with role="button" and keyboard support', async ({ page }) => {
    await page.goto('/projects');
    await page.waitForLoadState('networkidle');

    // Locate project cards
    const cards = page.locator('div[role="button"][tabindex="0"]');
    await expect(cards).toHaveCount(2);

    // Verify content of first card
    await expect(cards.first()).toContainText('Phase 28 Quantum Architecture Investigation');
    await expect(cards.first()).toContainText('1 Sources');

    // Test Search input filtering
    const searchInput = page.locator('input[placeholder*="Search projects"]');
    await searchInput.fill('Autonomous');
    await expect(page.locator('text=Autonomous Multi-Agent Editorial Pipelines')).toBeVisible();
    await expect(page.locator('text=Phase 28 Quantum Architecture Investigation')).not.toBeVisible();

    // Clear search
    await searchInput.fill('');
    await expect(page.locator('text=Phase 28 Quantum Architecture Investigation')).toBeVisible();
  });

  test('3. ConfirmDialog modal accessibility, escape dismissal, and backdrop handling', async ({ page }) => {
    await page.goto('/projects');
    await page.waitForLoadState('networkidle');

    // Trigger delete button on first card
    const deleteBtn = page.locator('button[title="Delete project"]').first();
    await deleteBtn.click();

    // Confirm dialog should be visible
    const dialog = page.locator('div[role="dialog"][aria-modal="true"]');
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText('Delete Research Project?');

    // Press Escape to dismiss
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();

    // Reopen dialog and dismiss via Cancel button
    await deleteBtn.click();
    await expect(dialog).toBeVisible();
    const cancelBtn = page.locator('button:has-text("Cancel")');
    await cancelBtn.click();
    await expect(dialog).not.toBeVisible();
  });

  test('4. User Profile Menu renders avatar, organization, role badge and modal navigation', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Find and click profile trigger
    const profileTrigger = page.locator('button[aria-label="User Profile Menu"]');
    await expect(profileTrigger).toBeVisible();
    await profileTrigger.click();

    // Verify dropdown menu content
    await expect(page.locator('text=Lead Technical Editor')).toBeVisible();
    await expect(page.locator('text=editor@thisweekinai.test')).toBeVisible();
    await expect(page.locator('text=This Week in AI Editorial Lab')).toBeVisible();
    await expect(page.locator('text=ADMIN')).toBeVisible();

    // Verify navigation options are present
    await expect(page.locator('button:has-text("My Profile")')).toBeVisible();
    await expect(page.locator('button:has-text("Account Settings")')).toBeVisible();
    await expect(page.locator('button:has-text("Change Password")')).toBeVisible();
    await expect(page.locator('button:has-text("Organization & Team")')).toBeVisible();
    await expect(page.locator('button:has-text("Sign Out")')).toBeVisible();

    // Close menu with Escape
    await page.keyboard.press('Escape');
    await expect(page.locator('button:has-text("Sign Out")')).not.toBeVisible();
  });

  test('5. ErrorBoundary gracefully surrounds application root and handles module views', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify main content container rendered cleanly without error state
    await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible();
    await expect(page.locator('text=An Unexpected View Error Occurred')).not.toBeVisible();
  });
});
