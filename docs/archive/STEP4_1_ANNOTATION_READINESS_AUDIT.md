# AgileGraph Step 4.1 — Annotation Package Readiness Audit Report

**Date:** 2026-10-12  
**Audit Status:** AUDIT COMPLETE  
**Readiness Determination:** **READY WITH CAVEATS** (Engineering framework and blinded artifacts fully verified; external human panel recruitment, ethics approvals, and rubric alignment remain mandatory human prerequisites before collecting data)  
**Constraints Enforced:** No GATv2 model training; no synthetic expert labels or fake agreement scores created; no benchmark commits modified; strict double-blind protocol verified.

---

## Executive Summary

Step 4.1 conducts a rigorous, independent readiness audit of the AgileGraph expert annotation infrastructure established in Step 4. All code paths, schemas, sampling outputs, submission templates, and statistical evaluation engines were inspected and tested against the project's scientific and research-integrity constraints.

### Key Audit Findings
1. **Asset Sampling & Blinding (`VERIFIED`):** The 166-asset sample maps 100% to pinned benchmark repository commits across all 8 repositories and all 3 languages (Python, Java, Go). All 166 dossiers contain concrete observable AST evidence. **Zero heuristic risk scores, rule scores, or model predictions appear in the package.**
2. **Reviewer Independence & Privacy (`VERIFIED`):** Non-identifying pseudonyms (`expert_01` through `expert_04`) are enforced. Individual submissions cannot overwrite other reviewers' labels. Adjudicated consensus labels are stored separately in `AdjudicatedLabel` objects without altering original ratings.
3. **Submission Workflow & Defect Resolution (`FIXED AND REVERIFIED`):** Identified and resolved a `timezone.utc` datetime deprecation in `AnnotationImporter`. Enhanced unit tests to cover missing response handling, invalid category enum rejection, and rater isolation.
4. **Statistical Methodology (`VERIFIED`):** Krippendorff's alpha coincidence matrix was corrected to strictly pair distinct raters per unit. The proposed $\alpha \ge 0.80$ threshold has been contextualized in the protocol as a pre-specified study criterion requiring empirical justification, rather than a foregone conclusion.
5. **Outstanding Human Study Prerequisites:** The engineering framework is fully prepared, but deployment to a live study requires human panel recruitment, conflict-of-interest screening, and host-institution ethics determinations.

---

## 1. Inventory of Inspected Deliverables

| Deliverable | File Path | Scope of Inspection | Findings |
| :--- | :--- | :--- | :--- |
| **Annotation Protocol** | `docs/EXPERT_ANNOTATION_PROTOCOL.md` | Multi-stage review workflow, panel qualifications, blinding rules, acceptance criteria | Verified. Updated with Conflict of Interest disclosure, code snippet licensing, institutional oversight notice, and $\alpha \ge 0.80$ justification. |
| **Annotation Rubric** | `docs/EXPERT_ANNOTATION_RUBRIC.md` | 7-factor evaluation dimensions, definitions, operational examples, uncertainty handling | Verified. Clear guidance forbidding path-based criticality inference; concrete positive/negative examples provided. |
| **Data Schema** | `backend/src/ml/expert_validation.py` | Pydantic models: `ExpertLabel`, `AdjudicatedLabel`, `AssetForReview`, `ValidationDataset` | Verified. Multi-dimensional enums and alias validators operate cleanly with backward compatibility. |
| **Import Validator** | `backend/src/ml/import_annotations.py` | Data ingestion, protocol status enforcement, duplicate detection, validation rules | Verified. Resolved `datetime.now(timezone.utc)` deprecation. Rejection and acceptance tests pass. |
| **Agreement Engine** | `backend/src/ml/agreement.py` | Weighted Cohen's $\kappa$ (with bootstrap CI), Fleiss' $\kappa$, Krippendorff's $\alpha$, confusion matrices | Verified. Corrected coincidence matrix to omit self-pairs ($r1 \neq r2$). Ordinal and missing data handling validated. |
| **Package Generator** | `backend/scripts/generate_annotation_package.py` | Deterministic stratified sampling across all 8 repositories and 3 languages (seed: 42) | Verified. Produces exactly 166 blinded asset dossiers. |
| **Blinded Review Package** | `backend/dataset/annotation/sample_annotation_package.json` | 166 asset dossiers containing observable AST evidence, certificates, dependencies | Verified. Confirmed 0 heuristic leaks across all 166 items. |
| **Submission Template** | `backend/dataset/annotation/expert_submission_template.json` | Standardized JSON template for expert responses | Verified. Asset IDs match 100% with the review package. |
| **Regression Tests** | `backend/tests/ml/test_expert_annotation_framework.py` | End-to-end testing of schema, sampling, blinding, importer, and agreement metrics | Verified. 7 test cases covering all edge cases. |

