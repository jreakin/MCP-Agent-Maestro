# Plan Execution Workflow: How Cursor Builds Plans

## 🎯 **Your Question**

> "If I create a plan in Cursor, and then tell Cursor to build that plan, will it assign new agents in parallel by default, and if it does, what agents get used?"

---

## 📋 **Current Behavior: NOT Automatic**

### **Short Answer:**

**No, Agent-MCP does NOT automatically create agents in parallel when you build a plan.**

**Current workflow:**
1. You create tasks (plan)
2. You manually assign agents to tasks
3. Agents work on tasks (one at a time, or you manually create multiple)

**It's NOT automatic** - Cursor's AI would need to explicitly:
- Create multiple agents
- Assign tasks to them
- Coordinate them

---

## 🔍 **How It Actually Works**

### **Step 1: Create Plan (Tasks)**

**You in Cursor:**
> "Create a plan to build a user authentication system"

**Cursor's AI might:**
```python
# Creates multiple tasks
create_task(title="Design database schema", ...)
create_task(title="Build login API endpoint", ...)
create_task(title="Create login UI component", ...)
create_task(title="Add password hashing", ...)
```

**Result:** Multiple tasks created, but **NO agents assigned yet**

---

### **Step 2: Build Plan (Assign Agents)**

**You in Cursor:**
> "Build this plan" or "Assign agents to these tasks"

**What Cursor's AI would need to do:**

#### **Option A: Manual Assignment (Current)**
```python
# Create one agent
create_agent(agent_id="backend-worker", task_ids=["task_1", "task_2"])

# Create another agent
create_agent(agent_id="frontend-worker", task_ids=["task_3"])

# Assign remaining tasks
assign_task(task_id="task_4", agent_id="backend-worker")
```

**Result:** Agents created and tasks assigned, but **sequentially, not automatically parallel**

---

#### **Option B: Cursor's AI Could Do This (But Doesn't Automatically)**

Cursor's AI **could** automatically:
1. Analyze the plan
2. Group tasks by type (backend, frontend, etc.)
3. Create multiple agents in parallel
4. Assign tasks to appropriate agents

**But it doesn't do this automatically** - it depends on:
- How you phrase your request
- Cursor's AI's decision-making
- Whether it understands the plan structure

---

## 🚫 **What's NOT Automatic**

### **1. Automatic Agent Creation**
- ❌ Doesn't automatically create agents when you create tasks
- ❌ Doesn't automatically create multiple agents for parallel work
- ❌ Doesn't automatically assign tasks to agents

### **2. Automatic Parallel Assignment**
- ❌ Doesn't automatically create agents in parallel
- ❌ Doesn't automatically distribute tasks across agents
- ❌ Doesn't automatically coordinate multiple agents

### **3. Automatic Agent Selection**
- ❌ Doesn't automatically pick agent types (backend, frontend, etc.)
- ❌ Doesn't automatically match tasks to agent capabilities
- ❌ Doesn't automatically create specialized agents

---

## ✅ **What IS Available**

### **1. Manual Agent Creation**
```python
# You can create agents with multiple tasks
create_agent(
    agent_id="backend-worker",
    task_ids=["task_1", "task_2", "task_3"]  # Multiple tasks
)
```

### **2. Bulk Task Assignment**
```python
# You can assign multiple tasks at once
assign_task(
    task_ids=["task_1", "task_2", "task_3"],  # Multiple tasks
    agent_id="backend-worker"
)
```

### **3. Multiple Agents Can Work Simultaneously**
- ✅ Once created, agents can work in parallel
- ✅ Each agent has their own tmux session
- ✅ They can work on different tasks simultaneously

---

## 🎯 **How to Get Parallel Execution**

### **Option 1: Explicitly Ask Cursor**

**You:**
> "Create a backend agent for the API tasks and a frontend agent for the UI tasks, then assign the appropriate tasks to each"

**Cursor's AI would:**
```python
# 1. Create backend agent
create_agent(
    agent_id="backend-worker",
    capabilities=["backend", "api"],
    task_ids=["task_1", "task_2"]  # API tasks
)

# 2. Create frontend agent
create_agent(
    agent_id="frontend-worker",
    capabilities=["frontend", "ui"],
    task_ids=["task_3"]  # UI tasks
)

# 3. Both agents now work in parallel!
```

---

### **Option 2: Use Assessment Agent (New Feature)**

**You:**
> "Use orchestrate_workflow to build this plan: [list of tasks]"

**What happens:**
1. Assessment agent analyzes the plan
2. Determines which agents needed
3. Creates agents with appropriate capabilities
4. Assigns tasks to agents
5. Agents work in parallel

**But this requires:**
- Using the `orchestrate_workflow` tool
- The assessment agent understanding the plan
- Explicit request to build the plan

---

## 📊 **Current Workflow Example**

### **Scenario: Building a Plan**

**Step 1: Create Plan**
```
You: "Create a plan to build authentication"

Cursor creates tasks:
- task_1: "Design database schema"
- task_2: "Build login API"
- task_3: "Create login UI"
- task_4: "Add password hashing"
```

