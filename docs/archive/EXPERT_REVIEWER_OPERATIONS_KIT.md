# AgileGraph Independent Expert Reviewer Operations Kit

**Document Version:** 2.0.0  
**Status:** READY FOR OPERATIONAL DEPLOYMENT (NO FABRICATED DATA)  
**Distribution Target:** External Independent Expert Panel (4 Qualified Cryptography/Security Reviewers)  
**Governing Protocol:** [`docs/EXPERT_ANNOTATION_PROTOCOL.md`](file:///d:/projects/agilegraph%20new/docs/EXPERT_ANNOTATION_PROTOCOL.md)  
**Governing Rubric:** [`docs/EXPERT_ANNOTATION_RUBRIC.md`](file:///d:/projects/agilegraph%20new/docs/EXPERT_ANNOTATION_RUBRIC.md)

---

## 1. Reviewer Cohort & Anonymous Handle Assignment

To eliminate anchoring bias and protect expert confidentiality, all reviewers are assigned pseudonymous identifiers. Personal names, email addresses, employer details, and institutional affiliations are stored strictly in an offline, password-protected tracking roster and are **NEVER committed to Git or embedded in dataset packages**.

### Panel Roster & Reviewer ID Map

| Pseudonym Handle | Target Profile / Specialization | Contact / Channel | Package Dispatched? | Formal Consent Received? | Conflict of Interest Disclosed? | Submission Received? | Verification Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `expert_01` | Applied Cryptographer (PQC/NIST standards) | `[CONFIDENTIAL_OFFLINE]` | [ ] Yes / [ ] No | [ ] Confirmed | [ ] Disclosed (No conflict) | [ ] Yes / [ ] No | PENDING |
| `expert_02` | Enterprise Security Architect (Crypto-agility) | `[CONFIDENTIAL_OFFLINE]` | [ ] Yes / [ ] No | [ ] Confirmed | [ ] Disclosed (No conflict) | [ ] Yes / [ ] No | PENDING |
| `expert_03` | Systems Security Engineer (Go/Java token crypto) | `[CONFIDENTIAL_OFFLINE]` | [ ] Yes / [ ] No | [ ] Confirmed | [ ] Disclosed (No conflict) | [ ] Yes / [ ] No | PENDING |
| `expert_04` | Software Security Engineer (Python/C bindings) | `[CONFIDENTIAL_OFFLINE]` | [ ] Yes / [ ] No | [ ] Confirmed | [ ] Disclosed (No conflict) | [ ] Yes / [ ] No | PENDING |

---

## 2. Reviewer Pre-Flight Checklist

Before distributing review dossiers to an external expert, the project lead must confirm every step:

```
[ ] 1. PROTOCOL STATUS CHECK
       Confirmdocs/EXPERT_ANNOTATION_PROTOCOL.md status is "FINALIZED".
[ ] 2. BLINDING VERIFICATION
       Confirm the distributed package (sample_annotation_package.json) contains:
       - Asset identifiers, paths, observable AST snippets, algorithms, and key sizes.
       - ZERO heuristic risk scores (base_risk omitted).
       - ZERO rule-based scores.
       - ZERO GATv2 model predictions or ranking orders.
[ ] 3. CONFLICT OF INTEREST DISCLOSURE
       Reviewer confirms they have not been a primary author/maintainer of the 8 pinned repos:
       (pallets/itsdangerous, pyca/bcrypt, pyca/cryptography, auth0/java-jwt,
        jwtk/jjwt, golang-jwt/jwt, dgrijalva/jwt-go, golang/crypto).
       If an author conflict exists for a repo, the expert must mark those assets UNKNOWN / abstain.
[ ] 4. TEMPLATE BINDING
       Reviewer receives a personalized copy of expert_submission_template.json with their assigned
       handle prefilled (e.g. expert_id: "expert_01").
[ ] 5. ETHICS & OVERSIGHT SIGN-OFF
       Project guide confirms consent and research review status per institutional policy.
```

---

## 3. Concise Reviewer Instructions (For Distribution)

*(Include this section in the reviewer package alongside the JSON dossier and Rubric)*

### Overview
You are invited to provide independent human expert judgments on **166 cryptographic asset dossiers** sampled from real-world open-source software repositories (Python, Java, Go). Your assessments will serve as the independent ground truth to evaluate automated crypto-agility and post-quantum migration risk discovery systems.

### Rules of Engagement
1. **Strict Independence:** Please evaluate each dossier individually. Do not discuss specific ratings with other participants.
2. **Double-Blind Procedure:** You have not been provided with automated risk scores or model rankings. Rely strictly on the observable code snippets, parameters, and your professional expertise.
3. **Primary Assessment (`migration_priority`):**
   Assign one of the following priority levels based on urgency for post-quantum planning and crypto-agility:
   - `"HIGH"`: Urgent planning required. Classical asymmetric primitives vulnerable to Shor's algorithm (RSA, ECC, ECDSA, DH) securing high-value credentials or sensitive data with long shelf life (Store Now, Decrypt Later risk); or broken legacy primitives (MD5, SHA1 in signatures, DES).
   - `"MEDIUM"`: Moderate urgency. Symmetric algorithms (AES-128, SHA-256) subject to Grover's quadratic speedup but not immediately compromised; or indirect token generation in standard applications.
   - `"LOW"`: Low priority / robust posture. Modern algorithms (AES-256, SHA-384/512) or already post-quantum ready implementations (ML-KEM, ML-DSA); non-sensitive integrity tokens.
   - `"UNKNOWN"`: Insufficient evidence in snippet or cannot determine without entire repository context. **Abstaining is scientifically valid and preferred over guessing.**
4. **Multi-Dimensional Context Dimensions (Optional but Recommended):**
   - `crypto_concern`: `CLASSICAL_BROKEN`, `CLASSICAL_VULNERABLE_PQC`, `QUANTUM_VULNERABLE_STRONG`, `POST_QUANTUM_READY`, `UNKNOWN_OR_UNCLASSIFIED`.
   - `sensitive_data_impact`: `CREDENTIALS_OR_SECRETS`, `PERSONAL_DATA_PII`, `COMMUNICATION_CONTENT`, `INTEGRITY_TOKEN`, `INTERNAL_OR_ANCILLARY`, `UNKNOWN_OR_INSUFFICIENT_EVIDENCE`.
   - `exposure`: `INTERNET_FACING`, `INTERNAL`, `NOT_APPLICABLE`, `UNKNOWN`.
   - `post_quantum_urgency`: `IMMEDIATE_ACTION`, `PLANNED_MIGRATION`, `MONITOR`, `INVESTIGATE_FURTHER`.
   - `evidence_confidence`: `HIGH`, `MEDIUM`, `LOW`.
   - `rationale`: Brief sentence explaining your technical reasoning.

---

## 4. Submission Validation and Quality Control Pipeline

When an expert completes their JSON file, execute the following command sequence in the repository root:

### Step 1: Ingest & Validate Schema
```bash
python -c "
import json
from backend.src.ml.import_annotations import AnnotationImporter

# Load expected asset IDs from package
with open('backend/dataset/annotation/sample_annotation_package.json', 'r') as f:
    pkg = json.load(f)
expected_assets = [a['asset_id'] for a in pkg['assets']]
expected_experts = ['expert_01', 'expert_02', 'expert_03', 'expert_04']

importer = AnnotationImporter(
    expected_asset_ids=expected_assets,
    expected_expert_ids=expected_experts,
    dataset_version='v1',
    expected_protocol_version='2.0.0'
)

# Replace with the path to the returned submission
submission_file = 'backend/dataset/annotation/submissions/expert_01_submission.json'
result = importer.import_annotations(submission_file, protocol_status='FINALIZED')
print('Import status:', result['status'])
if result['status'] != 'SUCCESS':
    print('Validation error:', result.get('message'))
else:
    print('Imported', result['imported_count'], 'valid records.')
"
```

### Step 2: Quality Control Rejection Criteria
The importer automatically rejects submissions for any of the following defects:
- Any altered or missing `asset_id` (must match the 166 canonical IDs).
- Any unapproved `expert_id` or non-standard pseudonym.
- Unrecognized enum values outside the Rubric v2.0 specification.
- Duplicate ratings by the same expert for the same asset.
- Missing timestamps or inconsistent protocol version strings.

If rejected, notify the expert with the exact error message and request re-submission before proceeding to agreement calculation.

---

## 5. Statistical Inter-Annotator Agreement Calculation

Once all 4 submissions are successfully imported, compute agreement across all ratings:

```bash
python -c "
import numpy as np
from backend.src.ml.agreement import AgreementMetrics
from backend.src.ml.expert_validation import ExpertLabelClass

# Construct ratings matrix (4 raters x 166 assets)
# Encode: LOW -> 0, MEDIUM -> 1, HIGH -> 2, UNKNOWN/Missing -> np.nan
# (Example loaded from verified imported labels list)

# 1. Krippendorff's Alpha (Ordinal metric per Krippendorff 2011)
# alpha_result = AgreementMetrics.krippendorff_alpha(reliability_data, level='ordinal')
# print('Krippendorff alpha:', alpha_result['statistic'])

# 2. Pairwise Weighted Cohen's Kappa
# kappa_result = AgreementMetrics.cohens_kappa(rater1_labels, rater2_labels, weights='quadratic', bootstrap_ci=True)
# print('Cohen kappa (1 vs 2):', kappa_result['statistic'])
"
```

### Preregistered Decision Gate ($\alpha \ge 0.80$)
- **If $\alpha \ge 0.80$**: Inter-annotator agreement is established. Formulate consensus via Majority Vote or Lead Adjudication. Unlock Step 6B (Ground-Truth Consensus Dataset Creation).
- **If $0.67 \le \alpha < 0.80$**: Tentative agreement. Require formal joint adjudication by an adjudication board for all discrepant assets before establishing ground truth.
- **If $\alpha < 0.67$**: Agreement failed. Stop pipeline. Do not train GATv2. Convene a rubric clarification session to resolve systematic rater disagreements.

---

## 6. Discrepancy Adjudication Workflow

When expert ratings diverge on an asset (e.g., 2 experts rate `HIGH`, 1 rates `MEDIUM`, 1 rates `LOW`):
1. **Discrepancy Identification**: Automatically flag all assets where rater variance $> 0$.
2. **Adjudication Dossier**: Compile the divergent ratings alongside annotator rationales (`rationale` field).
3. **Consensus Meeting**: Lead adjudicator reviews the conflicting rationales and records a final binding `AdjudicatedLabel` with explicit justification in `adjudication_rationale`.
4. **Preservation**: The original rater judgments are preserved in `original_expert_labels` for inter-rater transparency.

---

## 7. Professional Reviewer Recruitment Email Draft

**Subject:** Invitation: Expert Review of Cryptographic Assets for Post-Quantum Migration (AgileGraph Project)

Dear [Expert Name],

I hope this message finds you well.

I am conducting research on **Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration (AgileGraph)** as part of my major engineering project. The research investigates how automated static code analysis and graph neural networks can discover cryptographic primitives across enterprise codebases and prioritize post-quantum migration.

To rigorously evaluate our models without circular reasoning, we require independent ground truth established by domain experts in applied cryptography and security engineering.

### What is Involved?
- **Task:** Reviewing **166 code asset dossiers** sampled from open-source repositories (Python, Java, Go).
- **Dossiers Provided:** Each dossier contains observable AST code snippets, API call sites, key sizes, and dependency references. No model predictions or preliminary risk scores are shown (strict double-blind review).
- **Rating:** Assigning a post-quantum migration priority (`HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN` if evidence is incomplete) using our 7-factor evaluation rubric.
- **Estimated Effort:** Approximately 2.5 to 3.5 hours total. You can complete the reviews in multiple sessions using a simple standardized JSON template.

### Confidentiality and Ethics
- **Voluntary Participation:** Your participation is completely voluntary, and you may withdraw at any time.
- **Strict Anonymity:** All reviewers are assigned pseudonymous handles (e.g. `expert_01`). No names, employer details, or email addresses will appear in dataset publications or code repositories.
- **Institutional Oversight:** This evaluation procedure is conducted under the guidance of our academic project mentor. (Formal IRB/ethics approvals, if required by your institution, can be coordinated upon request).
- **Conflict of Interest:** If you are an active maintainer of any of the benchmark libraries (`pyca/cryptography`, `pallets/itsdangerous`, `jwtk/jjwt`, `golang/crypto`, etc.), you will simply abstain from those specific items.

### Timeline
We kindly request completed submissions by **[Insert Date, e.g., 2 weeks from dispatch]**.

If you are willing to participate, please reply to this email, and I will share the blinded evaluation package, rubric, and your assigned reviewer template.

Thank you very much for your time and consideration.

Warm regards,

**[Your Name]**  
Lead Researcher, Project AgileGraph  
Department of Computer Science & Engineering  
[Institution / University Name]
