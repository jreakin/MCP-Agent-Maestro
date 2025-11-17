# Troubleshooting Guide

Common issues and solutions for Agent-MCP setup and usage.

## Installation Issues

### "Python version not found" or "Python 3.10+ required"

**Problem:** Python 3.10 or higher is not installed or not in PATH.

**Solution:**
```bash
# Check Python version
python --version  # Should be 3.10+

# If not installed, install Python 3.10+ from python.org
# Or use pyenv to manage versions:
pyenv install 3.11.0
pyenv local 3.11.0
```

### "uv: command not found"

**Problem:** uv package manager is not installed.

**Solution:**
```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Verify installation
uv --version
```

### "npm: command not found"

**Problem:** Node.js/npm is not installed.

**Solution:**
```bash
# Install Node.js from nodejs.org
# Or use nvm:
nvm install 18
nvm use 18

# Verify installation
node --version  # Should be >=18.0.0
npm --version   # Should be >=9.0.0
```

### "ModuleNotFoundError: No module named 'agent_mcp'"

**Problem:** Package not installed or virtual environment not activated.

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall package
uv pip install -e .
```

---

## Server Startup Issues

### "Admin token not found"

**Problem:** Server startup doesn't display token.

**Solution:**
1. Check server logs: `tail -f logs/mcp-server.log` (if logging enabled)
2. Ensure server started successfully - look for "Server running on..." message
3. Check for errors in terminal output
4. Verify environment variables are set correctly

### "Port already in use"

**Problem:** Port 8080 (or specified port) is occupied.

**Solution:**
```bash
# Find process using the port
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Kill the process or use a different port
uv run -m agent_mcp.cli --port 8081 --project-dir /path/to/project
```

### "Database connection failed"

**Problem:** Cannot connect to database.

**Solution:**
1. **For SQLite (default):**
   - Check file permissions on `.agent/` directory
   - Ensure disk space is available
   - Verify project directory is writable

2. **For PostgreSQL:**
   - Verify `DATABASE_URL` environment variable is set
   - Check PostgreSQL is running: `pg_isready`
   - Verify credentials and database exists
   - Check network connectivity

### "OpenAI API Error"

**Problem:** Invalid or missing API key.

**Solution:**
1. Verify key is set:
   ```bash
   echo $OPENAI_API_KEY  # Should show your key
   ```

2. Check key validity at [platform.openai.com](https://platform.openai.com)

3. Ensure `.env` file is in correct location (project root)

4. Verify `.env` file format:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   # No quotes, no spaces around =
   ```

5. Restart the server after changing `.env`

---

## Dashboard Issues

### "Dashboard connection failed"

**Problem:** Dashboard cannot connect to MCP server.

**Solution:**
1. Ensure MCP server is running first
2. Check server URL in dashboard settings (default: `http://localhost:8080`)
3. Verify CORS is enabled (should be by default)
4. Check browser console for errors
5. Verify firewall isn't blocking connections

### "Dashboard shows 'No server connected'"

**Problem:** Dashboard cannot reach the MCP server.

**Solution:**
1. Check server is running: `curl http://localhost:8080/api/status`
2. Verify server URL in dashboard matches server port
3. Check for CORS errors in browser console
4. Try refreshing the dashboard

### "npm install fails"

**Problem:** npm package installation errors.

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# If using Node 18+, ensure compatibility
node --version  # Should be >=18.0.0
```

---

## Agent Issues

### "Worker can't access tasks"

**Problem:** Agent cannot retrieve assigned tasks.

**Solution:**
1. Ensure you're using the worker token (not admin token) when initializing workers
2. Verify agent was created successfully
3. Check task assignment in dashboard
4. Verify database connectivity

### "Agents overwriting each other"

**Problem:** Multiple agents modifying the same files.

**Solution:**
1. Verify all workers are initialized with the `--worker` flag
2. Check file locking is enabled (should be automatic)
3. Review task assignments to ensure no overlap
4. Check dashboard for file lock status

### "Agent stuck or not responding"

**Problem:** Agent appears frozen or unresponsive.

**Solution:**
1. Check agent status in dashboard
2. Review agent logs (if available)
3. Terminate and recreate the agent
4. Verify OpenAI API quota/rate limits
5. Check for network connectivity issues

---

## RAG/Memory Issues

### "Memory queries returning stale data"

**Problem:** RAG system returns outdated information.

**Solution:**
```bash
# Run memory garbage collection through dashboard
# OR restart with refresh flag:
uv run -m agent_mcp.cli --refresh-memory --project-dir /path/to/project

