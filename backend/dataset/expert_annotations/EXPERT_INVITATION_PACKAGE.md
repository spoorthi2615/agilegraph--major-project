# AgileGraph Independent Expert Review Invitation Package

This document contains everything needed to invite, brief, and collect reviews from cybersecurity professionals and cryptography researchers for the **AgileGraph** final-year major project at NMAMIT.

---

## 1. Ready-to-Send Email Template

Copy and personalize the email below when reaching out to prospective reviewers:

```text
Subject: Invitation: Expert Review of Post-Quantum Cryptographic Migration Risk Scoring (B.Tech Research Project)

Dear [Expert Name / Title],

We are final-year B.Tech Cyber Security students at NMAM Institute of Technology (NMAMIT), Nitte (Deemed to be University), Karnataka, conducting our major project under the guidance of Assistant Professor Ms. Madhushree.

Our research project, AgileGraph, investigates graph-learned and heuristic risk scoring for prioritizing cryptographic migration to post-quantum standards (NIST FIPS 203/204/205).

To independently evaluate and scientifically validate our risk models against human domain expertise, we are conducting a blinded expert validation study. We would be honored to include your expert assessment in our research panel.

What is involved?
- Scope: Reviewing a curated sample of cryptographic assets (source code files containing cryptographic algorithms across Python, Java, and Go).
- Task: Classifying each asset into HIGH, MEDIUM, or LOW post-quantum migration risk based on the cryptographic primitive, exposure, and data shelf-life.
- Time commitment: Approximately 30–45 minutes.
- Confidentiality & Independence: All assessments are blinded (you will not see machine-predicted scores). You may choose to be acknowledged by name/affiliation in our project thesis or remain anonymous.

How to participate:
1. Review the attached Labelling Guide and Instructions.
2. Complete the attached Review Sheet (available as an Excel/CSV spreadsheet or JSON template).
3. Reply to this email with your completed sheet by [Target Date, e.g., November 25, 2026].

We have attached:
• Attachment 1: AgileGraph_Review_Sheet.xlsx (Excel spreadsheet with dropdown selectors for risk levels)
• Attachment 2: AgileGraph_Labelling_Guide.pdf (rubric, guidelines, and worked examples)

Thank you very much for your time and for supporting student cybersecurity research!

Sincerely,
Student Investigators:
- Spoorthi (USN: NNM23CB058)
- Sindhoora R (USN: NNM23CB057)
- Nivedita V Shetty (USN: NNM23CB033)
- Sujan S (USN: NNM23CB062)

Project Guide:
Ms. Madhushree, Assistant Professor
Department of Computer Science and Engineering (Cyber Security)
NMAM Institute of Technology (NMAMIT), Nitte, Karnataka
Contact Email: [Your Team / Guide Email Address]
```

---

## 2. Reviewer Briefing & Step-by-Step Instructions

### Step 1: Open the Review Workbook
Open `AgileGraph_Review_Sheet.xlsx` in Microsoft Excel, Google Sheets, or LibreOffice Calc.

### Step 2: Fill Reviewer Profile (Sheet 1)
Click on the first tab **"Reviewer Profile & Rubric"** and complete cells **B5–B9**:
- **B5 (Reviewer Name / Pseudonym)**: Your name or preferred pseudonym for anonymous inclusion.
- **B6 (Years of Experience)**: Total years in applied cryptography, cybersecurity, or secure software engineering.
- **B7 (Professional Role)**: e.g., *Senior Security Architect, Cryptography Researcher, Penetration Tester*.
- **B8 (Institutional Affiliation)**: Enterprise, academic institution, or independent security practice.
- **B9 (Date of Review)**: Date completed (YYYY-MM-DD).

### Step 3: Classify Cryptographic Assets (Sheet 2)
Switch to the second tab **"Asset Review (160)"**. Each row represents a cryptographic source code file with pre-filled context:
- **Columns A–D (Read-Only Context)**: File path, benchmark repository, programming language, and detected cryptographic primitives.
- **Column E (Expert Assigned Risk)**: Click the cell to open the dropdown menu and select:
  - `HIGH`: Immediate migration priority (e.g., RSA, ECC, broken classical digests).
  - `MEDIUM`: Intermediate / scheduled migration priority (e.g., AES-128, key wrappers).
  - `LOW`: Post-quantum resilient / negligible risk (e.g., ML-KEM, ML-DSA, AES-256, SHA-256).
- **Column F (Expert Confidence)**: Enter your confidence level from `0.0` (uncertain) to `1.0` (completely certain).
- **Column G (Expert Rationale)**: A concise 1–2 sentence explanation of your decision.

### Step 4: Save & Return
Save the workbook as `.xlsx` and reply to the invitation email with the completed file attached.

---

## 3. Reference Summary Rubric

For in-depth explanations, criteria, and worked examples, refer to the attached **`AgileGraph_Labelling_Guide.pdf`**.

| Risk Tier | Criteria & Affected Primitives | Cryptographic Justification |
| :---: | :--- | :--- |
| **HIGH** | • **Shor's Algorithm Targets**: RSA ($\le 4096$b), ECC (ECDSA, ECDH, Ed25519, P-256), DSA, DH.<br>• **Broken Classical Primitives**: MD5, SHA-1, DES, 3DES, RC4.<br>• **Harvest Now, Decrypt Later (HNDL)**: Confidentiality lifetimes extending into the quantum capability horizon. | A Cryptanalytically Relevant Quantum Computer (CRQC) solves discrete logarithms and integer factorization in polynomial time. Immediate migration to NIST FIPS 203/204 is required. |
| **MEDIUM** | • **Constrained Symmetric Keys**: AES-128 or legacy block ciphers.<br>• **Transitional Deployments**: Incomplete hybrid encapsulation.<br>• **High-Centrality Wrappers**: Cryptographic abstractions where refactoring is complex. | Grover's search algorithm ($O(\sqrt{N})$) halves effective symmetric key length (AES-128 reduced to 64-bit security). Migration to 256-bit symmetric keys is advised. |
| **LOW** | • **Standard Post-Quantum Algorithms**: NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA).<br>• **Quantum-Resistant Symmetric Primitives**: AES-256, ChaCha20-Poly1305, SHA-256, SHA-384, SHA-512, SHA-3, HMAC ($\ge 256$ bits).<br>• **Non-Security Usage**: Hash functions used strictly for non-adversarial hash tables or cache keys. | AES-256 retains 128 bits of post-quantum security against Grover's algorithm, which remains computationally infeasible. |

---

## 4. Research Confidentiality & Ethics

- **Blinded Evaluation**: Reviewers evaluate code assets without visibility into automated heuristic scores or GNN predictions to ensure unbiased independent validation.
- **Independence**: Reviewers are requested not to discuss or compare classifications with other reviewers prior to submission.
- **Attribution**: You may indicate in your profile whether you wish to be formally acknowledged in our final thesis and publication or remain anonymous.
- **Post-Hoc Validation Only**: Your evaluations are solely used as a post-hoc evaluation ground truth for computing inter-rater reliability ($\kappa$) and classification performance ($F_1$). Expert annotations are never injected into GNN model weights or training loops.

