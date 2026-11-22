---
description: Turn distilled Instagram notes into project ideas, opportunities, outreach templates and concepts
argument-hint: [area or folder] [count, default 10]
---
Promote distilled notes: $ARGUMENTS

The vault is `{{VAULT}}`. Work only on notes in `Instagram Brain/` with `status: distilled` and no `promoted:` field (filtered by area or folder if one is given, at most the count asked for, default 10).

Follow the vault's own `CLAUDE.md` rules: frontmatter first, use the templates in `Templates/`, never edit the owner's existing text, and separate what a post says from your own inference.

For each note, decide what it is useful for, and do only the steps that apply:

| The note is about | Do this |
|---|---|
| A project idea or build tutorial | Append a bullet under `## From Instagram` at the end of the matching ideas note in `Projects/Ideas/` (`AIML PROJECTS.md`, or create `QUANT PROJECTS.md` with the same frontmatter as `AIML PROJECTS.md` and `domain: quant`). Bullet: idea in one line, difficulty (easy/medium/hard), resume angle, `[[source note]]`. |
| A specific named program, internship, fellowship, hackathon or competition | Create a note in `Career/Opportunities/Research/` (or `Career/Opportunities/` for hackathons) from `Templates/Opportunity.md`, with `verified: false` and empty `deadline`. Never fill eligibility or deadlines from Instagram; they must come from the official page later. Link the source note. |
| A general source of opportunities (job boards, where to find internships, hackathon platforms) | Append a bullet under `## From Instagram` in `Career/Opportunities/Research Internship Sources.md` or `Career/Opportunities/Hackathons.md`. |
| Cold email or outreach technique, or a message template | Append it under `## From Instagram` in `Career/Outreach/Outreach Templates.md`: the technique in one or two lines plus `[[source note]]`. Do not paste a template the note marks as not captured. |
| A concept worth learning (an algorithm, a math idea, a tool) | Create a concept note in `Learning/Concepts/` from `Templates/Concept.md` with `review_stage: 0`, `next_review` tomorrow, `confidence: low`, `sources: [[source note]]`. |
| Content creation technique (hooks, editing, fonts, shot styles) | Append under `## From Instagram` in `Instagram Brain/Content Creation/Content Playbook.md` (create it with `type: reference` if missing), grouped by Hooks, Editing, Visual style, Audio. |
| Nothing actionable | Skip it. |

Then on the source note:
- Add `promoted: [<target note names>]` to the frontmatter (or `promoted: []` if skipped), so it is not processed twice.
- Add the targets to its `## Related` section as wikilinks.

Finish by appending one line to `Log.md` that lists how many notes were promoted and where they went. Do not create a `## From Instagram` section twice in the same note; append to the existing one.
