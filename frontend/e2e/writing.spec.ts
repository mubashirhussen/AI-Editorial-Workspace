import { test, expect } from '@playwright/test';

test.describe('Writing Assistant & Auditor E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept drafts list
    await page.route('**/api/v1/writing/drafts', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'draft-e2e-1',
              title: 'AI Hardware Scaling 2026',
              original_content: 'In order to understand hardware bottlenecks, models were trained by engineers.',
              revised_content: 'In order to understand hardware bottlenecks, models were trained by engineers.',
              readability_score: 64.2,
              word_count: 11,
              status: 'in_progress',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }
          ]),
        });
      } else if (route.request().method() === 'POST') {
        const body = JSON.parse(route.request().postData() || '{}');
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'draft-new-1',
            title: body.title || 'New Draft',
            original_content: body.original_content || 'Sample draft text',
            revised_content: body.original_content || 'Sample draft text',
            status: 'draft',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      }
    });

    // Intercept analyze endpoint
    await page.route('**/api/v1/writing/analyze', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          draft_id: 'draft-e2e-1',
          metrics: {
            word_count: 55,
            sentence_count: 3,
            reading_time_minutes: 0.3,
            flesch_reading_ease: 68.5,
            passive_voice_count: 1,
            filler_word_count: 1,
            complex_sentence_count: 1,
            long_sentence_count: 0,
            jargon_term_count: 0,
            repetition_count: 0,
          },
          overall_feedback: 'Clear technical tone with minor filler phrases and passive constructions.',
          issues: [
            {
              id: 'sug-filler-1',
              category: 'filler',
              severity: 'medium',
              original_text: 'In order to',
              suggested_rewrite: 'To',
              explanation: 'Simplify wordy prepositional phrase.',
              start_char: 0,
              end_char: 11,
              status: 'pending',
            },
            {
              id: 'sug-passive-1',
              category: 'passive_voice',
              severity: 'low',
              original_text: 'models were trained by engineers',
              suggested_rewrite: 'engineers trained models',
              explanation: 'Active voice strengthens clarity.',
              start_char: 45,
              end_char: 77,
              status: 'pending',
            }
          ]
        }),
      });
    });

    // Intercept suggestion accept
    await page.route('**/api/v1/writing/drafts/draft-e2e-1/suggestions/sug-filler-1/accept', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          suggestion_id: 'sug-filler-1',
          original_content: 'In order to understand hardware bottlenecks, models were trained by engineers.',
          revised_content: 'To understand hardware bottlenecks, models were trained by engineers.',
          metrics: {
            word_count: 53,
            sentence_count: 3,
            reading_time_minutes: 0.3,
            flesch_reading_ease: 72.1,
            passive_voice_count: 1,
            filler_word_count: 0,
            complex_sentence_count: 1,
            long_sentence_count: 0,
            jargon_term_count: 0,
            repetition_count: 0,
          }
        }),
      });
    });

    // Intercept suggestion reject
    await page.route('**/api/v1/writing/drafts/draft-e2e-1/suggestions/sug-passive-1/reject', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          suggestion_id: 'sug-passive-1',
          status: 'rejected'
        }),
      });
    });

    // Intercept compare
    await page.route('**/api/v1/writing/drafts/draft-e2e-1/compare', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          draft_id: 'draft-e2e-1',
          original_content: 'In order to understand hardware bottlenecks, models were trained by engineers.',
          revised_content: 'To understand hardware bottlenecks, models were trained by engineers.',
          diff_summary: {
            word_count_delta: -2,
            readability_delta: 3.6,
          },
          suggestions_applied: {
            accepted: 1,
            rejected: 1,
            pending: 0,
          }
        }),
      });
    });
  });

  test('should analyze text, display metrics, accept and reject suggestions, and compare diff', async ({ page }) => {
    await page.goto('/writing');

    // Verify page title
    await expect(page.locator('text=Writing Assistant & Auditor')).toBeVisible();

    // Verify Audit Quality button is present
    const auditBtn = page.getByRole('button', { name: /Audit Quality/i });
    await expect(auditBtn).toBeVisible();
    await auditBtn.click();

    // Check that feedback and metrics are rendered
    await expect(page.locator('text=Clear technical tone with minor filler phrases')).toBeVisible();
    await expect(page.getByText('"In order to"')).toBeVisible();
    await expect(page.getByText('"models were trained by engineers"')).toBeVisible();

    // Verify Accept & Apply button for the first issue
    const acceptButtons = page.getByRole('button', { name: /Accept & Apply/i });
    await expect(acceptButtons.first()).toBeVisible();
    await acceptButtons.first().click();

    // Verify Reject button for the second issue
    const rejectButtons = page.getByRole('button', { name: /Reject/i });
    if (await rejectButtons.count() > 0) {
      await rejectButtons.first().click();
    }

    // Toggle Comparison view
    const compareBtn = page.getByRole('button', { name: /Compare Original vs Revised/i });
    await expect(compareBtn).toBeVisible();
    await compareBtn.click();

    // Verify original and revised diff blocks appear
    await expect(page.locator('text=Original Draft (Immutable)')).toBeVisible();
    await expect(page.locator('text=Revised Draft (Accepted Changes)')).toBeVisible();
  });
});

