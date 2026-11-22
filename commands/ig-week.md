---
description: Pick this week's actions from the Instagram Brain and put them on Home
argument-hint: [focus, e.g. "quant" or "research internships"]
---
Plan this week from the Instagram Brain. Focus, if given: $ARGUMENTS

The vault is `{{VAULT}}`. Read its `CLAUDE.md` first and follow its rules.

## Gather
1. The `## From Instagram` sections in `Projects/Ideas/*.md`, `Career/Outreach/Outreach Templates.md`, `Career/Opportunities/Research Internship Sources.md` and `Career/Opportunities/Hackathons.md`.
2. Concept notes in `Learning/Concepts/` whose `next_review` is today or earlier.
3. `type: opportunity` notes with `verified: false` that came from Instagram (they link a note in `Instagram Brain/`).
4. Last week's block on `Home.md` (between the markers below), to see what was picked before and whether it moved.

## Pick (at most one of each)
- **Build**: one project idea that fits the focus, is not already a project note, and is small enough to start this week. Prefer ideas that strengthen the resume for the current focus in `Home.md`.
- **Reach out**: one outreach action using a technique from the outreach sources, aimed at a real person or lab relevant to the focus. Offer to draft it with `/ig-draft`; never send anything.
- **Verify**: one Instagram-sourced opportunity to check on its official page.
- **Review**: the concepts due, by name.

## Write
Replace everything between `<!-- ig-week:start -->` and `<!-- ig-week:end -->` in `Home.md` (add the markers at the end of the "Today" section if they are missing; never edit anything outside them):

```
<!-- ig-week:start -->
### 📌 This week from Instagram (YYYY-MM-DD)
- 🛠 Build: [[idea or source note]]: one line on the first step
- ✉️ Reach out: who and which technique ([[source note]])
- ✅ Verify: [[opportunity note]]
- 🧠 Review: [[Concept A]], [[Concept B]]
- ↩️ Last week: what happened to last week's picks (started / done / dropped / no change)
<!-- ig-week:end -->
```

If the user says they are starting the picked project, create a proper project note in `Projects/` from `Templates/Project.md` (status `active`) that links the idea and its source notes, and change nothing else in the ideas note except adding "→ started as [[Project]]" to that bullet.

Append one line to `Log.md`.
