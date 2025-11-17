# Testing Guide: How to Run Agent-MCP and See the UI

## 🎯 **Quick Start**

### **Option 1: Docker Compose (Recommended - Easiest)**

This runs both the backend server and PostgreSQL database:

```bash
# 1. Create .env file with your API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
# Or if using Ollama:
# echo "EMBEDDING_PROVIDER=ollama" > .env

# 2. Start services
docker-compose up -d

# 3. Check logs
docker-compose logs -f agent-mcp

# 4. Access the API
curl http://localhost:8080/api/status
```

**Backend is now running on:** `http://localhost:8080`

---

### **Option 2: Run Backend Locally (Python)**

```bash
# 1. Install dependencies
uv pip install -e .

# 2. Set up environment variables
export OPENAI_API_KEY=sk-your-key-here
# Or for Ollama:
# export EMBEDDING_PROVIDER=ollama

# 3. Make sure PostgreSQL is running (or use Docker for just the DB)
docker-compose up -d postgres

# 4. Run the server
uv run -m agent_mcp.cli server --project-dir ./project-data
```

**Backend is now running on:** `http://localhost:8080`

---

## 🎨 **Running the Dashboard UI**

The dashboard is a Next.js application that connects to the backend API.

### **Step 1: Navigate to Dashboard Directory**

```bash
cd agent_mcp/dashboard
```

### **Step 2: Install Dependencies**

```bash
npm install
```

### **Step 3: Start Development Server**

```bash
npm run dev
```

**Dashboard is now running on:** `http://localhost:3000`

---

## 🔗 **Complete Setup (Backend + UI)**

### **Terminal 1: Start Backend**

```bash
# Option A: Docker (recommended)
docker-compose up

# Option B: Local Python
uv run -m agent_mcp.cli server --project-dir ./project-data
```

### **Terminal 2: Start Dashboard**

```bash
cd agent_mcp/dashboard
npm install  # First time only
npm run dev
```

### **Access the UI**

Open your browser to: **http://localhost:3000**

---

## 📋 **What You'll See**

### **Dashboard Features:**

1. **Overview Dashboard** - System status, agent count, task statistics
2. **Agents Dashboard** - View and manage all agents
3. **Tasks Dashboard** - Kanban board for task management
4. **Memories Dashboard** - RAG context and knowledge graph
5. **Security Dashboard** - Security monitoring and logs
6. **System Dashboard** - System configuration and health

### **Initial Setup:**

When you first open the dashboard:
- It will prompt you to connect to a server
- Enter: `http://localhost:8080` (or your backend URL)
- The dashboard will auto-detect and connect

---

## 🧪 **Testing the API Directly**

### **Health Check**

```bash
curl http://localhost:8080/api/status
```

### **List Agents**

```bash
curl http://localhost:8080/api/agents
```

### **List Tasks**

```bash
curl http://localhost:8080/api/tasks
```

### **RAG Query**

```bash
curl -X POST http://localhost:8080/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this project about?"}'
```

---

## 🔧 **Configuration**

### **Environment Variables**

Create a `.env` file in the project root:

```bash
# Required for OpenAI
OPENAI_API_KEY=sk-your-key-here

# Optional: Use Ollama instead
# EMBEDDING_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434

# Database (if not using Docker)
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=agent_mcp
# DB_USER=agent_mcp
# DB_PASSWORD=your-password

# Server port
# PORT=8080
```

### **Dashboard Configuration**

The dashboard automatically connects to `http://localhost:8080` by default.

To change the backend URL:
1. Open the dashboard
2. Click "Server Settings" or "Connect to Server"
3. Enter your backend URL

---

## 🐛 **Troubleshooting**

### **Backend Not Starting**

**Check logs:**
```bash
# Docker
docker-compose logs agent-mcp

# Local
# Check terminal output
```

**Common issues:**
- Missing `OPENAI_API_KEY` - Set it in `.env` or environment
- PostgreSQL not running - Start with `docker-compose up -d postgres`
- Port 8080 in use - Change `PORT` in `.env`

### **Dashboard Not Connecting**

**Check:**
1. Backend is running on `http://localhost:8080`
2. CORS is enabled (should be by default)
3. Browser console for errors

**Test connection:**
```bash
curl http://localhost:8080/api/status
```

### **Database Connection Issues**

**If using Docker:**
```bash
# Check PostgreSQL is healthy
docker-compose ps

# Check logs
docker-compose logs postgres
```

**If using local PostgreSQL:**
- Ensure PostgreSQL is running
- Check connection settings in `.env`
- Verify database exists: `createdb agent_mcp`

---

## 📊 **Testing Workflow**

### **1. Start Everything**

```bash
# Terminal 1: Backend
docker-compose up

# Terminal 2: Dashboard
cd agent_mcp/dashboard && npm run dev
```

### **2. Open Dashboard**

Navigate to: `http://localhost:3000`

### **3. Create Your First Agent**

1. Go to "Agents" tab
2. Click "Create Agent"
3. Fill in details
4. Click "Create"

### **4. Create a Task**

1. Go to "Tasks" tab
2. Click "Create Task"
3. Fill in task details
4. Assign to an agent

### **5. Test RAG**

1. Go to "Memories" tab
2. Enter a query
3. See results from your indexed context

---

## 🎯 **Quick Test Commands**

### **Full Stack Test**

```bash
# 1. Start backend
docker-compose up -d

# 2. Wait for it to be ready
sleep 5

# 3. Check health
curl http://localhost:8080/api/status

# 4. Start dashboard
cd agent_mcp/dashboard && npm run dev
```

### **API Test**

```bash
# Health check
curl http://localhost:8080/api/status

# List agents
curl http://localhost:8080/api/agents

# Create a test agent (requires auth token)
# Get token from logs or create via CLI
```

---

## 📝 **Next Steps**

1. **Explore the Dashboard** - Navigate through all tabs
2. **Create Agents** - Set up your first agent
3. **Create Tasks** - Add tasks and assign them
4. **Index Content** - Add project context to RAG
5. **Test Tools** - Try the MCP tools via Cursor or Claude

---

## 🔗 **Useful Links**

- **API Docs:** `http://localhost:8080/docs` (Swagger UI)
- **Health Check:** `http://localhost:8080/api/status`
- **Metrics:** `http://localhost:8080/api/metrics`

---

## ✅ **Success Indicators**

You'll know everything is working when:

1. ✅ Backend logs show: "Application startup complete"
2. ✅ `curl http://localhost:8080/api/status` returns JSON
3. ✅ Dashboard loads at `http://localhost:3000`
4. ✅ Dashboard shows "Connected" status
5. ✅ You can see agents/tasks in the UI

**Happy testing!** 🚀
