import { test, expect } from '@playwright/test';

test.describe('Phase 24 - Full-Platform Cross-Module Integration E2E', () => {
  test.use({ baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Mock standard API routes with deterministic test fixtures
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
                id: 'proj-phase24-1',
                title: 'Quantum Computing & Post-Quantum Cryptography 2026',
                description: 'End-to-end evaluation of NIST standards and crypto-agility timelines.',
                organization_id: 'org-phase24-media',
                sources: [
                  { id: 'src-1', title: 'NIST SP 800-208 Finalized Algorithms', url: 'https://csrc.nist.gov' },
                  { id: 'src-2', title: 'Cloudflare Post-Quantum Hybrid TLS', url: 'https://blog.cloudflare.com' },
                  { id: 'src-3', title: 'Financial Stability Board Quantum Report', url: 'https://fsb.org' },
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

      if (url.includes('/research/projects/proj-phase24-1/brief') || url.includes('/brief')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'brief-phase24-1',
            project_id: 'proj-phase24-1',
            title: 'Research Brief: Post-Quantum Cryptography',
            executive_summary: 'Central banking authorities and NIST mandate crypto-agility roadmaps before 2028.',
            key_findings: [
              'NIST has finalized ML-KEM and ML-DSA post-quantum standards.',
              'Financial infrastructure requires crypto-agility before 2028 to prevent retroactive decryption.',
            ],
            newsletter_angles: [
              { headline: 'Why Post-Quantum Cryptography Is Now an Active Board Priority' },
              { headline: 'Inside the 2028 Crypto-Agility Banking Mandate' },
            ],
            brief_content: {
              what_happened: 'NIST formalized official post-quantum algorithms.',
              why_it_matters: 'Enterprise deployments demand grounded, auditable source citations.',
            },
            created_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes('/writing/drafts') && method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'draft-phase24-1',
              project_id: 'proj-phase24-1',
              title: 'The Post-Quantum Banking Transition',
              content_type: 'editorial_analysis',
              original_content: 'Financial institutions face unprecedented exposure as quantum computers scale.',
              revised_content: 'Financial institutions face unprecedented exposure as quantum computers scale.',
              word_count: 360,
              readability_score: 72.0,
              status: 'draft',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          ])
        });
      }

      if (url.includes('/writing/analyze')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            draft_id: 'draft-phase24-1',
            overall_feedback: 'Draft is well structured.',
            metrics: {
              word_count: 24,
              character_count: 160,
              sentence_count: 1,
              paragraph_count: 1,
              flesch_reading_ease: 52.0,
              flesch_kincaid_grade: 11.2,
              gunning_fog_index: 12.0,
              coleman_liau_index: 10.5,
              smog_index: 11.0,
              automated_readability_index: 10.8,
              style_score: 85.0,
              passive_voice_percentage: 15.0,
              adverb_percentage: 4.0,
              average_sentence_length: 24.0,
              vocabulary_richness: 0.85
            },
            issues_count: 0,
            issues: []
          })
        });
      }

      if (url.includes('/editorial/headlines') && method === 'POST') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 'proj-phase24-1',
            headlines: [
              {
                headline: 'Why Post-Quantum Cryptography Is Now an Active Board Priority',
                editorial_angle: 'System architecture analysis',
                explanation: 'Focuses on factual grounding and operational moats.',
              },
            ],
            recommended_headline: 'Why Post-Quantum Cryptography Is Now an Active Board Priority',
          }),
        });
      }

      if (url.includes('/editorial/generate') && method === 'POST') {
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'ed-phase24-1',
            project_id: 'proj-phase24-1',
            draft_id: 'draft-phase24-1',
            headline: 'Why Post-Quantum Cryptography Is Now an Active Board Priority',
            content: 'The rapid acceleration of Post-Quantum Cryptography has reached an operational inflection point. NIST has formalized ML-KEM [1].',
            word_count: 385,
            source_references: [
              { index: 1, title: 'NIST SP 800-208 Finalized Algorithms', url: 'https://csrc.nist.gov' },
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
              id: 'ed-phase24-1',
              project_id: 'proj-phase24-1',
              headline: 'Why Post-Quantum Cryptography Is Now an Active Board Priority',
              content: 'The rapid acceleration of Post-Quantum Cryptography has reached an operational inflection point...',
              word_count: 385,
              status: 'DRAFT_CREATED',
              source_references: [
                { index: 1, title: 'NIST SP 800-208 Finalized Algorithms', url: 'https://csrc.nist.gov' },
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
            editorial_id: 'ed-phase24-1',
            headline: 'Why Post-Quantum Cryptography Is Now an Active Board Priority',
            markdown_content: '# Why Post-Quantum Cryptography Is Now an Active Board Priority\n\nContent with citations [1].',
            plain_text_content: 'Why Post-Quantum Cryptography Is Now an Active Board Priority\n\nContent with citations [1].',
            html_content: '<h1>Why Post-Quantum Cryptography Is Now an Active Board Priority</h1>',
            json_content: JSON.stringify({ id: 'ed-phase24-1' }),
            format: 'markdown',
            word_count: 385,
            exported_at: new Date().toISOString(),
          }),
        });
      }

      // Default passthrough
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, items: [] }),
      });
    });
  });

  test('1. Cross-Module Navigation: Editorial Studio and Project Loading', async ({ page }) => {
    await page.goto('/editorial');
    await expect(page.locator('h2')).toContainText('Editorial Studio');
    await expect(page.locator('text=300–500 Words').first()).toBeVisible();
    await expect(page.locator('select').first()).toContainText('Quantum Computing & Post-Quantum Cryptography 2026');
  });

  test('2. Cross-Module Navigation: Writing Assistant & Deterministic Analysis', async ({ page }) => {
    await page.goto('/writing');
    await expect(page).toHaveURL(/.*\/writing/);
    await expect(page.locator('text=Writing Assistant & Auditor')).toBeVisible();
    await expect(page.locator('text=13 AI Capabilities')).toBeVisible();
  });

  test('3. Cross-Module Navigation: Editorial Review and Quality Controls', async ({ page }) => {
    await page.goto('/editorial');
    await expect(page.locator('text=Editorial Parameters')).toBeVisible();
    await expect(page.locator('text=Target Audience')).toBeVisible();
    await expect(page.locator('text=Editorial Tone')).toBeVisible();
  });
});
