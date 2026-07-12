# Contributing

Thanks for considering a contribution to Felicity Solar Local!

## Dev setup

```console
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
```

## Running checks

```console
ruff check .
pytest
```

Both must pass before a PR can be merged (enforced by CI - see `.github/workflows/test.yml`
and `validate.yml`, which also run `hassfest` and the HACS validation action).

## Adding a new battery model profile

If you have a Felicity Solar WiFi battery that isn't the FLB48314TG1-H:

1. Run `python3 scripts/probe.py <your-battery-ip>` and note the `Type`/`SubType` it prints.
2. Compare its raw JSON shape to `tests/fixtures/sample_response.json`.
3. Add a new `BatteryProfile` in `custom_components/felicity_solar_local/profiles.py`,
   matched by your device's `Type`/`SubType`, and add it to the `PROFILES` tuple. Only mark
   `confidence="verified"` if you've cross-checked field scaling against another known-good
   source for that same battery (e.g. its cloud app, if it has one).
4. Add a corresponding test fixture and test cases in `tests/test_profiles.py`.

## Commit messages

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) for every commit:

```
<type>[optional scope]: <description>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`. This is required, not
just a style preference - `release-please` parses commit history on `main` to decide the next
version number and changelog. A `BREAKING CHANGE:` footer triggers a major version bump.

`.github/workflows/commitlint.yml` enforces this automatically by checking that your PR title
follows Conventional Commits - it'll fail the check if it doesn't. If you squash-merge, GitHub
uses the PR title as the commit message on `main`, so a correctly formatted title is what
`release-please` actually sees.

## Release process

- Every PR gets its own pre-release build automatically (`.github/workflows/pr-prerelease.yml`)
  - a GitHub Release tagged `pr-<number>` with a zip of the integration, so you can install and
    test your change with HACS before it merges.
- Once merged to `main`, `release-please` (`.github/workflows/release-please.yml`) maintains a
  standing "Release PR" that aggregates unreleased Conventional Commits. Merging that PR bumps
  `manifest.json`'s version, tags the release, and publishes it - no manual version bumping.

## Pull requests

Keep PRs focused. Include tests for behavior changes. If you're changing scaling/field mapping
in `profiles.py`, explain in the PR description how you verified the new values (what you
compared against) - that verification is what the `confidence` field on `BatteryProfile` is
meant to reflect honestly.
