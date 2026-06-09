---
name: DECISION RECORD — Managed Agents (memory + dreaming) vs our hand-built Claude Code brain
description: s079 deep investigation (official Anthropic docs) of whether to adopt Claude Managed Agents memory stores + "dreaming" instead of our hand-built brain_v2. Verdict: we ARE ~80% reinventing, BUT Managed Agents is a SEPARATE product with NO Claude Code interoperability — adopting = abandoning Claude Code + rebuilding 45 skills/hooks/MCP. Recommendation: stay on Claude Code, selectively adopt DREAMING (AI curation, the one genuinely-better piece) via its API. User's call (strategy, rule #151).
type: project
---

# Decision Record — Managed Agents vs hand-built brain (s079)

User perception (correct): "por algo lo sacaron y nosotros estamos inventando." Investigated against
official docs. Verdict below.

## What Managed Agents is (cited)
- A SEPARATE product: a pre-built agent harness running in **Anthropic-managed cloud** (not your process).
  Distinct from Messages API, Agent SDK, and **Claude Code (CLI) — which is what we use**.
  [platform.claude.com/docs/en/managed-agents/overview]
- **Memory stores**: `POST /v1/memory_stores`; attached via `resources[]` **at session creation only**;
  mounted at `/mnt/memory/`; workspace-scoped; versioned (`memver_*`, 30-day); 2,000 memories/store,
  100kB each; read_write/read_only. **NOT auto-loaded** — each session must explicitly attach.
  [platform.claude.com/docs/en/managed-agents/memory]
- **"Dreaming"**: async job that reads a memory store + 1–100 session transcripts and outputs a NEW
  CURATED store (dedupe, resolve contradictions, surface insights). Manual trigger; research preview;
  request access. [platform.claude.com/docs/en/managed-agents/dreams]

## The decisive fact: NO Claude Code interoperability
Claude Code (local) and Managed Agents (cloud) are separate runtimes. A Claude Code session CANNOT
read/write Managed Agents memory stores; Managed Agents cannot use our skills/hooks/settings. No hybrid
path. To get auto-mount + dreaming for our brain, we'd have to MIGRATE OFF Claude Code to a hosted agent.

## Are we reinventing? ~80% YES (honest)
- `brain_state.json` ≈ a hand-rolled memory store (16 layers ≈ structured memories).
- `rebuild_all.py` ≈ a hand-rolled "dreaming" (manual dedupe/merge/gap-surface) — dreaming does it with
  Claude's reasoning, likely better at finding patterns.
- `incidents.json` / claims ≈ versioning + audit.
- ~20% is genuinely ours and not in the native model: the NetworkX **graph** structure (Managed Agents
  memory is document-oriented, not graph), the rule-severity hierarchy, force-include/blind-spot curation.

## What we'd LOSE by migrating (why full adoption is NOT worth it for us)
Interactive approval flow · local file control · the rebuild pipeline · 45 skills + hooks + MCP (port =
6–12 months) · ZDR eligibility. We are an INTERACTIVE, iterative dev team — Managed Agents is
fire-and-forget autonomous. Wrong fit for the daily workflow.

## What we'd GAIN — and the ONE piece worth taking
GAIN: auto-mount memory, **dreaming** (AI curation), version audit, async execution, proven-at-scale.
The single genuinely-better piece is **DREAMING** — AI-driven curation beats our hand-coded rebuild. And
it has an API: we can CALL dreaming from a Claude Code skill (request access, feed it our session
transcripts + a brain export, get a curated store back) WITHOUT abandoning Claude Code.

## RECOMMENDATION (user decides — strategy, rule #151)
**STAY on Claude Code + emulate/borrow, do NOT migrate:**
1. Auto-load: already hardened (SessionStart hook + CLAUDE.md STOP block + MEMORY pointer — s079).
2. Brain size: tiered loading (lean index at bootstrap, drill via graph_queries.py) — the real fix for
   the 400K-token problem, not migration.
3. Dreaming: optionally port as a Claude Code skill that calls the Managed Agents dreaming API monthly —
   take the better curation WITHOUT the platform lock-in.
4. Keep the graph + rule hierarchy + curation (the ~20% that's genuinely better than the flat native model).

Net: we built the RIGHT wheel for an interactive knowledge-first team; the native product optimizes for
hosted autonomous deployment. Borrow dreaming; don't migrate. (Access form:
https://claude.com/form/claude-managed-agents)

## Sources (official)
managed-agents/overview · managed-agents/memory · managed-agents/dreams · agent-sdk/overview ·
claude.com/blog/new-in-claude-managed-agents
