# AgileGraph — Phase 3: Public Landing Page, Authentication & User Data Isolation Report

**Project Title:** AgileGraph — Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration  
**Degree Level:** Final-Year B.Tech Cyber Security Project (2026)  
**Document Classification:** Engineering & Security Audit Deliverable  
**Date:** October 25, 2026  
**Status:** COMPLETE — Security Hardened, All Backend Tests Passed (396/396), All Frontend Tests Passed (38/38), Production Build Clean  

---

## 1. Executive Summary

This deliverable implements and hardens Phase 3 for the AgileGraph platform:
1. **Public Landing / About Page (`/`)**: Designed with visual layout and section structure inspired by modern post-quantum cybersecurity portals, while strictly truthful to the academic B.Tech Cyber Security research project. Contains no fabricated customer logos, fake certification seals, or inflated benchmark statistics. Clearly states that the **GATv2 Graph Neural Network is an exploratory prototype evaluated under weak supervision**, alongside the primary **deterministic 7-factor heuristic engine**.
2. **Defensive End-to-End Authentication System**: Implemented genuine backend authentication using `bcrypt` (12 rounds) salted hashing and `PyJWT` (HS256) signed bearer tokens with a 24-hour expiration window. Includes server-side token revocation (`invalidated_tokens` table) upon logout and automatic session revalidation on page reload.
3. **Safe Multi-User Isolation & Ownership Policy**:
   - Unknown or ownerless projects are **strictly denied access (HTTP 403)**, preventing the accidental disclosure of orphan or user-specific data.
   - Public reference benchmarks (the 8 benchmark repositories and the existing `agile` project) are explicitly registered in `LEGACY_BENCHMARK_PROJECTS`, granting **read-only access** to authenticated researchers without silently assigning ownership to any user.
   - Mutations, re-scans, or deletions on projects owned by other users or on shared benchmark datasets are strictly rejected.
4. **Hardened Default-Secure Environment Controls**:
   - `AGILEGRAPH_ALLOW_ANONYMOUS` is disabled by default. It functions **strictly as a development/test override** in non-production environments.
   - In production (`AGILEGRAPH_ENV=production`), `AGILEGRAPH_ALLOW_ANONYMOUS` is strictly ignored and rejected, and any attempt to run with default or weak JWT secrets (< 32 characters) immediately halts execution.
5. **Comprehensive Verification**: 396 backend pytest tests passed (0 failures, 4 skips due to Windows symlink limitations), 38 frontend vitest tests passed (0 failures), and production bundle generation (`npm run build`) succeeded cleanly.

---

## 2. Architecture & File Inventory

### Backend Security Components

