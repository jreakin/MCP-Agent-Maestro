# Test Run Guide - Quick Demo of Agent-MCP

## 🚀 **Quick Test Run**

Want to see Agent-MCP in action quickly? Use the test run script!

### **Option 1: Test Run with Sample Data** (Recommended)

```bash
# Start everything and seed with test data
./scripts/test-run.sh --seed
```

This will:
- ✅ Create `.env` file if it doesn't exist (with test defaults)
- ✅ Start all services (backend + dashboard + database)
- ✅ Seed database with sample agents, tasks, and context
- ✅ Open dashboard in your browser

**Result:** You'll see a fully populated dashboard with:
- 3 sample agents (Backend, Frontend, QA)
- 5 sample tasks (various statuses)
- Sample context entries

---

### **Option 2: Test Run Without Sample Data**

```bash
# Start services only (no sample data)
./scripts/test-run.sh
```

This starts everything but leaves the database empty.

---

## 📋 **What You'll See**

After running the test script, you can explore:

### **Dashboard Tabs:**

1. **Overview** (`http://localhost:3000`)
   - System status
   - Agent count
   - Task statistics
   - Recent activity

2. **Agents** (`http://localhost:3000/agents`)
   - List of all agents
   - Agent details and capabilities
   - Agent status and activity

3. **Tasks** (`http://localhost:3000/tasks`)
   - Kanban board view
   - Task details
   - Task assignment
   - Status tracking

4. **Memories** (`http://localhost:3000/memories`)
   - RAG context entries
   - Knowledge graph visualization
   - Search and query interface

5. **System** (`http://localhost:3000/system`)
   - Configuration
   - Health checks
   - System metrics

---

## 🔧 **Manual Test Run**

If you prefer to do it manually:

```bash
# 1. Create .env (if needed)
cat > .env << EOF
PORT=8080
DB_PORT=5433
DB_PASSWORD=test_password_123
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
EOF

# 2. Start services
docker-compose up -d

# 3. Wait for services to be ready
sleep 10

# 4. Seed test data (optional)
docker-compose exec agent-mcp python scripts/seed_test_data.py

# 5. Open dashboard
open http://localhost:3000
```

---

## 🧪 **Test Data Details**

The seed script creates:

### **Agents:**
- `demo-backend-agent` - Backend Developer
- `demo-frontend-agent` - Frontend Developer  
- `demo-qa-agent` - QA Engineer

### **Tasks:**
- "Set up authentication system" (in_progress)
- "Create login UI component" (pending)
- "Write unit tests for auth" (pending)
- "Design database schema" (completed)
- "Add error handling" (pending)

### **Context:**
- Project overview
- Tech stack information
- Architecture notes

---

## 🛑 **Stopping the Test Run**

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## 🔍 **Verifying Test Run**

Check that everything is working:

```bash
# Check services
docker-compose ps

# Check backend
curl http://localhost:8080/api/status

# Check dashboard
curl http://localhost:3000

# View logs
docker-compose logs -f
```

---

## 🐛 **Troubleshooting**

### **Services won't start:**
```bash
# Check Docker is running
docker info

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

### **Dashboard not loading:**
```bash
# Check if dashboard container is running
docker-compose ps dashboard

# Check dashboard logs
docker-compose logs dashboard

# Rebuild dashboard
docker-compose up -d --build dashboard
```

### **No test data:**
```bash
# Manually seed data
docker-compose exec agent-mcp python scripts/seed_test_data.py

# Or run the test script again with --seed
./scripts/test-run.sh --seed
```

---

## 📊 **API Testing**

You can also test the API directly:

```bash
# Get admin token (from seed script output or database)
ADMIN_TOKEN="your-admin-token-here"

# List agents
curl http://localhost:8080/api/agents \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# List tasks
curl http://localhost:8080/api/tasks \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Create a new task
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "title": "Test Task",
    "description": "This is a test",
    "priority": "medium"
  }'
```

---

## 🎯 **Next Steps After Test Run**

1. **Explore the Dashboard** - Navigate through all tabs
2. **Create Your Own Agents** - Go to Agents tab and create new agents
3. **Add Real Tasks** - Create tasks for your actual project
4. **Index Your Project** - Add your project's context to RAG
5. **Connect to Cursor** - Use `mcp-setup install --client cursor`

---

## ✅ **Quick Reference**

| Command | Description |
|---------|-------------|
| `./scripts/test-run.sh --seed` | Start with test data |
| `./scripts/test-run.sh` | Start without test data |
| `docker-compose down` | Stop services |
| `docker-compose logs -f` | View logs |
| `docker-compose restart` | Restart services |

---

**Happy testing!** 🚀
