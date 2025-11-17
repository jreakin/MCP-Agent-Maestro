# Publishing Guide

Guide for publishing Agent-MCP as an npm package.

## Prerequisites

1. **npm account** with access to `@rinadelph` scope
2. **GitHub access** for releases
3. **Python package** properly configured in `pyproject.toml`

## Pre-Publishing Checklist

- [ ] Update version in `package.json` and `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Run tests: `npm test` and `pytest`
- [ ] Build TypeScript (if applicable): `npm run build`
- [ ] Verify postinstall script works
- [ ] Test installation in clean environment
- [ ] Update documentation

## Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## Publishing Steps

### 1. Prepare Release

```bash
# Update version
npm version patch  # or minor, major

# This automatically:
# - Updates package.json version
# - Creates git tag
# - Commits changes
```

### 2. Build Package

```bash
# Build TypeScript (if applicable)
npm run build

# Verify package contents
npm pack --dry-run
```

### 3. Test Installation

```bash
# Test in clean directory
mkdir /tmp/agent-mcp-test
cd /tmp/agent-mcp-test
npm install /path/to/Agent-MCP

# Verify installation
agent-mcp --help
```

### 4. Publish to npm

```bash
# Dry run first
npm publish --dry-run

# Publish to npm
npm publish --access public

# Or publish to specific registry
npm publish --registry https://registry.npmjs.org/
```

### 5. Create GitHub Release

```bash
# Push tags
git push --tags

# Create release on GitHub (manual or via GitHub CLI)
gh release create v2.5.0 --notes "Release notes here"
```

## Automated Publishing

GitHub Actions workflow (`.github/workflows/npm-publish.yml`) automatically publishes on release tags.

### Manual Trigger

```bash
# Create and push tag
git tag v2.5.0
git push origin v2.5.0
```

## Post-Publishing

1. Verify package on npm: https://www.npmjs.com/package/@rinadelph/agent-mcp
2. Test installation: `npm install -g @rinadelph/agent-mcp`
3. Update documentation with new version
4. Announce release in Discord/community

## Troubleshooting

### "Package name already exists"
- Check if version already published
- Increment version number

### "Authentication failed"
- Run `npm login`
- Verify npm token permissions

### "Python dependencies not installing"
- Check postinstall script
- Verify uv is available
- Check Python version compatibility

## Rollback

If a bad version is published:

1. **Deprecate version:**
   ```bash
   npm deprecate @rinadelph/agent-mcp@2.5.0 "Reason for deprecation"
   ```

2. **Publish fix:**
   - Increment version
   - Fix issues
   - Publish new version

## Best Practices

1. **Always test** in clean environment before publishing
2. **Use semantic versioning** consistently
3. **Write clear release notes**
4. **Tag releases** in git
5. **Monitor** npm download stats
6. **Respond** to issues quickly

---

For questions, see [Contributing Guide](../CONTRIBUTING.md) or [Discord Community](https://discord.gg/7Jm7nrhjGn).

