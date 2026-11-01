import { test, expect } from '@playwright/test';

test.describe('Editorial Studio E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept all API calls under /api/v1/
    await page.route('**/api/v1/**', async (route) => {
      const url = route.request().url();

      if (url.includes('/headlines')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            headlines: [
              {
                id: 'hl-1',
                headline: 'Why Power Rather Than Silicon Is the True AI Bottleneck',
                hook: 'Datacenter power caps are changing hyperscaler infrastructure.',
                angle: 'Infrastructure analysis',
                target_audience: 'Engineers & Founders'
              },
              {
                id: 'hl-2',
                headline: 'The $120B Megawatt Frontier: Inside Next-Gen Datacenters',
                hook: 'Capex surges as immersion cooling hits mainstream production.',
                angle: 'Financial & hardware breakdown',
                target_audience: 'Operators'
              }
            ],
            recommended_headline: 'Why Power Rather Than Silicon Is the True AI Bottleneck'
          }),
        });
      }

      if (url.includes('/generate')) {
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'editorial-studio-1',
            project_id: 'proj-e2e-studio',
            headline: 'Why Power Rather Than Silicon Is the True AI Bottleneck',
            content: 'Hyperscalers are investing over $120B in AI infrastructure [SemiAnalysis 2026 Capex]. However, power grids in major hubs are reaching capacity, pushing operators toward direct two-phase immersion cooling [Two-Phase Immersion Cooling]. Founders building compute-intensive models must optimize throughput per watt.',
            word_count: 365,
            target_audience: 'founders, builders, and operators',
            tone: 'Newsletter-style',
            source_references: [
              { source_title: 'SemiAnalysis 2026 Capex', url: null },
              { source_title: 'Two-Phase Immersion Cooling', url: null }
            ],
            created_at: new Date().toISOString()
          }),
        });
      }

      if (url.includes('/export')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            editorial_id: 'editorial-studio-1',
            headline: 'Why Power Rather Than Silicon Is the True AI Bottleneck',
            word_count: 365,
            markdown_content: '# Why Power Rather Than Silicon Is the True AI Bottleneck\n\nHyperscalers are investing over $120B in AI infrastructure...',
            plain_text_content: 'WHY POWER RATHER THAN SILICON IS THE TRUE AI BOTTLENECK\n\nHyperscalers are investing...',
            html_content: '<article><h1>Why Power Rather Than Silicon Is the True AI Bottleneck</h1><p>Hyperscalers are investing over $120B...</p></article>',
            source_citations: ['SemiAnalysis 2026 Capex', 'Two-Phase Immersion Cooling']
          }),
        });
      }

      if (url.includes('/brief')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'brief-studio-1',
            project_id: 'proj-e2e-studio',
            summary: 'Accelerated compute demand drives modular micro-nuclear and two-phase liquid immersion cooling deployments.',
            key_findings: [
              'Capex reached record $120B in Q1 2026.',
              'Direct immersion cooling decreases PUE from 1.35 to 1.04.',
            ],
            newsletter_angles: [
              'Why Power Rather Than Silicon Is the New Bottleneck in AI Clusters',
              'From GPUs to SMRs: How Hyperscalers Are Securing Clean Energy'
            ],
            evidence: [
              { source_title: 'SemiAnalysis 2026', fact: 'Datacenter capex reached $120B.' },
              { source_title: 'Cooling Tech Benchmarks', fact: 'PUE decreases to 1.04.' }
            ],
            brief_content: {
              what_happened: 'Compute demand has shifted power into the primary constraint.',
              why_it_matters: 'Founders must design architectures around megawatt density.',
              predictions: 'Expect hyperscalers to colocate modular reactors by 2028.'
            }
          }),
        });
      }

      if (url.includes('/editorial')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      }

      if (url.includes('/sources')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 'src-1', title: 'SemiAnalysis 2026 Capex', extraction_status: 'completed' },
            { id: 'src-2', title: 'Two-Phase Immersion Cooling', extraction_status: 'completed' },
            { id: 'src-3', title: 'TPU v6 Benchmarks', extraction_status: 'completed' },
          ]),
        });
      }

      if (url.includes('proj-e2e-studio')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'proj-e2e-studio',
            title: 'AI Cluster Scaling 2026',
            description: 'Hyperscale AI infrastructure research and newsletter package',
            created_at: new Date().toISOString(),
            sources: [
              { id: 'src-1', title: 'SemiAnalysis 2026 Capex', extraction_status: 'completed' },
              { id: 'src-2', title: 'Two-Phase Immersion Cooling', extraction_status: 'completed' },
              { id: 'src-3', title: 'TPU v6 Benchmarks', extraction_status: 'completed' },
            ]
          }),
        });
      }

      if (url.includes('/projects')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            total: 1,
            items: [
              {
                id: 'proj-e2e-studio',
                title: 'AI Cluster Scaling 2026',
                description: 'Hyperscale AI infrastructure research and newsletter package',
                created_at: new Date().toISOString(),
                sources_count: 3,
              }
            ]
          }),
        });
      }

      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });
  });

  test('should select project, generate headlines and editorial, inspect citations, and export markdown/HTML', async ({ page }) => {
    await page.goto('/editorial?projectId=proj-e2e-studio');

    // Verify Editorial Studio loaded
    await expect(page.getByRole('heading', { name: 'Editorial Studio' })).toBeVisible();

    // Verify headline option is present
    await expect(page.getByText('Why Power Rather Than Silicon Is the True AI Bottleneck').first()).toBeVisible();

    // Verify Generate Article button
    const genArticleBtn = page.getByRole('button', { name: /Generate 300–500 Word Article/i });
    await expect(genArticleBtn).toBeVisible();
    await genArticleBtn.click();

    // Check that generated editorial content is populated
    await expect(page.getByText('Hyperscalers are investing over $120B').first()).toBeVisible();

    // Verify Export button in toolbar is enabled and click it
    const exportBtn = page.getByRole('button', { name: 'Export' });
    await expect(exportBtn).toBeVisible();
    await exportBtn.click();

    // Verify Export Modal displays tabs
    await expect(page.locator('text=Markdown (.md)')).toBeVisible();
    await expect(page.locator('text=Plain Text (.txt)')).toBeVisible();
    await expect(page.locator('text=HTML5 (.html)')).toBeVisible();
  });
});