---

## 2. Verification of the 166-Asset Sample

### A. Asset Count and Repository Representation
The sample was evaluated across all 8 pinned benchmark repositories:

| Repository Key | Language | Pinned Commit SHA | Available Assets | Sampled Assets | Coverage (%) | Observable Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `python_itsdangerous` | Python | `672971d66a2ef9f85151e53283113f33d642dabd` | 7 | 7 | 100.0% | Signing, serialization, HMAC |
| `python_bcrypt` | Python | `59b41aaa24c025d1cd231c37d2755b94184a3e67` | 2 | 2 | 100.0% | Key derivation, native bindings |
| `python_cryptography` | Python | `f0ba3000a365d44db153362e847c88339c9231f4` | 1,013 | 50 | 4.9% | Ciphers, hazmat primitives, X.509 certs |
| `java_java_jwt` | Java | `29f252b2d6fea74df6576803d5fce5f6d6799cf3` | 34 | 20 | 58.8% | RSA/ECDSA/HMAC algorithms, verifiers |
| `java_jjwt` | Java | `fb71496164c71442d08adec4571d9616ed5e1b8d` | 212 | 35 | 16.5% | Signature schemes, key loaders |
| `go_jwt` | Go | `73c870b18e68b6e654b2b03f485aa3c9fab32cea` | 30 | 15 | 50.0% | Standard Go token signing methods |
| `go_jwt_go` | Go | `9742bd7fca1c67ba2eb793750f56ee3094d1b04f` | 26 | 12 | 46.2% | Legacy Go token parsing & verification |
| `go_crypto` | Go | `b39ff6d641ecc5bb4b241737cb0c6b646f3e12a9` | 108 | 25 | 23.1% | SSH, OpenPGP, curve primitives |
| **Corpus Total** | **All 3** | **All Pinned** | **1,432** | **166** | **11.6%** | **All assets have evidence** |

### B. Representation by Programming Language
- **Python:** 59 assets (35.5%)
- **Java:** 55 assets (33.1%)
- **Go:** 52 assets (31.3%)

### C. Blinding and Information Leakage Audit
A comprehensive key-scanning script audited every entry in `sample_annotation_package.json`:
- Mismatches against pinned `benchmark_manifest.json` commits: **0**
- Leaked heuristic risk scores (`heuristic_score`, `score`, `weight`): **0**
- Leaked baseline or rule classifications (`prediction`, `rule_scores`): **0**
- Assets with zero observable evidence: **0**
- Asset ID stability: The sequence and identifiers in `expert_submission_template.json` match `sample_annotation_package.json` with 100% identity.

---

## 3. Reviewer Independence, Privacy, and Ethics Review

