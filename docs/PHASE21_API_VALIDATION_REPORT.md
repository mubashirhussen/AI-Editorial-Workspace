# Phase 21 — API Validation & Security Dependency Report

**Module:** Editorial Studio & Review Workflow APIs  
**Base Route:** `/api/v1/editorial` & `/api/v1/editorial/{id}/*`  
**Authentication Standard:** HTTP Bearer JWT (`Depends(get_current_user)`)  
**Tenant Scoping Standard:** Organization Membership Check (`check_project_tenant_access`)  
**Test Framework:** Pytest (`pytest-asyncio`, `httpx.AsyncClient`)  

---

## 1. Endpoint Inventory & Contract Audit

| HTTP Method | Route | Description | Auth Dependency | Tenant Isolation | Error Codes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/editorial/headlines` | Generate candidate newsletter headlines & angles | `Depends(get_current_user)` | `check_project_tenant_access(..., "view")` | 400, 401, 403, 404 |
| `POST` | `/api/v1/editorial/generate` | Synthesize 300–500 word article draft | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` | 400, 401, 403, 404 |
| `POST` | `/api/v1/editorial` | Create manual editorial edition | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` | 400, 401, 403, 404 |
| `GET` | `/api/v1/editorial` | List editorials for project / org | `Depends(get_current_user)` | `check_project_tenant_access` + org query filter | 401, 403, 404 |
| `GET` | `/api/v1/editorial/{id}` | Retrieve specific editorial edition | `Depends(get_current_user)` | `check_project_tenant_access(..., "view")` | 401, 403, 404 |
| `PUT` | `/api/v1/editorial/{id}` | Update draft content / headline | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` + **Immutability Lock** | 400, 401, 403, 404, **409** |
| `DELETE` | `/api/v1/editorial/{id}` | Delete editorial edition | `Depends(get_current_user)` | `check_project_tenant_access(..., "admin")` + **Immutability Lock** | 401, 403, 404, **409** |
| `GET` | `/api/v1/editorial/{id}/export` | Multi-format export (`md`, `txt`, `html`, `json`) | `Depends(get_current_user)` | `check_project_tenant_access(..., "view")` | 400, 401, 403, 404 |
| `GET` | `/api/v1/editorial/dashboard/stats` | Editorial review metrics & activity | `Depends(get_current_user)` | Filtered by `user_org_ids` | 401 |
| `POST` | `/api/v1/editorial/{id}/ai-review` | Run automated AI quality review | `Depends(get_current_user)` | `check_project_tenant_access(..., "view")` | 401, 403, 404 |
| `POST` | `/api/v1/editorial/{id}/reviews` | Submit peer review | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` + Server Reviewer Identity | 400, 401, 403, 404 |
| `GET` | `/api/v1/editorial/{id}/reviews` | List peer reviews | `Depends(get_current_user)` | `check_project_tenant_access(..., "view")` | 401, 403, 404 |
| `POST` | `/api/v1/editorial/{id}/comments` | Add inline review comment | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` + Server Author Identity | 400, 401, 403, 404 |
| `GET` | `/api/v1/editorial/{id}/comments` | List review comments | `Depends(get_current_user)` | `check_project_tenant_access(..., "view")` | 401, 403, 404 |
| `POST` | `/api/v1/editorial/{id}/request-changes` | Set status to `CHANGES_REQUESTED` | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` | 400, 401, 403, 404 |
| `POST` | `/api/v1/editorial/{id}/approve` | Approve editorial for publication | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` + No Self-Approval Rule | 400, 401, 403, 404 |
| `POST` | `/api/v1/editorial/{id}/finalize` | Lock edition for distribution | `Depends(get_current_user)` | `check_project_tenant_access(..., "admin")` + Status Transition | 400, 401, 403, 404 |
| `POST` | `/api/v1/editorial/{id}/revision` | Create new version branch | `Depends(get_current_user)` | `check_project_tenant_access(..., "edit")` | 400, 401, 403, 404 |

---

## 2. Security Dependency Implementation Details

### 2.1 Multi-Tenant Access Verification
Every route accessing a project or editorial executes `check_project_tenant_access`:
```python
def check_project_tenant_access(
    db: Session,
    project: ResearchProject,
    user: User,
    permission: str = "view"
) -> bool:
    # 1. Superusers have universal access
    if user.is_superuser:
        return True

    # 2. Verify project organization matches user memberships
    if not project.organization_id:
        return True

    membership = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == project.organization_id,
        OrganizationMember.user_id == user.id
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to this organization's project.")

    # 3. Role-Based Permissions
    if permission in ("edit", "admin") and membership.role == "VIEWER":
        raise HTTPException(status_code=403, detail="Insufficient permissions for this action.")

    return True
```

### 2.2 Server-Enforced Identity
In `POST /api/v1/editorial/{id}/reviews` and `comments`:
```python
# Server strictly overrides any client-supplied reviewer string
reviewer_name = current_user.full_name or current_user.email
review = review_workflow_service.submit_review(
    db=db,
    editorial_id=id,
    reviewer_name=reviewer_name,
    status=req.status,
    notes=req.notes,
    score=req.score,
    metadata=req.metadata
)
```

### 2.3 Publication Immutability Guards
In `backend/app/services/editorial/editorial_service.py`:
```python
def update_editorial(self, db: Session, editorial_id: str, req: EditorialUpdate) -> EditorialOutput:
    editorial = self.get_editorial(db, editorial_id)
    if not editorial:
        raise HTTPException(status_code=404, detail="Editorial edition not found.")
    
    if editorial.status == "FINALIZED":
        raise HTTPException(
            status_code=409,
            detail="Cannot modify a finalized editorial edition. The content is locked for publication."
        )
    ...
```

---

## 3. Automated Test Verification Results

All 5 Phase 21 security and hardening tests in `backend/tests/test_phase21_editorial_hardening.py` passed with 100% compliance:

```
backend/tests/test_phase21_editorial_hardening.py::test_phase21_multi_tenant_editorial_isolation PASSED [ 20%]
backend/tests/test_phase21_editorial_hardening.py::test_phase21_finalized_editorial_immutability PASSED [ 40%]
backend/tests/test_phase21_editorial_hardening.py::test_phase21_reviewer_identity_server_enforcement PASSED [ 60%]
backend/tests/test_phase21_editorial_hardening.py::test_phase21_multi_format_exports PASSED [ 80%]
backend/tests/test_phase21_editorial_hardening.py::test_phase21_dashboard_stats_tenant_scoping PASSED [100%]
```

Full backend test suite status: **229 passed in 7.13s (100% success rate)**.