| File | Type | Description |
|---|---|---|
| `backend/src/core/auth.py` | Security Core | Bcrypt password hashing (12 rounds, 72-byte max guard), JWT issuance & signature validation (`HS256`), dynamic production secret validation, and `get_current_user` dependency with production-safe anonymous disabling. |
| `backend/src/core/auth_storage.py` | Data Persistence | SQLite database layer managing `users`, `user_projects` (ownership mapping), and `invalidated_tokens` (revocation blacklist). Enforces `LEGACY_BENCHMARK_PROJECTS` safe whitelist. |
| `backend/src/api/auth_routes.py` | API Router | REST endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`. Enforces username regex, email format, and password length checks. |
| `backend/src/api/routes.py` | Scanner & Core API | Enforced `Depends(get_current_user)`, `verify_project_ownership`, and `verify_project_scan_permission` on `/scan`, `/projects/{id}/graph`, `/projects/{id}/risk`, `/projects/{id}/report/*`, and `DELETE /projects/{id}`. |
| `backend/src/api/product_routes.py` | Product API | Protected `/pqc-readiness/{id}`, `/crypto-inventory`, `/assets/{aid}/priority`, `/assets/{aid}/roadmap` (read), and `/assets/{aid}/roadmap` transition (`write=True`). |
| `backend/src/core/storage.py` | Storage Layer | Added `project_exists(project_id)` check to verify on-disk artifacts without exposing unowned directories. |
| `backend/tests/api/test_auth.py` | Security Test Suite | 5 exhaustive test suites covering registration, login, token revocation, production safety, cross-user isolation across all verbs, and ownerless project policies. |
| `backend/tests/conftest.py` | Test Harness | Autouse fixture configuring `AGILEGRAPH_ALLOW_ANONYMOUS=1` so 391 pre-existing tests continue passing without modification. |

### Frontend Components

| File | Type | Description |
|---|---|---|
| `frontend/src/components/LandingPage.tsx` | View | High-aesthetic dark navy landing page featuring: Hero with NIST PQC badge, Platform Capabilities anchor (`#platform`), How It Works anchor (`#how`), Research & Methodology anchor (`#research`), Technology Stack anchor (`#tech`), Interactive SVG Graph architecture preview, and footer. |
| `frontend/src/components/auth/LoginPage.tsx` | View | Dark cybersecurity login form with real-time error messaging, token storage, and redirect preservation. |
| `frontend/src/components/auth/RegisterPage.tsx` | View | Registration form with client-side password matching and length validation, submitting to backend auth API. |
| `frontend/src/components/ProtectedRoute.tsx` | Route Guard | React Router guard redirecting unauthenticated visitors to `/login` with target path state. |
| `frontend/src/context/AuthContext.tsx` | State | React Context managing `user`, `token`, `isAuthenticated`, session revalidation against `GET /api/v1/auth/me`, `login`, `register`, and `logout`. |
| `frontend/src/api/client.ts` | HTTP Client | Added Bearer token header injection and typed API methods for auth endpoints. |
| `frontend/src/components/Layout.tsx` | Layout | Updated Overview navigation link to `/app`, added user badge (username, role), Public Site link (`/`), and Sign Out button. |
| `frontend/src/App.tsx` | Router | Wrapped application in `AuthProvider`, established public routes (`/`, `/login`, `/register`), mapped `/app` to Dashboard, and protected all functional views. |
| `frontend/src/tests/Auth.test.tsx` | Test Suite | 7 tests verifying login validation, successful login and token storage, error handling, registration validation, registration submission, protected route guarding, and logout state clearing. |
| `frontend/src/tests/AppIntegration.test.tsx` | Test Suite | Integration suite verifying public landing page render, unauthenticated redirect to `/login`, and multi-route navigation across all 9 dashboard views when authenticated. |

---

## 3. Route Map & Security Policy Matrix

| Endpoint | Method | Operation Type | Ownership Check | Policy / Access Rule |
|---|---|---|---|---|
| `/` | `GET` | Read | None (Public) | Public Landing Page |
| `/login`, `/register` | `POST` | Create | None (Public) | Account Registration and Login |
| `/api/v1/auth/me` | `GET` | Read | Authenticated User | Retrieves caller profile |
| `/api/v1/auth/logout`| `POST` | Revoke | Authenticated User | Revokes JWT in `invalidated_tokens` |
| `/api/v1/scan` | `POST` | Create / Scan | `verify_project_scan_permission` | Re-scan allowed only if caller owns project; new scan establishes caller ownership; overwriting other users or shared benchmarks rejected with **403**. |
| `/api/v1/projects/{id}/graph` | `GET` | Read | `verify_project_ownership(read)` | Allowed if caller is owner or `{id}` in `LEGACY_BENCHMARK_PROJECTS`. Unknown or unowned projects rejected with **403**. |
| `/api/v1/projects/{id}/risk` | `GET` | Read | `verify_project_ownership(read)` | Same as above. |
| `/api/v1/projects/{id}/report/json` | `GET` | Read / Export | `verify_project_ownership(read)` | Same as above. |
| `/api/v1/projects/{id}/report/markdown` | `GET` | Read / Export | `verify_project_ownership(read)` | Same as above. |
| `/api/v1/projects/{id}` | `DELETE` | Delete | `verify_project_ownership(write)` | Allowed only if caller is recorded owner. Shared benchmarks and unowned projects rejected with **403**. |
| `/api/v1/product/{id}/pqc-readiness` | `GET` | Read | `verify_project_ownership(read)` | Allowed for owner or benchmark whitelist. |
| `/api/v1/product/{id}/crypto-inventory` | `GET` | Read | `verify_project_ownership(read)` | Allowed for owner or benchmark whitelist. |
| `/api/v1/product/{id}/assets/{aid}/priority` | `GET` | Read | `verify_project_ownership(read)` | Allowed for owner or benchmark whitelist. |
| `/api/v1/product/{id}/assets/{aid}/roadmap` | `GET` | Read | `verify_project_ownership(read)` | Allowed for owner or benchmark whitelist. |
| `/api/v1/product/{id}/assets/{aid}/roadmap` | `POST` | Modify / Write | `verify_project_ownership(write)` | Allowed only if caller is recorded owner. Mutations on benchmarks or unowned projects rejected with **403**. |
| `/api/v1/product/mosca` | `POST` | Compute | None (Public Math) | Stateless mathematical calculator $(X + Y > Z)$. |

---

## 4. Focused Security Review & Hardening Details

### 4.1 Production Safety of `AGILEGRAPH_ALLOW_ANONYMOUS`
- **Vulnerability Analyzed**: A development flag intended for test harnesses could accidentally bypass authentication in a production deployment if environment variables were misconfigured.
- **Hardening Implemented**:
  1. Default behavior is strictly secure: when `AGILEGRAPH_ALLOW_ANONYMOUS` is not set, all protected endpoints require a valid Bearer token.
  2. In `backend/src/core/auth.py`, `is_anonymous_allowed()` verifies both `AGILEGRAPH_ALLOW_ANONYMOUS == "1"` and `not is_production()`.
  3. If `AGILEGRAPH_ENV=production` is detected, `is_anonymous_allowed()` returns `False` unconditionally and logs a critical security alert. The flag cannot bypass authentication in production under any circumstances.

### 4.2 Safe Handling of Benchmark Projects and Existing `agile` Project
- **Vulnerability Analyzed**: Treating ownerless projects as universally accessible (`if owner is None: return True`) risks exposing orphan cache directories or unassigned user data.
- **Hardening Implemented**:
  1. Created an explicit immutable whitelist: `LEGACY_BENCHMARK_PROJECTS = frozenset({"python_cryptography", "python_bcrypt", "python_itsdangerous", "java_jjwt", "java_java_jwt", "go_crypto", "go_jwt", "go_jwt_go", "agile", "audit_test_project", ...})`.
  2. Authenticated researchers may read from whitelisted benchmark datasets and the `agile` project as public reference artifacts.
  3. Querying these reference artifacts **never silently assigns ownership** to the querying user (`get_project_owner("agile")` remains `None`).
  4. Write operations (`write=True`), re-scans (`POST /scan`), and deletions (`DELETE /projects/{id}`) on shared reference projects are strictly rejected (**HTTP 403 Forbidden**) in authenticated deployments.
  5. Any project not in `LEGACY_BENCHMARK_PROJECTS` and lacking a recorded owner is treated as an unknown/unowned project and **strictly denied access (HTTP 403 Forbidden)**.

### 4.3 Secrets, Passwords & Tokens
- **Production Secret Validation**: In production mode, `get_secret_key()` verifies that `AGILEGRAPH_SECRET_KEY` is set, does not equal the development default fallback, and has a minimum entropy length of 32 characters. If invalid, the service refuses to start.
- **Password Work Factor & Byte Limit**: Passwords are hashed with `bcrypt.gensalt(rounds=12)`. Inputs exceeding 72 bytes are rejected with HTTP 400 to prevent silent bcrypt truncation vulnerabilities.
- **Token Invalidation**: Server-side token blacklisting in SQLite (`invalidated_tokens`) ensures that logging out immediately revokes the JWT, preventing replay attacks within the 24-hour expiration window.

### 4.4 Browser Token Storage Security Review
- **Current Approach**: The frontend stores the access token in `localStorage` under `agilegraph_token`.
- **Identified Risk**: Storage in `localStorage` is susceptible to token exfiltration if Cross-Site Scripting (XSS) is present on the origin.
- **Existing Mitigations**:
  - React 19's virtual DOM automatically performs HTML entity encoding on rendered strings, preventing standard injection.
  - Server-side revocation blacklist allows immediate invalidation upon logout.
- **Production Recommendation**: For high-assurance institutional deployments, transition the session architecture to `HttpOnly`, `Secure`, `SameSite=Strict` cookies with CSRF tokens, which prevents JavaScript access to raw token credentials.

---

## 5. Test Suite Verification & Audit Results

### Backend Test Results (`python -m pytest backend/tests -rs`)

```
=========================== short test summary info ===========================
SKIPPED [1] backend\tests\pipeline\test_runner_filesystem.py:65: Symlink creation not supported (Windows without developer mode)
SKIPPED [1] backend\tests\pipeline\test_runner_filesystem.py:89: Symlink creation not supported
SKIPPED [1] backend\tests\pipeline\test_runner_filesystem.py:105: FIFO not supported on this platform
SKIPPED [1] backend\tests\pipeline\test_runner_filesystem.py:169: Symlink not available
=============== 396 passed, 4 skipped, 1314 warnings in 30.85s ================
```

### Dedicated Security & Multi-User Tests (`pytest backend/tests/api/test_auth.py -v`)

```
backend/tests/api/test_auth.py::test_registration_and_login_flow PASSED          [ 20%]
backend/tests/api/test_auth.py::test_missing_and_invalid_token_rejections PASSED [ 40%]
backend/tests/api/test_auth.py::test_anonymous_access_and_production_safety PASSED [ 60%]
backend/tests/api/test_auth.py::test_cross_user_isolation_read_write_scan_export_delete PASSED [ 80%]
backend/tests/api/test_auth.py::test_unknown_and_legacy_project_ownership_policy PASSED [100%]
```

### Frontend Test Results (`npm test -- --run`)

```
Test Files  5 passed (5)
     Tests  38 passed (38)
  Duration  2.89s
```

Detailed suites:
- `src/tests/Reports.test.tsx` (8 passed)
- `src/tests/CryptoInventory.test.tsx` (8 passed)
- `src/tests/Auth.test.tsx` (7 passed)
- `src/tests/ProductLayer.test.tsx` (12 passed)
- `src/tests/AppIntegration.test.tsx` (3 passed)

### Frontend Production Build (`tsc -b && vite build`)

```
vite v8.3.2 building client environment for production...
✓ 2950 modules transformed.
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-D8oIKQJ2.css   60.42 kB │ gzip:  10.13 kB
dist/assets/index-CRVb8rse.js   598.27 kB │ gzip: 171.81 kB
✓ built in 864ms
```

---

## 6. Production Deployment & Configuration Guide

For production deployment:
```bash
# 1. Set environment to production
export AGILEGRAPH_ENV="production"

# 2. Provide a cryptographically random secret key (minimum 32 characters)
export AGILEGRAPH_SECRET_KEY="c8f17e30d1b4a92e850f492b7194d30a6e812547b93a02ef591c7849e62d41b5"

# 3. Optional: Configure dedicated database and scan root
export AGILEGRAPH_AUTH_DB="/var/lib/agilegraph/auth.db"
export AGILEGRAPH_SCAN_ROOT="/var/agilegraph/repositories"

# 4. Start backend with uvicorn
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```
