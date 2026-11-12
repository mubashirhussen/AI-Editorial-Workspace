import { test, expect } from '@playwright/test';

test.describe('Phase 23 Writing Assistant Workflow & Production Hardening', () => {
  test.beforeEach(async ({ page }) => {
    // Mock user authentication state
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'test-phase23-token');
      localStorage.setItem('user', JSON.stringify({
        id: 'user-p23-1',
        email: 'writer@phase23.ai',
        full_name: 'Lead Phase 23 Writer'
      }));
      localStorage.setItem('active_organization', JSON.stringify({
        id: 'org-p23-1',
        name: 'Phase 23 Editorial Bureau',
        role: 'OWNER'
      }));
    });

    // Mock API routes for deterministic test reliability
    let currentDraft = {
      id: 'draft-p23-alpha',
      title: 'Production Reasoning Architecture Review',
      original_content: 'In order to understand the significance of recent reasoning benchmarks, it is important to note that a large number of tests were conducted by the research team.',
      revised_content: 'In order to understand the significance of recent reasoning benchmarks, it is important to note that a large number of tests were conducted by the research team.',
      content_type: 'editorial_analysis',
      target_audience: 'Technical Leaders & Builders',
      tone: 'authoritative',
      desired_length: 800,
      word_count: 24,
      readability_score: 52.0,
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    let draftsList = [currentDraft];

    await page.route('**/api/v1/writing/drafts**', async (route) => {
      const url = new URL(route.request().url());
      const method = route.request().method();

      if (url.pathname.endsWith('/duplicate')) {
        const cloned = {
          ...currentDraft,
          id: `draft-p23-copy-${Date.now()}`,
          title: `Copy of ${currentDraft.title}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        draftsList.push(cloned);
        await route.fulfill({ status: 201, json: cloned });
        return;
      }

      if (url.pathname.endsWith('/archive')) {
        currentDraft.status = 'archived';
        await route.fulfill({ status: 200, json: currentDraft });
        return;
      }

      if (url.pathname.endsWith('/reopen')) {
        currentDraft.status = 'draft';
        await route.fulfill({ status: 200, json: currentDraft });
        return;
      }

      if (url.pathname.endsWith('/style-check')) {
        await route.fulfill({
          status: 200,
          json: {
            draft_id: currentDraft.id,
            style_score: 88.0,
            violations: []
          }
        });
        return;
      }

      if (url.pathname.endsWith('/versions')) {
        await route.fulfill({
          status: 200,
          json: [
            {
              id: 'ver-1',
              version_number: 1,
              content: currentDraft.original_content,
              change_summary: 'Initial draft snapshot',
              created_at: new Date().toISOString()
            }
          ]
        });
        return;
      }

      if (url.pathname.endsWith('/export')) {
        const fmt = url.searchParams.get('format') || 'markdown';
        await route.fulfill({
          status: 200,
          contentType: fmt === 'html' ? 'text/html' : 'text/plain',
          body: fmt === 'html'
            ? '<html><body><h1>Production Reasoning Architecture Review</h1><p>Escaped content</p></body></html>'
            : `# Production Reasoning Architecture Review\n\n${currentDraft.revised_content}`
        });
        return;
      }

      if (method === 'GET' && url.pathname.endsWith(`/writing/drafts/${currentDraft.id}`)) {
        await route.fulfill({ status: 200, json: currentDraft });
        return;
      }

      if (method === 'GET') {
        await route.fulfill({ status: 200, json: draftsList });
        return;
      }

      if (method === 'POST') {
        const data = JSON.parse(route.request().postData() || '{}');
        const newDraft = {
          id: `draft-new-${Date.now()}`,
          title: data.title || 'Untitled Draft',
          original_content: data.original_content || '',
          revised_content: data.original_content || '',
          content_type: data.content_type || 'editorial_analysis',
          target_audience: data.target_audience || 'General',
          tone: data.tone || 'authoritative',
          desired_length: data.desired_length || 800,
          word_count: data.original_content ? data.original_content.split(/\s+/).length : 0,
          readability_score: 65.0,
          status: 'draft',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        draftsList.push(newDraft);
        currentDraft = newDraft;
        await route.fulfill({ status: 201, json: newDraft });
        return;
      }

      if (method === 'PUT') {
        const data = JSON.parse(route.request().postData() || '{}');
        currentDraft = {
          ...currentDraft,
          title: data.title || currentDraft.title,
          revised_content: data.revised_content || currentDraft.revised_content,
          status: data.status || currentDraft.status,
          updated_at: new Date().toISOString()
        };
        await route.fulfill({ status: 200, json: currentDraft });
        return;
      }

      await route.fallback();
    });

    // Mock analyze endpoint
    await page.route('**/api/v1/writing/analyze', async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          draft_id: currentDraft.id,
          metrics: {
            word_count: 48,
            character_count: 310,
            sentence_count: 2,
            paragraph_count: 1,
            average_sentence_length: 24.0,
            reading_time_minutes: 0.3,
            readability_score: 58.0,
            readability_grade: 'Academic / Complex',
            readability_note: 'Flesch Reading Ease: 58/100'
          },
          overall_feedback: 'Prose is authoritative with opportunities to streamline elongated subordinate clauses.',
          issues: [
            {
              id: 'issue-1',
              category: 'long_sentence',
              severity: 'medium',
              original_text: 'In order to understand the significance of recent reasoning benchmarks...',
              explanation: 'Elongated compound sentence can be split for crisp cadence.',
              suggested_rewrite: 'To evaluate recent reasoning benchmarks, researchers conducted comprehensive tests.',
              status: 'pending',
              confidence: 0.92
            }
          ]
        }
      });
    });

    // Mock selection rewrite endpoint
    await page.route('**/api/v1/writing/rewrite-selection', async (route) => {
      const data = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 200,
        json: {
          operation: data.operation || 'improve_clarity',
          original_text: data.selected_text || '',
          rewritten_text: 'To understand the significance of recent reasoning benchmarks, the research team conducted numerous tests.',
          explanation: 'Eliminated wordy prepositional phrases and converted to direct active cadence.'
        }
      });
    });

    // Mock projects list endpoint
    await page.route('**/api/v1/projects**', async (route) => {
      await route.fulfill({
        status: 200,
        json: {
          items: [
            { id: 'proj-1', title: 'Frontier AI Reasoning Benchmarks', sources: [] }
          ],
          total: 1
        }
      });
    });
  });

  test('completes full end-to-end writing assistant workflow', async ({ page }) => {
    // 1. Navigate to writing page
    await page.goto('/writing');
    await expect(page).toHaveURL(/.*\/writing/);

    // 2. Verify header, deterministic metrics, and capabilities badge
    await expect(page.locator('text=Writing Assistant & Auditor')).toBeVisible();
    await expect(page.locator('text=13 AI Capabilities')).toBeVisible();
    await expect(page.locator('text=Deterministic Metrics:')).toBeVisible();

    // 3. Open Drafts Library Drawer
    const libraryBtn = page.locator('button:has-text("Drafts Library")');
    await expect(libraryBtn).toBeVisible();
    await libraryBtn.click();

    // Verify modal opened
    await expect(page.locator('text=Drafts Library & Document Management')).toBeVisible();
    await expect(page.locator('text=Production Reasoning Architecture Review')).toBeVisible();

    // Close modal
    await page.locator('button:has-text("Close")').click();

    // 4. Create a Rich New Draft
    await page.locator('button:has-text("New Draft")').click();
    await expect(page.locator('text=Create New Writing Draft')).toBeVisible();

    await page.fill('input[placeholder="e.g. Q4 AI Reasoning & Architecture Review"]', 'Autonomous Agentic Systems 2026');
    await page.locator('form select').first().selectOption('technical_explainer');
    await page.fill('textarea[placeholder="Paste preliminary notes or leave blank for a clean document..."]', 'Autonomous agent frameworks are shifting from single prompt loops to multi-tenant state graphs.');
    await page.locator('button:has-text("Create Draft")').click();

    // Verify draft loaded into editor
    await expect(page.locator('input[value="Autonomous Agentic Systems 2026"]')).toBeVisible({ timeout: 5000 });

    // 5. Test AI Rewrite Capabilities and Review Banner
    // Select rewrite operation
    await page.selectOption('select >> nth=0', 'improve_clarity');
    await page.locator('button:has-text("Apply to Full Draft")').click();

    // Verify Suggestion Review Banner appears non-destructively
    await expect(page.locator('text=AI Suggestion Review: Improve Clarity')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Eliminated wordy prepositional phrases and converted to direct active cadence.', { exact: true })).toBeVisible();

    // Accept suggestion
    await page.locator('button:has-text("Accept & Apply Rewrite")').click();
    await expect(page.locator('text=Applied AI suggestion to draft!')).toBeVisible();

    // 6. Test Undo AI Edit
    const undoBtn = page.locator('button:has-text("Undo AI Edit")');
    await expect(undoBtn).toBeVisible();
    await undoBtn.click();
    await expect(page.locator('text=Restored previous draft snapshot!')).toBeVisible();

    // 7. Test Export Dialog
    const exportBtn = page.locator('button:has-text("Export")');
    await expect(exportBtn).toBeVisible();
    await exportBtn.click();

    await expect(page.locator('text=Export Publication-Ready Draft')).toBeVisible();
    await expect(page.locator('text=Markdown (.md)')).toBeVisible();
    await expect(page.locator('text=Word (.docx)')).toBeVisible();
    await expect(page.locator('text=HTML (.html)')).toBeVisible();
    await page.locator('button:has-text("Cancel")').click();

    // 8. Test Quality Audit Action
    const auditBtn = page.locator('button:has-text("Audit Quality")');
    await expect(auditBtn).toBeVisible();
    await auditBtn.click();
    await expect(page.locator('text=Writing quality audit completed.')).toBeVisible({ timeout: 5000 });
  });
});
