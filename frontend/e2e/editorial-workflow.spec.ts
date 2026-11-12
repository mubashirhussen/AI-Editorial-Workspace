import { test, expect } from '@playwright/test';

test.describe('Phase 21 - Editorial Studio End-User Workflow & Journey E2E', () => {
  test.use({ baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Mock standard API routes with deterministic test data
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
                id: 'proj-phase21-1',
                title: 'Autonomous AI Verification & Governance',
                description: 'End-to-end evaluation of factual reasoning and citations',
                organization_id: 'org-test-1',
                sources: [
                  { id: 'src-1', title: 'DeepSeek-R1 Technical Report', url: 'https://example.com/r1' },
                  { id: 'src-2', title: 'Model Context Protocol Spec', url: 'https://example.com/mcp' },
                  { id: 'src-3', title: 'Attention Is All You Need', url: 'https://example.com/attn' },
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

      if (url.includes('/research/projects/proj-phase21-1/brief') || url.includes('/brief')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'brief-phase21-1',
            project_id: 'proj-phase21-1',
            executive_summary: 'Frontier AI reasoning models require deterministic verification layers.',
            key_findings: [
              'Verification density improves factual citation fidelity by 44%.',
              'Deterministic checks eliminate multi-turn hallucination accumulation.',
            ],
            newsletter_angles: [
              { headline: 'Why Verification Architecture Is the True Moat for Enterprise AI' },
              { headline: 'From RAG to Grounded Proof: Inside Modern Fact-Checking Pipelines' },
            ],
            brief_content: {
              what_happened: 'Frontier models are shifting toward test-time reasoning and verification.',
              why_it_matters: 'Enterprise deployments demand grounded, auditable source citations.',
            },
            created_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes('/editorial/headlines') && method === 'POST') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 'proj-phase21-1',
            headlines: [
              {
                headline: 'Why Verification Architecture Is the True Moat for Enterprise AI',
                editorial_angle: 'System architecture analysis',
                explanation: 'Focuses on factual grounding and operational moats.',
              },
              {
                headline: 'The Proof-First Paradigm: How Newsletter Desks Automate Accuracy',
                editorial_angle: 'Publishing workflow transition',
                explanation: 'Examines human-in-the-loop auditability for operators.',
              },
            ],
            recommended_headline: 'Why Verification Architecture Is the True Moat for Enterprise AI',
          }),
        });
      }

      if (url.includes('/editorial/generate') && method === 'POST') {
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'ed-phase21-1',
            project_id: 'proj-phase21-1',
            draft_id: 'draft-phase21-1',
            headline: 'Why Verification Architecture Is the True Moat for Enterprise AI',
            content: 'The rapid acceleration of Autonomous AI Verification has reached an operational inflection point. For founders, builders, and operators, recent benchmark shifts highlight a clear transformation: models without deterministic verification degrade under scale. Specifically, DeepSeek-R1 technical disclosures [1] demonstrate verifiable inference benefits. Furthermore, verified testing confirms MCP protocol integration [2] provides reliable context isolation.\n\n### What Happened\n\nKey reports announce substantial milestones across model capabilities and infrastructural tooling. Synthesizing data across 3 sources confirms that frontier labs are prioritizing operational predictability over pure theoretical benchmark gains.\n\n### The Bottom Line\n\nEnterprise AI adoption requires proof-backed systems rather than hallucinated fluency.',
            word_count: 385,
            source_references: [
              { index: 1, title: 'DeepSeek-R1 Technical Report', url: 'https://example.com/r1' },
              { index: 2, title: 'Model Context Protocol Spec', url: 'https://example.com/mcp' },
            ],
            status: 'DRAFT_CREATED',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      }

      if ((url.includes('/editorial?') || url.endsWith('/editorial')) && method === 'GET' && !url.includes('/headlines') && !url.includes('/dashboard') && !url.includes('/ai-review')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'ed-phase21-1',
              project_id: 'proj-phase21-1',
              headline: 'Why Verification Architecture Is the True Moat for Enterprise AI',
              content: 'The rapid acceleration of Autonomous AI Verification has reached an operational inflection point...',
              word_count: 385,
              status: 'DRAFT_CREATED',
              source_references: [
                { index: 1, title: 'DeepSeek-R1 Technical Report', url: 'https://example.com/r1' },
              ],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ]),
        });
      }

      if (url.includes('/export')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            editorial_id: 'ed-phase21-1',
            headline: 'Why Verification Architecture Is the True Moat for Enterprise AI',
            markdown_content: '# Why Verification Architecture Is the True Moat for Enterprise AI\n\n*Published via This Week in AI Editorial Workspace* | *Word Count: 385 words*\n\nThe rapid acceleration of Autonomous AI Verification...',
            plain_text_content: 'WHY VERIFICATION ARCHITECTURE IS THE TRUE MOAT FOR ENTERPRISE AI\n\nWord Count: 385 words\n\nThe rapid acceleration of Autonomous AI Verification...',
            html_content: '<h1>Why Verification Architecture Is the True Moat for Enterprise AI</h1><p>The rapid acceleration of Autonomous AI Verification...</p>',
            json_content: JSON.stringify({
              id: 'ed-phase21-1',
              headline: 'Why Verification Architecture Is the True Moat for Enterprise AI',
              word_count: 385,
              status: 'DRAFT_CREATED',
            }, null, 2),
            format: 'markdown',
            word_count: 385,
            exported_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes('/ai-review')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            evaluated_at: new Date().toISOString(),
            word_count_compliance: { is_compliant: true, word_count: 385, range: '300-500' },
            readability_score: { f陽: 65, grade_level: 'Grade 10' },
            citations_check: { found: 2, invalid: [] },
            uncertainties: [],
            missing_sections: [],
          }),
        });
      }

      if (url.includes('/reviews') && method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      }

      if (url.includes('/dashboard/stats')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            pending_human_reviews: 1,
            approved_editorials: 0,
            changes_requested: 0,
            finalized_editorials: 0,
            total_editorials: 1,
            recent_activity: [],
          }),
        });
      }

      // Default passthrough for any other calls
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });
  });

  test('1. Application Navigation & Editorial Studio Initial Load', async ({ page }) => {
    await page.goto('/editorial');
    await expect(page.locator('h2')).toContainText('Editorial Studio');
    await expect(page.locator('text=300–500 Words').first()).toBeVisible();
  });

  test('2. Project Context & Brief Loading', async ({ page }) => {
    await page.goto('/editorial');
    await expect(page.locator('select')).toContainText('Autonomous AI Verification & Governance');
    await expect(page.locator('text=Sources Ingested')).toBeVisible();
    await expect(page.locator('text=Brief Synthesized')).toBeVisible();
  });

  test('3. Headline Selection & Parameter Controls', async ({ page }) => {
    await page.goto('/editorial');
    await expect(page.locator('text=Editorial Parameters')).toBeVisible();
    await expect(page.locator('text=Target Audience')).toBeVisible();
    await expect(page.locator('text=Editorial Tone')).toBeVisible();
  });

  test('4. Editorial Generation & Content Display', async ({ page }) => {
    await page.goto('/editorial');
    const generateBtn = page.locator('button:has-text("Draft Newsletter Article"), button:has-text("Generate Article")').first();
    if (await generateBtn.isVisible()) {
      await generateBtn.click();
      await expect(page.locator('text=The rapid acceleration')).toBeVisible({ timeout: 5000 });
    }
  });

  test('5. View Mode Switching (Editor, Preview, Review)', async ({ page }) => {
    await page.goto('/editorial');
    await page.locator('button:has-text("Newsletter Preview")').first().click();
    await expect(page.locator('text=This Week in AI').first()).toBeVisible();

    await page.locator('button:has-text("Review & Workflow")').first().click();
    await expect(page.locator('text=Review').first()).toBeVisible();

    await page.locator('button:has-text("Editor")').first().click();
    await expect(page.locator('text=Editorial Parameters')).toBeVisible();
  });

  test('6. Export Menu & Multi-Format Options (MD, TXT, HTML, JSON)', async ({ page }) => {
    await page.goto('/editorial');
    const exportBtn = page.locator('button:has-text("Export")').first();
    await expect(exportBtn).toBeVisible();
    if (await exportBtn.isEnabled()) {
      await exportBtn.click();
      await expect(page.locator('text=Export Newsletter Edition')).toBeVisible();
      await expect(page.locator('button:has-text("Markdown (.md)")')).toBeVisible();
      await expect(page.locator('button:has-text("Plain Text (.txt)")')).toBeVisible();
      await expect(page.locator('button:has-text("HTML5 (.html)")')).toBeVisible();
      await expect(page.locator('button:has-text("JSON (.json)")')).toBeVisible();
    }
  });
});
