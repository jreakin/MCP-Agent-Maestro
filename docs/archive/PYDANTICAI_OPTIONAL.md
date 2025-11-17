# PydanticAI is Now Optional

## ✅ **Changes Made**

PydanticAI has been moved to **optional dependencies**. The system works perfectly without it, and you can enable it when needed.

---

## 📦 **Installation**

### **Without PydanticAI (Default)**
```bash
# Standard installation - no PydanticAI
uv pip install -e .
# or
uv sync
```

**Result:** All core MCP tools work (RAG, tasks, agents, etc.)

---

### **With PydanticAI (Optional)**
```bash
# Install with PydanticAI support
uv pip install -e ".[pydantic-ai]"
# or
uv sync --extra pydantic-ai
```

**Result:** Additional structured tools available:
- `ask_project_rag_structured` - Type-safe RAG queries
- `create_task_structured` - Type-safe task creation
- `orchestrate_workflow` - Multi-agent orchestration
- `assess_request` - Intelligent request routing

---

## 🔍 **How It Works**

### **Automatic Detection**

The system automatically detects if PydanticAI is installed:

**If installed:**
```
✅ PydanticAI tools registered (pydantic-ai is installed)
```

**If not installed:**
```
ℹ️  PydanticAI tools not available (pydantic-ai not installed)
ℹ️  Install with: uv pip install -e '.[pydantic-ai]' or uv sync --extra pydantic-ai
```

**The system continues to work normally either way!**

---

## 🛠️ **What's Available**

### **Always Available (Core Tools)**

These work **without** PydanticAI:

- ✅ `ask_project_rag` - RAG queries
- ✅ `create_task` / `create_self_task` - Task creation
- ✅ `assign_task` - Task assignment
- ✅ `update_task_status` - Task updates
- ✅ `view_tasks` / `search_tasks` - Task viewing
- ✅ `create_agent` - Agent creation
- ✅ `terminate_agent` - Agent termination
- ✅ `list_agents` - Agent listing

**All core functionality works!**

---

### **Optional (PydanticAI Tools)**

These are **only available** if PydanticAI is installed:

- ⚠️ `ask_project_rag_structured` - Type-safe RAG with confidence scores
- ⚠️ `create_task_structured` - Type-safe task creation with validation
- ⚠️ `orchestrate_workflow` - Multi-agent orchestration
- ⚠️ `assess_request` - Intelligent request routing

**These add structure and type safety, but aren't required.**

---

## 💡 **When to Use PydanticAI**

### **Use PydanticAI if:**
- ✅ You want type-safe responses
- ✅ You need structured orchestration
- ✅ You want built-in retry logic
- ✅ You need complex multi-agent workflows

### **Skip PydanticAI if:**
- ✅ You want simpler architecture
- ✅ You prefer Cursor's AI to orchestrate directly
- ✅ You want fewer dependencies
- ✅ Core tools meet your needs

---

## 🔧 **Checking Installation**

### **Check if PydanticAI is installed:**
```bash
python -c "import pydantic_ai; print('PydanticAI installed')"
```

### **Check available tools:**
```bash
# Start the server and check logs
uv run -m agent_mcp.cli server
# Look for: "PydanticAI tools registered" or "PydanticAI tools not available"
```

---

## 📝 **Migration Notes**

### **If you were using PydanticAI before:**

**Before:**
```bash
uv pip install -e .
# PydanticAI was required
```

**Now:**
```bash
# Option 1: Install without PydanticAI (simpler)
uv pip install -e .

# Option 2: Install with PydanticAI (if you need it)
uv pip install -e ".[pydantic-ai]"
```

### **If you want to remove PydanticAI:**

```bash
# Uninstall pydantic-ai
pip uninstall pydantic-ai

# System continues to work with core tools
```

---

## ✅ **Benefits**

1. **Lighter Installation:** Fewer dependencies by default
2. **Flexibility:** Choose when to use structured agents
3. **Backward Compatible:** Existing code continues to work
4. **Clear Separation:** Core tools vs. optional enhancements

---

## 🎯 **Recommendation**

**Start without PydanticAI:**
- Use core MCP tools
- Let Cursor's AI orchestrate
- Add PydanticAI later if needed

**Install PydanticAI if:**
- You need type-safe responses
- You want structured orchestration
- You're building complex workflows

**The choice is yours!** 🚀
