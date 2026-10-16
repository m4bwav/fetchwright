# Log

Append-only. One line per operation: `## [YYYY-MM-DD] op | title` where op is one of add, update, supersede, verify, verify-failed, prune, handoff, index. Newest at the bottom. Never edited, only appended; this is the history the entries themselves do not carry.

## [2026-10-15] init | scaffolded
## [2026-10-15] add | solution: Word-for-word page copies are blocked as recitation; ask for a digest
## [2026-10-15] add | decision: fetchwright as a standalone public plugin with a stdlib CLI
## [2026-10-15] handoff | 0.1.0 built and pushed; CI green; installed fetchwright@mark-local; everscout PR #18 merged; evals and wiki open
## [2026-10-15] add | v0.1.0 released; wiki written and live (9 pages, verified against the tag through an API stand-in); README budget table fixed; --json cut found (0.1.1 candidate)
## [2026-10-15] index | rebuilt (4 entries)

## [2026-10-16] build | a 429 on one model's quota moves to the next model (PR #2, merged, unreleased)
everscout's first live run hit the free tier's 20-a-day limit on gemini-3.8-flash and fetchwright stopped although flash-lite had quota. Mark agreed to fall through on a per-model quota 429. Lessons L-004 and L-005 (PR #1). everscout runs this clone through its `fetchwright.cli` config until a 0.2.0 release, which needs Mark's go-ahead.
## [2026-10-16] release | fetchwright 0.2.0: the quota fall-through (PR #2), every version field bumped, README budget table refreshed (all green); released on the owner's go-ahead
