# GitHub Actions Workflows Guide

This document describes all GitHub Actions workflows in this repository.

## Existing Workflows

### 1. **tests.yml** - Unit Tests
- **When**: Push/PR to main, develop, feature/port-3000-default
- **What**: Runs pytest tests with PostgreSQL
- **Features**: Coverage reporting, Codecov integration

### 2. **deploy-check.yml** - Deployment Health Checks
- **When**: Push/PR to main, develop, feature/port-3000-default
- **What**: Builds dashboard, starts services, tests health endpoints
- **Features**: Validates deployment readiness

### 3. **mutation-testing.yml** - Mutation Testing
- **When**: PR on security code, weekly schedule
- **What**: Runs mutmut on security-critical code
- **Features**: Generates mutation reports

### 4. **npm-publish.yml** - NPM Publishing
- **When**: Release creation
- **What**: Publishes package to NPM registry

## New Workflows Added

### 5. **lint.yml** - Code Quality Checks ⭐ NEW
- **When**: Push/PR to main, develop, feature/port-3000-default
- **What**: 
  - Ruff linting and formatting checks
  - mypy type checking (non-blocking)
  - Bandit security scanning
- **Why**: Enforces code quality standards automatically

### 6. **security.yml** - Security Analysis ⭐ NEW
- **When**: Push/PR to main/develop, weekly schedule
- **What**: 
  - CodeQL analysis (Python & JavaScript)
  - Dependency review on PRs
- **Why**: Proactive security vulnerability detection

### 7. **docker.yml** - Docker Build & Push ⭐ NEW
- **When**: Push to main/develop, tags (v*.*.*), PRs, manual dispatch
- **What**: 
  - Builds multi-platform Docker images (amd64, arm64)
  - Pushes to GitHub Container Registry (ghcr.io)
  - Uses build cache for faster builds
- **Why**: Automated container image publishing

### 8. **release.yml** - Release Automation ⭐ NEW
- **When**: Tag push (v*.*.*) or manual dispatch
- **What**: 
  - Creates GitHub releases
  - Generates changelog from git commits
  - Marks as pre-release if version contains `-`
- **Why**: Streamlined release process

### 9. **docs.yml** - Documentation Checks ⭐ NEW
- **When**: Push/PR when markdown files change
- **What**: 
  - Spell checking (optional, non-blocking)
  - Link validation
- **Why**: Maintains documentation quality


## Recommended Additional Workflows

### 11. **dependabot.yml** - Dependency Updates
Enable Dependabot in GitHub Settings → Security → Dependabot:
- Automated dependency updates
- Security patches
- Version updates

### 12. **stale.yml** - Stale Issue/PR Management
Consider adding to automatically close stale issues/PRs after inactivity.

## Configuration Needed

### GitHub Secrets Required

1. **PyPI Publishing** (`pypi-publish.yml`):
   - Set up trusted publishing in PyPI
   - No token needed (uses OIDC)

2. **NPM Publishing** (existing):
   - `NPM_TOKEN` - Already configured

3. **Optional**:
   - `OPENAI_API_KEY` - For tests that require OpenAI (optional, uses Ollama fallback)
   - `CODECOV_TOKEN` - If using private Codecov (optional)

### GitHub Settings to Enable

1. **Dependabot**: 
   - Settings → Security → Dependabot → Enable
   - Configure update frequency

2. **CodeQL**:
   - Settings → Security → Code security and analysis
   - Enable "Code scanning" (used by security.yml)

3. **GitHub Container Registry**:
   - Packages are automatically created when docker.yml runs
   - Settings → Actions → General → Enable "Read and write permissions" for GITHUB_TOKEN

4. **Trusted Publishing for PyPI**:
   - PyPI → Account → Manage projects → Add trusted publisher (when ready)
   - Owner: `jreakin`, Repository: `MCP-Agent-Maestro`, Workflow: `pypi-publish.yml`
   - Can add `pypi-publish.yml` workflow later when ready to publish

## Workflow Execution Order

On a typical PR or push:

1. **lint.yml** - Quick code quality checks
2. **security.yml** - Security scanning (runs in parallel)
3. **tests.yml** - Unit tests with coverage
4. **deploy-check.yml** - Deployment validation
5. **docs.yml** - Documentation checks (only if docs changed)

On release/tag:

1. **docker.yml** - Build and push container images
2. **release.yml** - Create GitHub release with changelog
3. **npm-publish.yml** - Publish to NPM (if Node package)

**Note**: PyPI publishing workflow can be added later when ready.

## Customization

### Adjusting Workflow Triggers

Edit the `on:` section in each workflow file to change when it runs:
- Branch filters
- Path filters
- Schedule (cron)

### Adding More Checks

Consider adding:
- Performance benchmarks
- Bundle size checks (for dashboard)
- License compliance checks
- API contract testing
- Visual regression testing

## Monitoring

View workflow runs at:
- **Actions tab**: https://github.com/jreakin/MCP-Agent-Maestro/actions
- **Security tab**: For CodeQL and Dependabot alerts
- **Packages tab**: For Docker images published

## Local Testing

See `.github/workflows/README-TESTING.md` for instructions on testing workflows locally with `act`.