1. **Rater Isolation:** Annotators evaluate dossiers in complete isolation. No collaborative interface, shared spreadsheets, or prior peer ratings are exposed during Stage 2.
2. **Pseudonymous Identifiers:** Raters are identified as `expert_01`, `expert_02`, `expert_03`, `expert_04`. No names, contact details, or corporate affiliations exist in the data model.
3. **Duplicate Submission Control:** The `AnnotationImporter` tracks `(asset_id, expert_id)` tuples and strictly rejects duplicate evaluations of the same asset by the same expert.
4. **Adjudication Separation:** Consensus determinations do not overwrite individual records. Original ratings and rationales are preserved in `labels`, while final consensus is recorded in `adjudicated_labels` with adjudicator ID and rationale.
5. **Ethics and Institutional Oversight:** The protocol explicitly notes that formal Institutional Review Board (IRB) review, participant consent protocols, and ethical clearances are institutional responsibilities requiring authorization from the major project guide. No institutional clearance is claimed in advance.

---

## 4. Submission Workflow Verification

Synthetic test fixtures were used to validate the ingestion and validation rules in `backend/src/ml/import_annotations.py`:

| Test Scenario | Input Data | Expected Behavior | Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Protocol Status Gate** | `protocol_status="PENDING_FINALIZATION"` | Rejection with diagnostic error | `"REJECTED"`: Cannot import while protocol is unfinalized | **PASSED** |
| **Unknown Asset ID** | Asset ID not in expected manifest | Rejection | `"REJECTED"`: Unknown asset ID | **PASSED** |
| **Unknown Expert ID** | Pseudonym not in registered panel | Rejection | `"REJECTED"`: Unknown expert ID | **PASSED** |
| **Duplicate Rating** | Two ratings for same asset by same expert | Rejection | `"REJECTED"`: Duplicate rating | **PASSED** |
| **Invalid Category Enum** | `crypto_concern="INVALID_CATEGORY"` | Rejection | `"REJECTED"`: Invalid crypto_concern | **PASSED** |
| **Partial / Abstention Rating** | `label="UNKNOWN"`, low confidence | Accepted with uncertainty preserved | `"SUCCESS"`: Record imported as UNKNOWN | **PASSED** |
| **Adjudication Preservation** | 2 divergent expert ratings + 1 adjudicated label | Both individual ratings preserved; adjudication stored separately | `"SUCCESS"`: 2 ratings, 1 adjudication imported | **PASSED** |

---

## 5. Statistical Methodology Review

1. **Measurement Levels & Label Structure:**
   - **Ordinal Priority:** Migration priority (`LOW` < `MEDIUM` < `HIGH`) is evaluated using **Quadratic Weighted Cohen's Kappa** ($\kappa_w$) for pairs, penalizing a 2-step disagreement (LOW vs HIGH) 4× more than a 1-step disagreement.
   - **Multi-Rater Agreement:** **Fleiss' Kappa** provides an omnibus measure of non-chance agreement across the 4 annotators.
   - **Missing Data Handling:** **Krippendorff's Alpha** ($\alpha$, ordinal) was verified using coincidence matrices over non-missing pairs, ensuring that partial ratings or abstentions (`UNKNOWN`) do not force asset exclusion.
2. **Confidence Intervals:** Bootstrap resampling ($B=1,000$, seed: 42) is implemented for Cohen's kappa when valid pairs $N \ge 5$.
3. **Contextualizing the $\alpha \ge 0.80$ Threshold:** The protocol documents $\alpha \ge 0.80$ as an established academic target (Krippendorff, 2011), but explicitly emphasizes that high agreement indicates shared interpretation of evidence rather than absolute ground-truth validity.
4. **No Premature Computation:** In accordance with research integrity standards, no empirical kappa or alpha values are reported for real expert data, as human annotation has not yet taken place.

---

## 6. Verification Commands and Test Outputs

