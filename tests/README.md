# Agent-MCP Test Suite

This directory contains comprehensive Hypothesis-based property tests for all Agent-MCP features.

## Test Coverage

### 1. RAG Personalization Tests (`test_rag_personalization.py`)
- **ResponsePersonalizer**: Tests personalization, filtering, complexity adjustment, and role-based guidance
- **QueryIntentClassifier**: Tests intent classification for context-aware responses
- **Role-Based Filtering**: Tests role-specific result filtering and scoring

### 2. Task Operations Tests (`test_task_operations.py`)
- **TaskCreate Model**: Tests task creation with validation constraints
- **TaskUpdate Model**: Tests partial task updates
- **Task Database Operations**: Tests create, update, delete operations (requires database)

### 3. Task Models Tests (`test_task_models.py`)
- **Task Model**: Tests task validation, constraints (title length, tags, etc.)
- **TaskCreate Model**: Tests creation model validation
- **TaskUpdate Model**: Tests update model with optional fields
- **TaskReorder Model**: Tests reordering with position validation
- **BulkOperation Model**: Tests bulk operations validation

### 4. MCP Setup Tests (`test_mcp_setup.py`)
- **MCPConfigGenerator**: Tests configuration generation for different clients (cursor, claude, windsurf, vscode)
- **MCPConfigInstaller**: Tests configuration installation (requires file system)
- **MCPConfigVerifier**: Tests configuration verification

### 5. TOON Serialization Tests (`test_toon_serialization.py`)
- **ContextSerializer**: Tests context serialization/deserialization in JSON and TOON formats
- **MessageSerializer**: Tests message serialization/deserialization with roundtrip validation

### 6. PydanticAI Agents Tests (`test_pydanticai_agents.py`)
- **RAGAgent**: Tests structured RAG queries with context-aware responses (requires OpenAI API)
- **TaskAgent**: Tests structured task management operations (requires database)
- **AgentOrchestrator**: Tests multi-agent coordination and workflow orchestration

## Running Tests

**⚠️ IMPORTANT: All tests should be run in-container for consistency and to ensure database access.**

### Prerequisites

1. **Start Docker containers:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for containers to be ready** (database must be healthy)

### Run All Tests (Recommended)

```bash
# Using the wrapper script (recommended)
./scripts/run_tests_docker.sh

# Or using uv/rye script
uv run test

# Run with verbose output
./scripts/run_tests_docker.sh -v

# Run with coverage
./scripts/run_tests_docker.sh --cov=agent_mcp --cov-report=html
```

### Run Specific Tests

```bash
# Run specific test file
./scripts/run_tests_docker.sh tests/test_task_models.py

# Run specific test class
./scripts/run_tests_docker.sh tests/test_task_models.py::TestTaskModel

# Run specific test method
./scripts/run_tests_docker.sh tests/test_task_models.py::TestTaskModel::test_task_validates_correctly

# Run with pytest markers
./scripts/run_tests_docker.sh -m "not integration"  # Skip integration tests
./scripts/run_tests_docker.sh -m integration        # Run only integration tests
```

### Direct Container Execution (Alternative)

If you prefer to run pytest directly in the container:

```bash
# Run all tests
docker-compose exec agent-mcp uv run pytest tests/

# Run with verbose output
docker-compose exec agent-mcp uv run pytest tests/ -v

# Run with coverage
docker-compose exec agent-mcp uv run pytest tests/ --cov=agent_mcp --cov-report=html
```

### Local Testing (Not Recommended)

While tests *can* run locally, this is **not recommended** because:
- Database is not available (integration tests will be skipped)
- Environment may differ from production
- Dependencies may not match container

If you must run locally (for quick unit test checks):

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run only unit tests (integration tests will be skipped)
pytest tests/ -m "not integration"
```

### Run Specific Test Files

```bash
# Run RAG personalization tests
pytest tests/test_rag_personalization.py

# Run task operations tests
pytest tests/test_task_operations.py

