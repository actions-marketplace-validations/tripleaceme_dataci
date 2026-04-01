# DataCI

**CI/CD for analytics engineering.**

DataCI posts a detailed report on every dbt pull request — showing **impact analysis**, **test coverage**, and **risk assessment** — so reviewers know exactly what changed and what it affects.

**No database connection needed. No profiles.yml setup. Just point it at your dbt project.**

---

## What You Get

Every PR that touches dbt models gets a comment like this:

> ### Changed Models
> | Model | Change |
> |-------|--------|
> | `stg_orders` | modified |
>
> ### Impact Analysis
> **4 downstream model(s)** affected | Risk: **MEDIUM**
> - `int_order_items`
> - `fct_orders`
> - `dim_customers`
> - `fct_revenue`
>
> ### Test Coverage
> **57.1%** (4/7 models tested)
>
> **Changed models missing tests:** `stg_payments`

---

## Quick Start

Add this workflow to your dbt project — **just 2 steps**:

```yaml
# .github/workflows/dataci.yml

name: DataCI
on:
  pull_request:
    paths:
      - 'models/**'
      - 'macros/**'
      - 'tests/**'
      - 'dbt_project.yml'

jobs:
  dataci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run DataCI
        uses: tripleaceme/dataci@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

That's it. No `dbt compile`, no `profiles.yml`, no adapter install. DataCI handles manifest generation automatically.

---

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github-token` | GitHub token for posting PR comments | Yes | `${{ github.token }}` |
| `project-dir` | Path to dbt project root | No | `.` |
| `manifest-path` | Path to a pre-built manifest.json (skip auto-generation) | No | _(auto-generated)_ |
| `dbt-version` | dbt-core version for manifest generation | No | `1.9.0` |
| `fail-on-missing-tests` | Fail if changed models have no tests | No | `false` |
| `coverage-threshold` | Minimum test coverage % (fails if below) | No | `0` |

---

## Usage Options

### Zero-config (recommended)

DataCI auto-generates the manifest — no dbt install or profiles.yml needed:

```yaml
- uses: tripleaceme/dataci@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### With pre-built manifest

If your CI pipeline already runs `dbt compile`, pass the manifest directly:

```yaml
- uses: tripleaceme/dataci@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    manifest-path: 'target/manifest.json'
```

### With quality gates

Block PRs that don't meet your standards:

```yaml
- uses: tripleaceme/dataci@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    fail-on-missing-tests: 'true'
    coverage-threshold: '60'
```

---

## Features

### Impact Analysis
When you change a model, DataCI traces the full downstream dependency graph and tells you:
- How many models are affected
- Which specific models are downstream
- Risk level (LOW / MEDIUM / HIGH) based on blast radius

### Test Coverage
DataCI calculates what percentage of your models have at least one dbt test and flags:
- Overall project coverage
- Changed models that are missing tests

### Quality Gates
Set `fail-on-missing-tests: true` to block PRs where new/changed models don't have tests. Set `coverage-threshold` to enforce a minimum coverage percentage.

### Smart Comment Updates
DataCI posts one comment per PR and updates it on subsequent pushes — no comment spam.

### Zero-Config Manifest Generation
DataCI reads your `dbt_project.yml`, creates a temporary dummy profile, and runs `dbt parse` to generate the manifest. No database connection or credentials needed — `dbt parse` only reads your SQL and YAML files.

---

## How It Works

1. DataCI reads `dbt_project.yml` and auto-generates a manifest (or uses one you provide)
2. It parses the manifest to build the full dependency graph
3. It diffs against the base branch to find changed models
4. It traces downstream impact and calculates test coverage
5. It posts (or updates) a single Markdown comment on the PR

---

## Requirements

- A dbt project with `dbt_project.yml`
- GitHub Actions enabled on your repository

That's it. DataCI handles the rest.

---

## Roadmap

- [x] Impact analysis
- [x] Test coverage reporting
- [x] Quality gates (fail on missing tests / low coverage)
- [x] Zero-config manifest generation
- [ ] AI-powered SQL review (Claude)
- [ ] Query cost estimation (BigQuery / Snowflake)
- [ ] Lineage visualization (Mermaid diagrams)

---

## License

MIT