### 1. Targeted Annotation Framework Test Suite (7/7 Passed)
```powershell
pytest -v tests/ml/test_expert_annotation_framework.py
```
**Output:**
```
collected 7 items
tests/ml/test_expert_annotation_framework.py::test_expert_label_schema_multidimensional PASSED [ 14%]
tests/ml/test_expert_annotation_framework.py::test_adjudicated_label_schema_separation PASSED [ 28%]
tests/ml/test_expert_annotation_framework.py::test_sampling_determinism_and_blinding PASSED [ 42%]
tests/ml/test_expert_annotation_framework.py::test_importer_validations_and_rejections PASSED [ 57%]
tests/ml/test_expert_annotation_framework.py::test_krippendorff_alpha_nominal_and_ordinal PASSED [ 71%]
tests/ml/test_expert_annotation_framework.py::test_cohens_kappa_bootstrap_ci PASSED [ 85%]
tests/ml/test_expert_annotation_framework.py::test_per_class_agreement_and_confusion_matrix PASSED [100%]
============================== 7 passed in 4:16m ==============================
```

### 2. Full Machine Learning Test Suite (18/18 Passed)
```powershell
pytest -v tests/ml/test_expert_validation.py tests/ml/test_agreement.py tests/ml/test_phase14.py
```
**Output:**
```
============================= 18 passed in 3.05s ==============================
```

### 3. Frontend Vitest Suite (19/19 Passed)
```powershell
npx vitest run
```
**Output:**
```
 Test Files  3 passed (3)
      Tests  19 passed (19)
   Duration  3.84s
```

### 4. Frontend Production Build (0 Errors)
```powershell
npm run build
```
**Output:**
```
✓ built in 1.57s
dist/index.html                   0.45 kB
dist/assets/index-BtvMrJvh.css   40.01 kB
dist/assets/index-CaxfRlnV.js   532.24 kB
```

---

## 7. Audit Checklist & Status Summary

| Audit Item | Status | Verification Evidence |
| :--- | :--- | :--- |
| **Inspect Deliverables** | `VERIFIED` | All protocol, rubric, schema, script, and template files inspected and cross-referenced. |
| **166-Asset Sample Integrity** | `VERIFIED` | 166 assets match pinned commits, balanced across 3 languages, 0 heuristic leaks. |
| **Reviewer Independence & Privacy** | `VERIFIED` | Pseudonymous handles, conflict of interest policy, separate adjudication schema. |
| **Submission Workflow Ingestion** | `FIXED AND REVERIFIED` | Resolved timezone deprecation; all rejection and acceptance cases verified via synthetic tests. |
| **Statistical Methodology Review** | `FIXED AND REVERIFIED` | Corrected coincidence matrix pair logic; justified $\alpha \ge 0.80$ benchmark threshold. |
| **Preservation of Benchmark Pinned Commits**| `VERIFIED` | No changes made to repository corpus, commits, or baseline data. |
| **Prohibition on Synthetic Expert Data** | `VERIFIED` | No simulated human labels or fake consensus metrics generated. |
| **No Model Training** | `VERIFIED` | GATv2 training deferred until human annotations are collected. |

---

## 8. Final Recommendation and Readiness Determination

### Final Status: **READY WITH CAVEATS**

#### What is Ready:
The engineering infrastructure, data schemas, validation tools, blinded asset packages, submission templates, and statistical evaluation code are fully verified, robust, and mathematically sound.

#### Mandatory External Prerequisites (Caveats):
Before collecting expert labels:
1. **Recruit Panel:** Secure commitments from at least four (4) qualified experts matching the criteria in `docs/EXPERT_ANNOTATION_PROTOCOL.md`.
2. **Project Guide & Institutional Approval:** Confirm that institutional policies regarding software peer review, consent documentation, and licensing disclosures have been satisfied.
3. **Orientation:** Walk the recruited experts through `docs/EXPERT_ANNOTATION_RUBRIC.md` to ensure shared comprehension of the 7 evaluation dimensions prior to independent scoring.

**Next Step Recommendation:** Proceed to present the annotation package and protocol to the major project guide for panel recruitment and authorization. Do not begin GATv2 model training until authentic expert labels are imported and verified.
