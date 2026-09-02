# IdeaPartner Canonical Skill Name

## Goal

Make `ideapartner` the single canonical package, folder, invocation, and UI identity for both standalone skill installation and plugin distribution.

## Design

- Rename `skills/research-idea-review` to `skills/ideapartner`.
- Set the skill frontmatter name to `ideapartner` and its UI display name to `IdeaPartner`.
- Use `$ideapartner` in the default prompt and public installation documentation.
- Release the correction as `v1.1.1`; do not move the immutable `v1.1.0` tag.
- Add distribution assertions that bind the folder name, skill frontmatter, UI metadata, plugin manifest, and runtime version.

## Verification

- Run the full unit and distribution test suite.
- Run the bundled skill and plugin validators.
- Install from the eventual `v1.1.1` tag and verify the installed runtime reports `1.1.1`.
- Remove the legacy local `research-idea-review` installation only after the canonical tagged installation succeeds.
