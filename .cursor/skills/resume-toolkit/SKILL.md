---
name: resume-toolkit
description: Professional resume writing and optimization toolkit. Covers building resumes from scratch, rewriting for ATS, turning task lists into achievement bullets, keyword extraction, skill gap analysis, and per-job customization. Use when the user mentions resume, CV, ATS, job application, job description, achievement bullets, or keyword optimization.
---

# Resume Toolkit

## Auto-load resume context

Before starting, check if the user provided their resume. If not, read the appropriate file from this repo:
- English: `Roy-Resume-EN.md`
- Chinese: `Roy-Resume-中文.md`

Inform the user which file you loaded. If they want to use a different version, ask.

---

## Build from scratch

**Trigger**: user wants a resume created from raw info

- Target role: extract from job description or ask
- Produce clean, ATS-friendly format: Header → Summary → Experience → Skills → Education
- Every bullet: `[Action verb] + [task/project] + [measurable result]`
- Mirror exact keywords from the job description
- No tables, no graphics, no columns (ATS compatibility)

---

## Optimize existing resume

**Trigger**: user has a resume and wants it improved for a specific role

1. Read the existing resume (auto-loaded or pasted)
2. Read the job description
3. Identify: weak verbs, missing keywords, vague bullets, poor formatting
4. Rewrite section by section
5. Output: revised resume + a brief change log of what was improved and why

---

## Rewrite bullets into achievements

**Trigger**: user pastes task/responsibility bullets that read like a job description

Transform each bullet using:
```
[Strong action verb] + [what you did] + [impact / metric / result]
```

Examples:
- Before: `Responsible for managing social media`
- After: `Grew Instagram following 40% in 6 months by launching weekly video series`

If no metric is given, prompt the user: "Do you have a number for this?" before inventing one.

---

## Keyword optimization (ATS boost)

**Trigger**: user wants to improve ATS match score

1. Extract top 15–20 keywords from the job description (skills, tools, titles, verbs)
2. Compare against current resume
3. List: ✅ already present | ⚠️ present but weak | ❌ missing
4. Rewrite or suggest placements for missing/weak keywords
5. Keep language natural — never keyword-stuff

---

## Skill gap analysis

**Trigger**: user wants to know what's missing vs. the job requirements

Produce a table:

| Requirement | Status | Recommendation |
|---|---|---|
| Python | ✅ Strong | Highlight in summary |
| AWS | ⚠️ Implicit | Add explicit project example |
| Team lead | ❌ Missing | Reframe Project X or note it's a growth area |

End with: top 3 actionable suggestions ranked by impact.

---

## Cover letter

**Trigger**: user wants a cover letter for a specific job

- Length: 3 paragraphs, under 300 words
- Para 1: Hook — why this role, what you bring
- Para 2: 2–3 concrete achievements directly relevant to the JD
- Para 3: Forward-looking close, specific ask

Tone: confident, not sycophantic. No "I am very excited" opener.

---

## Per-job customization

**Trigger**: user has a base resume and wants a version tailored to a specific JD

1. Identify the top 5 requirements in the JD
2. Reorder resume sections to front-load the most relevant experience
3. Rewrite summary to mirror the role's language
4. Adjust bullet points — emphasize what the role cares about
5. Output the full customized resume, ready to submit

---

## Quality standards

- Action verbs: Led, Built, Reduced, Increased, Launched, Designed, Managed, Delivered
- Avoid: "Responsible for", "Helped with", "Worked on", "Assisted"
- Metrics wherever possible: %, $, time saved, team size, scale
- ATS rules: single column, standard section headers, no text boxes
- Bullet length: 1–2 lines max