# Run task models tests
pytest tests/test_task_models.py

# Run MCP setup tests
pytest tests/test_mcp_setup.py

# Run TOON serialization tests
pytest tests/test_toon_serialization.py

# Run PydanticAI agents tests
pytest tests/test_pydanticai_agents.py
```

### Run Specific Test Classes

```bash
# Run specific test class
pytest tests/test_rag_personalization.py::TestResponsePersonalizer

# Run specific test method
pytest tests/test_task_models.py::TestTaskModel::test_task_validates_correctly
```

### Hypothesis Settings

Tests use Hypothesis property-based testing with settings:
- `max_examples`: Limits number of generated test cases (default: 50-100)
- `settings`: Configures test execution (timeout, deadline, etc.)

You can adjust Hypothesis settings by modifying `@settings()` decorators in test files.

### Integration Tests

Some tests are marked with `@pytest.mark.integration` because they require:
- **Database connection**: Task database operations, agent memory (PostgreSQL in Docker)
- **OpenAI API**: PydanticAI agent tests (optional, will skip if API key not available)
- **File system access**: MCP configuration installation/verification

#### Running Integration Tests

**All tests should run in-container.** Integration tests require the database:

```bash
# Run all tests (including integration tests)
./scripts/run_tests_docker.sh

# Run only integration tests
./scripts/run_tests_docker.sh -m integration

# Skip integration tests (unit tests only)
./scripts/run_tests_docker.sh -m "not integration"
```

The tests automatically detect if a database is available via environment variables:
- `DB_HOST` (default: `postgres` in Docker)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `agent_mcp`)
- `DB_USER` (default: `agent_mcp`)
- `DB_PASSWORD` (set in docker-compose.yml)

Integration tests will automatically skip if the database is not available (with a helpful error message directing you to run in-container).

## Property-Based Testing

All tests use **Hypothesis** for property-based testing, which:
- Generates random inputs based on strategies
- Tests edge cases automatically
- Verifies invariants hold for all inputs
- Provides minimal failing examples on errors

### Example Test Pattern

```python
@given(
    title=text(min_size=1, max_size=300),
    priority=st.sampled_from(['low', 'medium', 'high', 'critical'])
)
@settings(max_examples=50)
def test_task_create_validates_correctly(title: str, priority: str):
    """TaskCreate validates correctly for all valid inputs."""
    task = TaskCreate(title=title, priority=priority)
    assert task.title == title.strip()
    assert task.priority == priority
```

## Mutation Testing with Mutmut

Mutation testing validates that your tests actually catch bugs by introducing small mutations (changes) to the code and checking if tests fail. This helps ensure test quality beyond just coverage metrics.

### Running Mutation Tests (In-Container)

All mutation testing runs inside the Docker container for consistency:

```bash
# Ensure container is running
docker-compose up -d

# Run mutation testing using wrapper script (shows progress)
./scripts/run_mutmut_docker.sh

# Or run directly in container (shows progress in real-time)
docker-compose exec agent-mcp mutmut run

# Or using rye script
docker-compose exec agent-mcp uv run mutate
```

**Progress Visibility**: Mutmut shows progress by default, displaying:
- Current mutation being tested (e.g., `1/50`)
- Status of each mutation (killed, survived, timeout, suspicious)
- Running totals and percentages

The wrapper scripts remove output buffering so you can see progress in real-time. If running directly, make sure not to use the `-T` flag with `docker-compose exec` to see live progress.

### Viewing Mutation Results

```bash
# View results summary
docker-compose exec agent-mcp mutmut results

# View HTML report (if generated)
docker-compose exec agent-mcp mutmut html
```

### Applying Specific Mutations

To see what a specific mutation does:

```bash
# Apply a specific mutation (replace <id> with mutation ID from results)
docker-compose exec agent-mcp uv run mutate-apply <id>

