# Claude Prompt: Implement One Plan Slice Cleanly

Use this prompt when you want Claude to implement a single slice from a project plan file.

```text
You are implementing exactly one slice from a project plan file in an existing codebase.

Plan file: {PLAN_FILE_PATH}
Target slice: {SLICE_NAME_OR_HEADING}

Your job is to:
1. Read the plan file and isolate only the requested slice.
2. Inspect the current codebase before changing anything.
3. Implement the slice fully and cleanly in the existing architecture.
4. Keep the codebase tidy: no dead code, no hanging TODO-only scaffolding, no half-wired features, no unused helpers, no placeholder branches left behind.
5. Prefer extending the correct existing files when that file already serves the purpose. Do not create duplicate files for logic that already has a home.
6. Create new files only when they clearly represent a distinct responsibility that does not already have an appropriate place.

Code organization rules:
- Separate files by purpose and responsibility.
- Do not create giant catch-all files.
- Do not put unrelated logic in the same file just because it is convenient.
- Avoid thousand-line files. If a file is getting large, split it by responsibility before it becomes unwieldy.
- Favor small, readable modules with clear names.
- Keep routes with routes, models with models, services with services, templates with templates, tests with tests, and utilities with utilities.
- If a file for this purpose already exists, work there instead of creating a new parallel version.
- If you must introduce a new file, make sure its purpose is obvious and narrow.

Implementation rules:
- Implement only the requested slice, plus any minimal supporting glue required for it to function correctly.
- Do not partially implement future slices.
- Do not leave behind speculative abstractions for work that is not part of this slice.
- Remove or avoid unused imports, unused functions, dead branches, commented-out blocks, and temporary debugging code.
- Ensure new code is actually wired into the app and reachable where required.
- Preserve existing project conventions unless the plan explicitly requires a change.
- Keep naming consistent with the plan and the existing codebase.

Testing and verification rules:
- Add or update tests that prove this slice works.
- Run the relevant tests and fix failures caused by your changes.
- Verify there is no orphaned code path created by this slice.
- If something in the plan conflicts with the current codebase, choose the smallest clean implementation and explain the tradeoff.

Process:
1. Summarize the requested slice in a few bullets.
2. Identify the existing files you will modify and why.
3. Implement the slice.
4. Run tests or other relevant verification.
5. Report:
- What you changed
- What files you touched
- What tests you ran
- Any assumptions or small tradeoffs

Quality bar:
- No dead code
- No hanging scaffolding
- No duplicate implementation paths
- No bloated files
- Clean separation of concerns
- Slice is complete, integrated, and test-backed
```

## Suggested use

Example values:
- `{PLAN_FILE_PATH}` -> `docs/phase1/plan.md`
- `{SLICE_NAME_OR_HEADING}` -> `Slice 2A - Hearing Data Layer`

If you want, I can also turn this into:
- a more aggressive prompt for stricter refactors
- a shorter copy-paste version for fast iteration
- a Codex/ChatGPT variant with the same constraints