**Step 2: Build Plan (Current - Manual)**
```
You: "Build this plan"

Cursor's AI might:
1. Create one agent: create_agent(agent_id="worker-1", task_ids=["task_1"])
2. Assign remaining tasks: assign_task(task_id="task_2", agent_id="worker-1")
3. Assign more: assign_task(task_id="task_3", agent_id="worker-1")
4. Assign more: assign_task(task_id="task_4", agent_id="worker-1")

Result: ONE agent working on ALL tasks sequentially ❌
```

**Step 2: Build Plan (Better - Explicit)**
```
You: "Create a backend agent for tasks 1, 2, 4 and a frontend agent for task 3"

Cursor's AI:
1. create_agent(agent_id="backend", task_ids=["task_1", "task_2", "task_4"])
2. create_agent(agent_id="frontend", task_ids=["task_3"])

Result: TWO agents working in parallel ✅
```

---

## 🔄 **What Agents Get Used?**

### **When You Create Agents:**

**Default behavior:**
- Uses `prompt_template="worker_with_rag"` (standard worker)
- No automatic specialization
- Agents are generic workers

**You can specify:**
```python
create_agent(
    agent_id="backend-worker",
    capabilities=["backend", "api"],  # Just metadata
    prompt_template="worker_with_rag"  # Standard template
)
```

**Available templates:**
- `worker_with_rag` - Standard worker (default)
- `basic_worker` - Basic worker
- `frontend_worker` - Frontend-focused (with Playwright)
- `admin_agent` - Admin/coordination
- `testing_agent` - Testing/validation
- `custom` - Your custom prompt

---

## 💡 **The Gap: No Automatic Plan Execution**

### **What's Missing:**

**Automatic plan execution would:**
1. Analyze the plan (task types, dependencies)
2. Group tasks by type/capability
3. Create specialized agents automatically
4. Assign tasks to appropriate agents
5. Start agents in parallel

**Current system:**
- ✅ Can create multiple agents
- ✅ Can assign multiple tasks
- ✅ Agents can work in parallel
- ❌ **NOT automatic** - requires explicit instructions

---

## 🚀 **How to Get Parallel Execution**

### **Method 1: Explicit Instructions**

**You:**
> "Create a backend agent and assign it tasks 1, 2, and 4. Create a frontend agent and assign it task 3. Have them work in parallel."

**Result:** Multiple agents, parallel execution ✅

---

### **Method 2: Use Orchestration Tool**

**You:**
> "Use orchestrate_workflow to: Create backend agent for API tasks and frontend agent for UI tasks, then assign tasks appropriately"

**Result:** Assessment agent helps route, but still requires explicit agent creation ✅

---

### **Method 3: Manual Step-by-Step**

**You:**
1. "Create a backend agent with tasks 1, 2, 4"
2. "Create a frontend agent with task 3"
3. "Start both agents"

**Result:** Parallel execution ✅

---

## 📋 **Summary**

### **Current State:**

| Feature | Status |
|---------|--------|
| **Automatic agent creation** | ❌ No |
| **Automatic parallel assignment** | ❌ No |
| **Automatic agent specialization** | ❌ No |
| **Manual agent creation** | ✅ Yes |
| **Multiple agents in parallel** | ✅ Yes (once created) |
| **Bulk task assignment** | ✅ Yes |

### **To Get Parallel Execution:**

**You need to explicitly:**
1. Create multiple agents
2. Assign tasks to them
3. Start them

**Cursor's AI won't do this automatically** - you need to ask for it explicitly.

---

## 🎯 **Recommended Workflow**

### **For Parallel Execution:**

**Step 1: Create Plan**
```
"Create a plan to build authentication with these tasks: [list]"
```

**Step 2: Build Plan (Explicit)**
```
"Create a backend agent for the API tasks (tasks 1, 2, 4) and a frontend agent for the UI tasks (task 3). Assign the tasks and have them work in parallel."
```

**Or:**
```
"Create specialized agents for this plan:
- Backend agent: tasks 1, 2, 4
- Frontend agent: task 3
- Testing agent: all tasks (for validation)"
```

**Result:** Multiple agents, parallel execution ✅

---

## 🔮 **Future Enhancement Possibility**

**Could add automatic plan execution:**
- Analyze plan structure
- Group tasks by type
- Create specialized agents automatically
- Assign tasks intelligently
- Start parallel execution

**But this doesn't exist yet** - requires explicit instructions.

---

## ✅ **Bottom Line**

**Current answer:**
- ❌ **NOT automatic** - Cursor won't automatically create agents in parallel
- ✅ **Possible** - You can explicitly request it
- ✅ **Works** - Once created, agents work in parallel
- ❌ **No auto-specialization** - Agents are generic unless you specify

**To get parallel execution, you need to explicitly ask Cursor to:**
1. Create multiple agents
2. Assign tasks to them
3. Start them

**The system supports it, but doesn't do it automatically!**