# Or directly
docker-compose exec agent-mcp mutmut apply <id>
```

### CI/CD Integration

For CI/CD pipelines, use the CI wrapper script that fails on low mutation scores:

```bash
# Set mutation score threshold (default: 70%)
export MUTATION_SCORE_THRESHOLD=70

# Run CI mutation testing
./scripts/run_mutmut_ci_docker.sh
```

### Interpreting Results

- **Killed mutations**: Tests caught the mutation (good!)
- **Survived mutations**: Tests didn't catch the mutation (needs better tests)
- **Timeout**: Mutation caused test to hang (may indicate infinite loop risk)
- **Suspicious**: Mutation may have equivalent behavior (false positive)

Aim for a mutation score (percentage of killed mutations) of 70% or higher.

### Configuration

Mutation testing is configured in `mutmut_config.py`:
- Paths to mutate: `agent_mcp/` package
- Excluded paths: Dashboard, migrations, tests, scripts
- Test command: Uses `uv run pytest` for in-container execution

## Continuous Integration

Tests should be run in CI/CD pipelines:
- On pull requests
- Before releases
- As part of quality gates

Add to your CI workflow:
```yaml
- name: Run Hypothesis tests
  run: pytest tests/ -v

- name: Run mutation testing (scheduled)
  run: ./scripts/run_mutmut_ci_docker.sh
  # Note: Mutation testing is slow, consider running on schedule rather than every PR
```

## Fuzzing with Atheris

Coverage-guided fuzzing using Atheris to find edge cases and potential security vulnerabilities in security-critical code.

### Running Fuzzers (In-Container)

All fuzzing runs inside the Docker container for consistency:

```bash
# Ensure container is running
docker-compose up -d

# Run all fuzzing targets
./scripts/run_fuzz_docker.sh

# Run a specific fuzzer
./scripts/run_fuzz_single_docker.sh tests/fuzz/test_json_sanitizer_fuzz.py

# Or run directly in container
docker-compose exec agent-mcp python tests/fuzz/test_json_sanitizer_fuzz.py
```

### Available Fuzzing Targets

- **`test_json_sanitizer_fuzz.py`**: Fuzzes `sanitize_json_input()` to find edge cases in JSON parsing and sanitization
- **`test_response_sanitizer_fuzz.py`**: Fuzzes `ResponseSanitizer.sanitize()` to test threat removal/neutralization
- **`test_task_models_fuzz.py`**: Fuzzes Task model validation (Task, TaskCreate, TaskUpdate)
- **`test_toon_serialization_fuzz.py`**: Fuzzes TOON serialization/deserialization

### Fuzzing Configuration

- **Timeout**: Default 60s per fuzzer (configurable via `FUZZ_TIMEOUT` environment variable)
- **Corpus**: Fuzzing corpus is stored in `.corpus/` directory (mounted as volume)
- **Crashes**: If Atheris finds a crash, it will save the input that caused it

### Interpreting Results

- **Normal completion**: Fuzzer ran without finding crashes (good!)
- **Timeout**: Fuzzer ran for the full timeout period (normal for fuzzing)
- **Crash**: Atheris found an input that causes a crash or assertion failure (investigate!)

### Corpus Management

The fuzzing corpus (seed inputs) is stored in `.corpus/` and persists across runs. Atheris will evolve the corpus to find new code paths.

To reset the corpus:
```bash
rm -rf .corpus/*
```

### Platform Requirements

Fuzzing runs in the Docker container (Linux-based), so platform concerns are eliminated. The container includes clang/llvm required for Atheris/libFuzzer. 

**Python Version**: The project requires Python 3.10+ due to dependencies (mcp, pydantic>=2.0), and all testing tools (mutmut, atheris, pytest) fully support Python 3.10+.

## Contributing

When adding new features:
1. Write Hypothesis tests for validation logic
2. Test edge cases and boundary conditions
3. Use property-based testing for models and serialization
4. Mark integration tests with `@pytest.mark.skip` if they require external services
5. Run mutation testing to ensure your tests actually catch bugs
6. Add fuzzing targets for security-critical input handling code

