# AgileGraph — Project Demonstration & Viva Checklist

This checklist provides an end-to-end operational guide for demonstrating the AgileGraph system during academic defense, viva examinations, and technical presentations.

---

## 1. Environment & Pre-Flight Checklist

Before presenting, ensure both backend and frontend servers are launched and responsive:

### 1.1 Backend Service Initialization
```powershell
# Open Terminal 1: Backend
cd "d:\projects\agilegraph new"
.\backend\venv\Scripts\Activate.ps1
$env:AGILEGRAPH_ALLOW_ANONYMOUS="1"   # Optional: bypass login for rapid demo
python -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8000 --reload
```
- Verify API Docs: Open `http://127.0.0.1:8000/docs` in your browser.
- Health Check: `curl http://127.0.0.1:8000/health` should return `{"status": "healthy"}`.

### 1.2 Frontend Service Initialization
```powershell
# Open Terminal 2: Frontend
cd "d:\projects\agilegraph new\frontend"
npm run dev
```
- Access UI: Open `http://localhost:5173` in Google Chrome or Microsoft Edge.

---

## 2. Step-by-Step Viva Demonstration Script

Follow this scripted 5-minute walk-through to present every critical feature cohesively:

### Step 1: Public Landing Page & Problem Framing (1 Minute)
- **Action**: Navigate to `http://localhost:5173/`.
- **Key Talking Points**:
  - Explain the Post-Quantum transition crisis: Shor's algorithm renders classical asymmetric algorithms (RSA, ECC, Diffie-Hellman) vulnerable to rapid decryption.
  - Highlight "Harvest Now, Decrypt Later" (HNDL) attacks where adversaries intercept encrypted traffic today to decrypt once a Cryptanalytically Relevant Quantum Computer (CRQC) exists.
  - Present AgileGraph as an automated crypto-agility risk assessment platform.

### Step 2: Multi-Language Cryptographic Discovery (1 Minute)
- **Action**: Log in or navigate to the Dashboard $\rightarrow$ **Crypto Inventory**.
- **Key Talking Points**:
  - Point out real discovered primitives across Go, Java, and Python.
  - Filter by algorithm (e.g., search `RSA` vs `AES-256` vs `SHA-256`).
  - Demonstrate transparent handling of missing metadata: explain that when an AST scanner cannot determine the exact key length, AgileGraph displays "Unspecified" rather than fabricating a guess.

### Step 3: Typed Property Graph Visualization (1 Minute)
- **Action**: Click on **Graph View**.
- **Key Talking Points**:
  - Explain the 6 canonical node types: `file`, `crypto_usage`, `certificate`, `endpoint`, `library`, `sensitive_data`.
  - Explain the 11 edge triplets connecting them (e.g., `('file', 'IMPORTS', 'library')`, `('file', 'CONTAINS', 'crypto_usage')`).
  - Explain why graph modeling is necessary: crypto risk is topological. An unobserved wrapper file that imports a vulnerable key-generation library inherits risk through dependency reachability.

### Step 4: Dual-Engine Risk Analysis & Version Switcher (1.5 Minutes)
- **Action**: Navigate to **Risk Analysis**.
- **Key Talking Points**:
  - **V1 Baseline (Default)**: Show that V1 is selected by default. Show the 7-factor linear composite score ($w_1 S + \dots + w_7 M$) and explain the missing-evidence policy (`RENORMALIZE`).
  - **Demonstrate Divergence**: Explain why V1 underpredicts on key abstractions (Macro-F1 $0.3225$) because pure heuristic scoring lacks structural propagation.
  - **Toggle to V2 Experimental**: Flip the Engine Version toggle to **V2 (Calibrated + Propagated)**.
  - **Observe Score Updates**: Point out how the score updates dynamically, displaying the active version badge (`heuristic-v2.0-experimental`), and showing how graph propagation elevated abstract key builders from LOW to MEDIUM/HIGH.
  - Explain the LORO evaluation: Macro-F1 rises to $0.7312$ ($+126.7\%$), with HIGH recall reaching $91.25\%$.

### Step 5: Mosca Readiness & Post-Quantum Remediation (30 Seconds)
- **Action**: Navigate to **PQC Readiness / Mosca Readiness**.
- **Key Talking Points**:
  - Show the Mosca Urgency Index: $U = (X + Y) / Z$.
  - Demonstrate how systems where $X + Y > Z$ are flagged as `AT_RISK`.
  - Show the 6-state migration lifecycle (`DISCOVERED` to `DECOMMISSIONED`).

---

## 3. Defense Fallback & Quick Verification Checks

If an evaluator asks to inspect code or run tests live during the viva:

| Evaluator Request | Command to Execute | Expected Result |
| :--- | :--- | :--- |
| "Show me your test coverage." | `pytest backend/tests/ -q` | `439 passed, 4 skipped` |
| "Prove there are no mocked strings in the code." | `pytest backend/tests/core/test_forbidden_strings.py -v` | `1 passed (100% clean)` |
| "Prove the frontend builds without TypeScript errors." | `npm --prefix frontend run build` | `built in ~1.7s (clean)` |
| "Show the independent expert validation statistics." | `cat backend/dataset/artifacts/expert_validation_report.json` | 4 reviewers, $\kappa_{\text{Fleiss}} = 0.7791$ |
| "Show the V1 vs V2 cross-validation ablation." | `cat backend/dataset/artifacts/heuristic_v2_experiment_results.json` | LORO Macro-F1 $0.3225 \rightarrow 0.7312$ |

---

## 4. UI State Sanity Matrix

Ensure the following states are observed in the web browser:
- [x] Engine switch defaults to **Heuristic V1 (Baseline)** upon page load.
- [x] Selecting an asset displays the explainability drawer with 7 factor contributions.
- [x] Toggling to **Heuristic V2 (Calibrated)** sends `?engine_version=v2` and reflects the new score.
- [x] Comparison banner displays V1 vs. V2 delta without layout break.
- [x] Export to JSON and CSV triggers download immediately.