# Re-index project:
uv run -m agent_mcp.features.rag.indexing --project-dir /path/to/project
```

### "RAG query fails"

**Problem:** RAG queries return errors.

**Solution:**
1. Verify OpenAI API key is valid
2. Check API quota/rate limits
3. Ensure vector database is initialized
4. Check database connectivity
5. Review error logs for specific issues

---

## Security Issues

### "Security scan blocking legitimate content"

**Problem:** False positives from security scanner.

**Solution:**
1. Adjust security sensitivity in `.env`:
   ```bash
   AGENT_MCP_SANITIZATION_MODE=neutralize  # Instead of 'remove'
   ```

2. Review security alerts in dashboard
3. Whitelist specific patterns if needed
4. Temporarily disable for testing:
   ```bash
   AGENT_MCP_SECURITY_ENABLED=false
   ```

### "Security alerts not appearing"

**Problem:** Security monitoring not working.

**Solution:**
1. Verify security is enabled:
   ```bash
   echo $AGENT_MCP_SECURITY_ENABLED  # Should be 'true'
   ```

2. Check security monitor is initialized
3. Review server logs for security warnings
4. Test with known malicious pattern

---

## Performance Issues

### "Server is slow or unresponsive"

**Problem:** High latency or timeouts.

**Solution:**
1. Check system resources (CPU, RAM, disk)
2. Review database query performance
3. Reduce concurrent agents if needed
4. Check OpenAI API rate limits
5. Enable caching if available

### "High memory usage"

**Problem:** Server consuming too much RAM.

**Solution:**
1. Reduce number of active agents
2. Clear old task/memory data
3. Restart server periodically
4. Check for memory leaks in logs
5. Increase system RAM if needed

---

## Configuration Issues

### "Configuration not loading"

**Problem:** Settings from `.env` or config file not applied.

**Solution:**
1. Verify `.env` file is in project root
2. Check environment variable names (case-sensitive)
3. Restart server after changing config
4. Verify config file syntax (no typos)
5. Check for conflicting environment variables

### "Port conflicts"

**Problem:** Multiple services trying to use same port.

**Solution:**
```bash
# Use different ports for server and dashboard
uv run -m agent_mcp.cli --port 8080 --project-dir /path/to/project
# Dashboard uses port 3000 by default (change in dashboard/.env)
```

---

## Getting Help

If you're still experiencing issues:

1. **Check the logs:**
   - Server logs: `logs/mcp-server.log` (if enabled)
   - Browser console for dashboard errors
   - System logs for infrastructure issues

2. **Run verification script:**
   ```bash
   python scripts/verify_setup.py
   ```

3. **Search existing issues:**
   - [GitHub Issues](https://github.com/rinadelph/Agent-MCP/issues)
   - [Discussions](https://github.com/rinadelph/Agent-MCP/discussions)

4. **Ask for help:**
   - [Discord Community](https://discord.gg/7Jm7nrhjGn)
   - Create a new GitHub issue with:
     - Error messages
     - Steps to reproduce
     - System information
     - Relevant logs

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `CRITICAL: OPENAI_API_KEY not found` | Missing API key | Set in `.env` file |
| `Port 8080 already in use` | Port conflict | Use `--port` flag |
| `ModuleNotFoundError` | Package not installed | Run `uv pip install -e .` |
| `Database connection failed` | DB not accessible | Check DB config/permissions |
| `CORS error` | Cross-origin issue | Verify server CORS settings |
| `Agent token invalid` | Wrong token used | Use correct worker/admin token |

---

For more detailed information, see the [Configuration Guide](./CONFIGURATION.md) or [Main Documentation](../).

