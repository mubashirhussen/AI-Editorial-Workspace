import { test, expect } from '@playwright/test';

test.describe('Phase 22 - Research Assistant End-to-End Workflow & Evidence Traceability', () => {
  test.use({ baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    let projectStatus = 'active';
    let briefVersion = 1;
    let briefData: any = {
      id: 'brief-phase22-test',
      project_id: 'proj-phase22-1',
      version: 1,
      is_user_edited: false,
      user_notes: 'Initial synthetic baseline generated from 3 sources.',
      executive_summary: 'Test-time compute and verifiable inference frameworks dramatically improve factual reliability in production LLMs.',
      key_findings: [
        'Deterministic verification layers eliminate multi-turn hallucination drift.',
        'Verifiable citation density improves grounding fidelity by 44%.',
        'Contradictory benchmarks demonstrate synthetic token over-optimization risks.',
      ],
      newsletter_angles: [
        {
          headline: 'Why Grounded Verification Is the True Moat for Enterprise AI Desks',
          angle: 'Architectural analysis of test-time reasoning and fact checking.',
        },
        {
          headline: 'From RAG to Grounded Proof: Eliminating Hallucinations at Scale',
          angle: 'Engineering deep-dive into source quotation verification.',
        },
      ],
      brief_content: {
        what_happened: 'Frontier AI labs published new architectures integrating programmatic verification loops into inference pipelines.',
        why_it_matters: 'Publishing desks cannot tolerate unverified assertions; source-backed grounding is mandatory.',
        key_quotes: [
          '"Verifiable test-time compute yields deterministic grounding across multi-source synthesis." - DeepSeek Technical Team',
        ],
      },
      evidence: [
        {
          id: 'ev-1',
          claim: 'Test-time compute improves factual grounding fidelity by 44%.',
          source_id: 'src-phase22-1',
          source_title: 'DeepSeek-R1 Technical Report',
          quote: 'We observe a 44% relative gain in factual consistency benchmarks with verifiable reasoning chains.',
          verification_status: 'SUPPORTED',
          confidence_score: 0.96,
        },
        {
          id: 'ev-2',
          claim: 'Synthetic token over-optimization yields degraded real-world reasoning.',
          source_id: 'src-phase22-2',
          source_title: 'Factual Grounding in Large Language Models',
          quote: 'Overfitting to benchmark reward models produces superficial reasoning tokens without semantic rigor.',
          verification_status: 'CONTRADICTED',
          confidence_score: 0.89,
        },
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    const mockSources = [
      {
        id: 'src-phase22-1',
        project_id: 'proj-phase22-1',
        title: 'DeepSeek-R1 Technical Report',
        url: 'https://arxiv.org/abs/2501.12948',
        source_type: 'url',
        extraction_status: 'completed',
        content_preview: 'In this work we introduce DeepSeek-R1, focusing on verifiable reasoning...',
        raw_content: 'Full academic paper detailing verifiable test-time compute, reasoning token rewards, and cross-source consistency evaluations.',
        metadata: { word_count: 4200, domain: 'arxiv.org' },
        created_at: new Date().toISOString(),
      },
      {
        id: 'src-phase22-2',
        project_id: 'proj-phase22-1',
        title: 'Factual Grounding in Large Language Models',
        url: 'https://example.com/grounding-study.pdf',
        source_type: 'pdf',
        extraction_status: 'completed',
        content_preview: 'A systematic empirical evaluation of hallucination rates across structured editorial workflows...',
        raw_content: 'Comprehensive analysis of hallucination mechanics, multi-hop claim verification, and epistemic confidence scoring.',
        metadata: { word_count: 3100, file_size: 1048576 },
        created_at: new Date().toISOString(),
      },
      {
        id: 'src-phase22-3',
        project_id: 'proj-phase22-1',
        title: 'Model Context Protocol Specification',
        url: 'https://modelcontextprotocol.io/specification',
        source_type: 'url',
        extraction_status: 'completed',
        content_preview: 'The Model Context Protocol standardizes how applications provide context to LLMs...',
        raw_content: 'Protocol specification detailing server-client communications, tool definitions, resource schemas, and strict sandboxing.',
        metadata: { word_count: 2800, domain: 'modelcontextprotocol.io' },
        created_at: new Date().toISOString(),
      },
    ];

    const projectDetail = {
      id: 'proj-phase22-1',
      title: 'Autonomous AI Verification & Grounding',
      topic: 'Test-Time Compute & Verification',
      research_objective: 'Evaluate factual reasoning architectures and citation grounding in enterprise systems.',
      target_audience: 'founders, builders, and operators',
      research_scope: 'Q4 2025 - Q1 2026 technical releases',
      keywords: ['reasoning', 'verification', 'citations', 'grounding'],
      status: projectStatus,
      created_at: new Date().toISOString(),
      sources: mockSources,
    };

    // Setup network mock intercepts
    await page.route('**/api/v1/**', async (route) => {
      const url = route.request().url();
      const method = route.request().method();

      // Project Archive & Reopen
      if (url.includes('/archive') && method === 'POST') {
        projectStatus = 'archived';
        projectDetail.status = 'archived';
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...projectDetail,
            status: 'archived',
            updated_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes('/reopen') && method === 'POST') {
        projectStatus = 'active';
        projectDetail.status = 'active';
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...projectDetail,
            status: 'active',
            updated_at: new Date().toISOString(),
          }),
        });
      }

      // Evidence Alignment
      if (url.includes('/evidence')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(briefData.evidence),
        });
      }

      // Research Brief History (returns direct array)
      if (url.includes('/brief/history') && method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'brief-v1',
              project_id: 'proj-phase22-1',
              version: 1,
              executive_summary: briefData.executive_summary,
              user_notes: 'Initial automated synthesis.',
              is_user_edited: false,
              created_at: new Date(Date.now() - 3600000).toISOString(),
            },
            ...(briefVersion > 1 ? [{
              id: 'brief-v2',
              project_id: 'proj-phase22-1',
              version: 2,
              executive_summary: briefData.executive_summary,
              user_notes: briefData.user_notes,
              is_user_edited: true,
              created_at: new Date().toISOString(),
            }] : []),
          ]),
        });
      }

      // Research Brief Export
      if (url.includes('/brief/export') && method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            project_id: 'proj-phase22-1',
            brief_id: 'brief-phase22-test',
            title: 'Autonomous AI Verification & Grounding',
            markdown_content: `# Autonomous AI Verification & Grounding - Research Brief (v${briefVersion})\n\n## Executive Summary\n${briefData.executive_summary}\n\n## Key Findings\n- ${briefData.key_findings.join('\n- ')}`,
            plain_text_content: `AUTONOMOUS AI VERIFICATION & GROUNDING - BRIEF (v${briefVersion})\n\nEXECUTIVE SUMMARY:\n${briefData.executive_summary}\n\nKEY FINDINGS:\n* ${briefData.key_findings.join('\n* ')}`,
            json_content: JSON.stringify(briefData, null, 2),
            format: 'markdown',
            exported_at: new Date().toISOString(),
          }),
        });
      }

      // Research Brief CRUD / Synthesize
      if (url.includes('/brief') || url.includes('/synthesize')) {
        if (method === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(briefData),
          });
        }
        if (method === 'PUT') {
          const body = route.request().postDataJSON() || {};
          briefVersion = 2;
          briefData = {
            ...briefData,
            version: briefVersion,
            is_user_edited: true,
            executive_summary: body.executive_summary || briefData.executive_summary,
            user_notes: body.user_notes || briefData.user_notes,
            brief_content: {
              ...briefData.brief_content,
              what_happened: body.what_happened || briefData.brief_content.what_happened,
              why_it_matters: body.why_it_matters || briefData.brief_content.why_it_matters,
            },
            updated_at: new Date().toISOString(),
          };
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(briefData),
          });
        }
        if (method === 'POST') {
          return route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify(briefData),
          });
        }
      }

      // Project Sources
      if (url.includes('/sources')) {
        if (url.includes('/retry') && method === 'POST') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'src-phase22-1',
              status: 'completed',
              extraction_status: 'completed',
              message: 'Source re-extraction succeeded',
            }),
          });
        }
        if (method === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockSources),
          });
        }
        if (method === 'POST') {
          return route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'src-phase22-new',
              project_id: 'proj-phase22-1',
              title: 'New Discovered Ingested Source',
              url: 'https://example.com/new-source',
              source_type: 'url',
              extraction_status: 'completed',
              content_preview: 'Verified ingested article content...',
              created_at: new Date().toISOString(),
            }),
          });
        }
      }

      // Single Project vs Projects List
      if (url.includes('/projects/proj-phase22-1')) {
        if (method === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(projectDetail),
          });
        }
      }

      if (url.includes('/projects') && method === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [projectDetail],
            total: 1,
            skip: 0,
            limit: 50,
          }),
        });
      }

      if (url.includes('/projects') && method === 'POST') {
        const body = route.request().postDataJSON() || {};
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'proj-phase22-new',
            title: body.title || 'Generative Code Synthesis 2026',
            topic: body.topic || 'Agentic Refactoring Systems',
            research_objective: body.research_objective || 'Investigate enterprise agent reliability.',
            target_audience: body.target_audience || 'CTOs and senior software architects',
            research_scope: body.research_scope || '2026 Models',
            keywords: body.keywords || ['reasoning', 'verification'],
            status: 'active',
            created_at: new Date().toISOString(),
            sources: [],
          }),
        });
      }

      return route.continue();
    });
  });

  test('E2E Flow: Project metadata, source review, brief synthesis, evidence filtering, editing, versioning, export & editorial studio handoff', async ({ page }) => {
    // 1. Visit Research Assistant
    await page.goto('/research');
    await expect(page).toHaveTitle(/Editorial AI/i);

    // 2. Verify workspace header & project select
    await expect(page.locator('text=Scholarly Workspace')).toBeVisible({ timeout: 10000 });
    const projectSelect = page.locator('select').first();
    await expect(projectSelect).toHaveValue('proj-phase22-1');

    // Verify source badge count (3 Verified Sources)
    await expect(page.locator('text=3 Verified Sources')).toBeVisible({ timeout: 10000 });

    // 3. Inspect the Research Brief tabs and views
    const briefTab = page.locator('button:has-text("Research Brief")').first();
    await expect(briefTab).toBeVisible();
    await briefTab.click();

    // Verify Executive Summary rendered
    await expect(page.locator('text=Test-time compute and verifiable inference frameworks')).toBeVisible();

    // 4. Test In-Place Brief Editor
    const editBriefBtn = page.locator('button[title="Edit research brief sections"]');
    await expect(editBriefBtn).toBeVisible();
    await editBriefBtn.click();

    // Verify editor mode is open
    const execSummaryTextarea = page.locator('label:has-text("Executive Summary") + textarea');
    await expect(execSummaryTextarea).toBeVisible();

    // Edit Executive Summary and User Notes
    await execSummaryTextarea.fill('Updated Executive Summary: Test-time compute verified with deterministic epistemic guardrails.');
    const userNotesInput = page.locator('textarea[placeholder*="investigative context"]');
    await userNotesInput.fill('Phase 22 audit notes: Validated against 3 authoritative sources.');

    // Save changes
    const saveBriefBtn = page.locator('button:has-text("Save Brief Changes")');
    await expect(saveBriefBtn).toBeVisible();
    await saveBriefBtn.click();

    // Check returning to view mode
    await expect(page.locator('button[title="Edit research brief sections"]')).toBeVisible({ timeout: 5000 });

    // 5. Version History Inspection Modal
    const versionHistoryBtn = page.locator('button[title*="View brief version lineage"]');
    await expect(versionHistoryBtn).toBeVisible();
    await versionHistoryBtn.click();

    // Verify Version Lineage modal rendered
    await expect(page.locator('text=Research Brief Version Lineage')).toBeVisible();
    await expect(page.locator('text=Version 1')).toBeVisible();
    
    // Close Version History modal using close icon
    const closeVersionModalBtn = page.locator('div.fixed button:has(svg.lucide-x)').first();
    await closeVersionModalBtn.click();
    await expect(page.locator('text=Research Brief Version Lineage')).not.toBeVisible();

    // 6. Test Multi-Format Brief Export Modal
    const exportBtn = page.locator('button[title*="Export structured research brief"]');
    await expect(exportBtn).toBeVisible();
    await exportBtn.click();

    // Verify Export Modal
    await expect(page.locator('text=Export Structured Research Brief')).toBeVisible();
    await expect(page.locator('button:has-text("Markdown (.md)")')).toBeVisible();
    await expect(page.locator('button:has-text("Plain Text (.txt)")')).toBeVisible();
    await expect(page.locator('button:has-text("JSON Schema (.json)")')).toBeVisible();

    // Switch tabs in export modal
    const txtTab = page.locator('button:has-text("Plain Text (.txt)")');
    await txtTab.click();
    await expect(page.locator('pre:has-text("AUTONOMOUS AI VERIFICATION")')).toBeVisible();

    const jsonTab = page.locator('button:has-text("JSON Schema (.json)")');
    await jsonTab.click();
    await expect(page.locator('pre:has-text("brief-phase22-test")')).toBeVisible();

    // Close Export Modal
    const closeExportBtn = page.locator('div.fixed button:has(svg.lucide-x)').first();
    await closeExportBtn.click();
    await expect(page.locator('text=Export Structured Research Brief')).not.toBeVisible();

    // 7. Verify Evidence Alignment Tab
    const evidenceTab = page.locator('button:has-text("Evidence Alignment")');
    await expect(evidenceTab).toBeVisible();
    await evidenceTab.click();

    // Check evidence header and status tags
    await expect(page.locator('text=Evidence Alignment & Grounding Verification')).toBeVisible();
    await expect(page.locator('text=SUPPORTED').first()).toBeVisible();

    // 8. Test Project Archive & Reopen Lifecycle
    const archiveBtn = page.locator('button:has-text("Archive")');
    await expect(archiveBtn).toBeVisible();
    await archiveBtn.click();

    // After archiving, button changes to "Reopen Project"
    await expect(page.locator('button:has-text("Reopen Project")')).toBeVisible({ timeout: 5000 });

    // Reopen project
    const reopenBtn = page.locator('button:has-text("Reopen Project")');
    await reopenBtn.click();
    await expect(page.locator('button:has-text("Archive")')).toBeVisible({ timeout: 5000 });

    // 9. Editorial Studio Direct Handoff
    const editorialBtn = page.locator('button:has-text("Editorial Studio")').first();
    await expect(editorialBtn).toBeVisible();
    await editorialBtn.click();

    // Verify browser navigates to Editorial Studio with projectId param
    await page.waitForURL(/.*\/editorial\?projectId=proj-phase22-1.*/, { timeout: 10000 });
    expect(page.url()).toContain('/editorial?projectId=proj-phase22-1');
  });

  test('Create New Project Modal: Validates rich fields and submission', async ({ page }) => {
    await page.goto('/research');
    await expect(page).toHaveTitle(/Editorial AI/i);

    // Wait for Scholarly Workspace to load completely
    await expect(page.locator('text=Scholarly Workspace')).toBeVisible({ timeout: 10000 });

    // Click "+" button to open New Project Modal
    const newProjectBtn = page.locator('button[title="Create new research project"]');
    await expect(newProjectBtn).toBeVisible({ timeout: 10000 });
    await newProjectBtn.click();

    // Verify modal inputs
    await expect(page.locator('text=Create Research Project')).toBeVisible();
    
    // Fill out form
    await page.fill('input[placeholder*="Autonomous AI Verification"]', 'Generative Code Synthesis 2026');
    await page.fill('input[placeholder*="Test-Time Compute"]', 'Agentic Refactoring Systems');
    await page.locator('div.fixed select').selectOption('founders, builders, and operators');
    await page.fill('textarea[placeholder*="What core operational question"]', 'Investigate enterprise agent reliability and determinism.');
    await page.fill('input[placeholder*="Q4 2025 – 2026 releases"]', '2026 Models');
    await page.fill('input[placeholder*="reasoning, citation"]', 'agent, refactoring, benchmark');

    // Submit form
    const createBtn = page.locator('button:has-text("Create Project")');
    await createBtn.click();

    // Verify modal closes
    await expect(page.locator('text=Create Research Project')).not.toBeVisible({ timeout: 5000 });
  });
});
