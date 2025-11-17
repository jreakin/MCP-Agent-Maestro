# Assessment Agent System

## 🎯 **Overview**

The Assessment Agent analyzes user requests and intelligently routes them to the most appropriate agents and models. It can run multiple Ollama models in parallel for optimal performance.

---

## 🏗️ **Architecture**

```
User Request
    ↓
Assessment Agent (analyzes request)
    ↓
Selects:
    ├─ Primary Agent (rag, task, code, chat, orchestrate)
    ├─ Best Model (codellama, llama3.2, etc.)
    ├─ Secondary Agents (if needed)
    └─ Execution Mode (parallel or sequential)
    ↓
Routes to Selected Agents
    ↓
Executes (potentially in parallel)
    ↓
Returns Combined Results
```

---

## 🔍 **How Assessment Works**

### **1. Request Analysis**

The assessment agent analyzes:
- **Request type**: Code, RAG query, task management, general chat
- **Keywords**: Detects code keywords, task keywords, RAG keywords
- **Complexity**: Determines if multiple agents needed
- **Available models**: Checks what Ollama models you have

### **2. Agent Selection**

**Primary Agent Types:**
- `rag` - For questions about project knowledge
- `task` - For task management operations
- `code` - For code generation/analysis
- `chat` - For general conversation
- `orchestrate` - For complex multi-agent workflows

### **3. Model Selection**

**Automatically selects best model:**
- Code requests → Code model (codellama, deepseek-coder)
- General requests → Chat model (llama3.2, mistral)
- RAG queries → Chat model (for synthesis)
- Task operations → Chat model

### **4. Parallel Execution**

If multiple agents needed, can run in parallel:
- RAG agent + Task agent simultaneously
- Code agent + Task agent simultaneously
- All using different Ollama models concurrently

---

## 🚀 **Usage**

### **Via MCP Tool: `assess_request`**

```python
# In Cursor, you can ask:
"Use assess_request to analyze: 'Write a Python function to parse JSON and create a task for it'"

# Returns:
🎯 Request Assessment

Primary Agent: orchestrate
Model: llama3.2
Confidence: 95%

Reasoning:
This request requires both code generation (Python function) and task creation.
The orchestrate agent can coordinate both operations.

Execution Plan:
- Primary: orchestrate using llama3.2
- Secondary: code, task
- Execution: Parallel (multiple agents simultaneously)
```

### **Via MCP Tool: `orchestrate_workflow`**

The orchestrator now uses assessment by default:

```python
# In Cursor:
"Use orchestrate_workflow to: 'Find authentication info and create a task for OAuth2'"

# What happens:
1. Assessment agent analyzes request
2. Determines: RAG query + Task creation needed
3. Selects: RAG agent (llama3.2) + Task agent (llama3.2)
4. Executes in parallel (if use_parallel=true)
5. Combines results
```

---

## 📋 **Example Scenarios**

### **Scenario 1: Code Request**

```
Request: "Write a Python function to parse JSON"

Assessment:
- Primary Agent: code
- Model: codellama (if available)
- Reasoning: Code generation requires code model
- Execution: Single agent

Result: Uses codellama for code generation
```

### **Scenario 2: Complex Request**

```
Request: "Write a Python function to parse JSON and create a task for it"

Assessment:
- Primary Agent: orchestrate
- Model: llama3.2
- Secondary Agents: [code, task]
- Reasoning: Requires both code generation and task creation
- Execution: Parallel

Result: 
- Code agent (codellama) generates function
- Task agent (llama3.2) creates task
- Both run simultaneously
```

### **Scenario 3: RAG Query**

```
Request: "How does authentication work in this project?"

Assessment:
- Primary Agent: rag
- Model: llama3.2
- Reasoning: Question about project knowledge
- Execution: Single agent

Result: Uses RAG agent with llama3.2
```

---

## ⚙️ **Configuration**

### **Enable/Disable Assessment**

```bash
# In orchestrate_workflow tool, you can disable assessment:
{
  "token": "...",
  "query": "...",
  "use_assessment": false  # Falls back to keyword-based detection
}
```

### **Assessment Model**

```bash
# Use specific model for assessment (defaults to fast model)
OLLAMA_ASSESSMENT_MODEL=llama3.2  # Or phi3, mistral-7b for faster assessment
```

---

## 🔄 **Parallel Execution**

### **How It Works**

When `use_parallel=true` and multiple agents needed:

```python
# Multiple agents run simultaneously
import asyncio

# RAG agent using llama3.2
rag_task = rag_agent.search(query, ...)

# Task agent using llama3.2 (or different model)
task_task = task_agent.create_task(...)

# Execute in parallel
results = await asyncio.gather(rag_task, task_task)

# Both complete at same time (or close to it)
```

### **Ollama Handles Multiple Models**

- Each request to Ollama is independent
- Multiple models can be loaded simultaneously
- Requests run in parallel automatically
- No special configuration needed

**Example:**
```
Request 1: Code generation (codellama) → Ollama
Request 2: Task creation (llama3.2) → Ollama
Request 3: RAG query (llama3.2) → Ollama

All run in parallel! ✅
```

---

## 📊 **Benefits**

### **1. Intelligent Routing**
- Automatically picks best agent for each request
- No manual selection needed
- Adapts to request type

### **2. Optimal Model Selection**
- Code requests → Code models
- General requests → Chat models
- Uses what you have available

### **3. Parallel Execution**
- Multiple agents work simultaneously
- Faster completion
- Better resource utilization

### **4. Reasoning**
- Explains why it chose specific agents
- Confidence scores
- Transparent decision-making

---

## 🧪 **Testing**

### **Test Assessment**

```python
from agent_mcp.agents import assess_and_route

plan = await assess_and_route(
    query="Write a Python function to parse JSON",
    agent_id="test-agent"
)

print(plan)
# {
#   "primary_agent": "code",
#   "model": "codellama",
#   "reasoning": "...",
#   "confidence": 0.95
# }
```

### **Test Parallel Execution**

```python
from agent_mcp.agents import AgentOrchestrator, OrchestrationRequest

orchestrator = AgentOrchestrator()
request = OrchestrationRequest(
    query="Find auth info and create a task for OAuth2",
    agent_id="test-agent"
)

result = await orchestrator.orchestrate(request, use_assessment=True)
# Uses assessment, runs agents in parallel if needed
```

---

## 🎓 **Key Concepts**

### **Assessment Agent**
- Analyzes requests
- Selects agents/models
- Provides reasoning
- Enables parallel execution

### **Parallel Execution**
- Multiple agents run simultaneously
- Each can use different Ollama model
- Faster completion
- Better resource use

### **Model Selection**
- Code requests → Code models
- General requests → Chat models
- Automatic fallback if preferred model unavailable

---

## ✅ **Summary**

**Assessment Agent:**
- ✅ Analyzes requests intelligently
- ✅ Routes to best agents/models
- ✅ Supports parallel execution
- ✅ Provides reasoning

**Multiple Ollama Models:**
- ✅ Can run simultaneously
- ✅ Each request independent
- ✅ No special configuration
- ✅ Automatic parallelization

**Result:**
- Smarter routing
- Better performance
- Optimal model usage
- Faster execution

The system now intelligently assesses each request and uses the best agents and models for optimal results! 🚀
