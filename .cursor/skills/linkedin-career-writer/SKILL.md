---
name: linkedin-career-writer
description: LinkedIn profile writing and career outreach toolkit. Covers LinkedIn headlines, About section, experience entries, cold recruiter messages, and interview preparation. Use when the user mentions LinkedIn, headline, About section, recruiter message, cold outreach, interview questions, or interview prep.
---

# LinkedIn & Career Writer

## Auto-load resume context

Before starting, check if the user provided their background. If not, read from this repo:
- English: `Roy-Resume-EN.md`
- Chinese: `Roy-Resume-中文.md`

Inform the user which file you loaded.

---

## LinkedIn headline

**Trigger**: user wants a LinkedIn headline

Generate 5 options. Each headline:
- Under 220 characters
- Format options to vary: `Title | Value prop | Niche`, `Outcome I deliver | Tool/domain`, `Who I help + How`
- Keyword-rich for LinkedIn search
- No buzzwords: "passionate", "guru", "ninja", "rockstar"

Present as a numbered list with a 1-line rationale per option.

---

## LinkedIn About section

**Trigger**: user wants to write or rewrite their About section

Structure:
1. **Hook** (1–2 lines): What you do and for whom — no "I am a dedicated professional"
2. **What you've built / delivered** (2–3 bullets or short paragraph): concrete results
3. **What makes you different**: your approach, perspective, or specialty
4. **What's next**: what you're looking for or open to
5. **CTA**: email or "Let's connect"

Length: 250–350 words. First-person, conversational but professional. Write for humans, not HR bots.

---

## LinkedIn experience entries

**Trigger**: user wants to rewrite work history for LinkedIn

Per role:
- **Headline**: `[Title] @ [Company] — [1-line value statement]`
- **3–5 bullets**: achievement-first, metrics where possible
- Same bullet formula as resume: `[Verb] + [what] + [impact]`

LinkedIn-specific: slightly more narrative than resume, context about company size/stage is valuable.

---

## Cold recruiter message

**Trigger**: user wants to reach out to a recruiter or hiring manager on LinkedIn

Default template structure:
```
Hi [Name],

[1 sentence: specific reason you're reaching out — role, company, or their background]

[1–2 sentences: what you bring that's relevant to the role]

[Ask: clear, low-friction — "Would you be open to a quick chat?" or "Happy to share my resume if helpful."]

[Your name]
```

- Under 100 words
- Do not open with "I hope this message finds you well"
- Personalize the opening line — reference something specific about the role or company

If the user provides a recruiter's name and role, generate a ready-to-send message.

---

## Interview preparation

**Trigger**: user wants to prepare for a specific interview

1. **Generate 10–12 likely questions** based on the JD and resume:
   - 3–4 behavioral (STAR format expected)
   - 3–4 role-specific technical / functional
   - 2–3 situational / judgment-based
   - 1–2 culture/motivation

2. **For each question**, provide:
   - Why interviewers ask it
   - A strong sample answer drawn from the user's actual experience
   - What to avoid saying

3. **Closing questions to ask the interviewer** (3–5 options)

STAR format reminder for behavioral answers:
- **S**ituation: brief context
- **T**ask: your responsibility
- **A**ction: what you specifically did
- **R**esult: measurable outcome

---

## Quality standards (all modes)

- Write in the user's voice — match their existing tone if sample text is available
- Confident, not arrogant. Specific, not generic.
- Avoid: "passionate about", "results-driven", "team player", "go-getter"
- Always optimize for the specific role/company when context is given
