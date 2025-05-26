# Tech Context

This document outlines the technologies, development environment, constraints, dependencies, and tool usage patterns for the LL-AI Legion to Atomic Agents migration project.

## 1. Core Technologies

**Programming Language:**
- **Python 3.10+** - Primary development language with modern async/await support

**AI/ML Frameworks:**
- **Atomic Agents** - Target framework for AI agent development with provider abstraction
- **Legion** - Legacy custom framework (being phased out)
- **Pydantic v2** - Data validation and serialization (via BaseIOSchema)
- **Instructor** - LLM response parsing and validation

**Web Framework:**
- **Streamlit** - Web UI framework for the application interface

**Data Validation & Modeling:**
- **BaseIOSchema** - Atomic Agents' enhanced Pydantic models with documentation requirements
- **Pydantic v2** - Underlying validation engine

**LLM Providers (Multi-provider support):**
- **OpenAI** - GPT models (primary)
- **Anthropic** - Claude models (secondary)
- **Azure OpenAI** - Enterprise deployment option

**Development & Testing:**
- **Pytest** - Testing framework with async support
- **Rich** - Enhanced console output and logging
- **Python-dotenv** - Environment variable management

**Utilities & Infrastructure:**
- **Asyncio** - Asynchronous programming support
- **Logging** - Python standard logging with Rich integration
- **JSON** - Data serialization and API communication

## 2. Development Environment Setup

### 2.1. Prerequisites
- **Python 3.10+** (recommended: Python 3.11)
- **Conda** or **Miniconda** for environment management
- **Git** for version control
- **VS Code** (recommended) with Python extension

### 2.2. Environment Setup Steps

1. **Create Conda Environment:**
   ```bash
   conda create -n llai-atomic python=3.11
   conda activate llai-atomic
   ```

2. **Install Core Dependencies:**
   ```bash
   pip install atomic-agents
   pip install streamlit
   pip install rich
   pip install python-dotenv
   pip install pytest
   pip install pytest-asyncio
   ```

3. **Install Development Dependencies:**
   ```bash
   pip install black  # Code formatting
   pip install flake8  # Linting
   pip install mypy  # Type checking
   ```

4. **Environment Verification:**
   ```bash
   python examples/atomic_agents_hello_world.py
   python examples/legion_hello_world.py
   ```

### 2.3. Key Commands

**Development:**
- `streamlit run llai/streamlit_app.py` - Run the main application
- `python -m pytest llai/tests/` - Run all tests
- `python -m pytest llai/tests/test_atomic_models.py` - Run specific test module
- `python -m pytest llai/tests/test_week3_utilities.py` - Run Week 3 utility tests

**Code Quality:**
- `black llai/` - Format code
- `flake8 llai/` - Lint code
- `mypy llai/` - Type checking

**Examples & Validation:**
- `python examples/atomic_agents_hello_world.py` - Test Atomic Agents setup
- `python examples/legion_hello_world.py` - Test Legacy Legion setup

## 3. Technical Constraints

### 3.1. Performance Requirements
- **Response Time:** Target 50% improvement in average response times
- **Memory Usage:** ≤20% reduction in memory footprint
- **Concurrent Users:** Support for multiple simultaneous Streamlit sessions

### 3.2. Compatibility Requirements
- **Python Version:** Minimum Python 3.10 for modern async features
- **Framework Migration:** Maintain functional parity during Legion → Atomic Agents transition
- **Data Integrity:** Zero data loss during migration process

### 3.3. Security Constraints
- **API Keys:** Secure storage and rotation of LLM provider API keys
- **Data Privacy:** No sensitive data in logs or error messages
- **Input Validation:** All user inputs validated through BaseIOSchema

### 3.4. Operational Constraints
- **Deployment:** Gradual rollout using Strangler Fig pattern
- **Monitoring:** Comprehensive logging and error tracking
- **Rollback:** Ability to revert to Legion implementation at any stage

## 4. Key Dependencies & Services

### 4.1. Core Dependencies
- **atomic-agents** (latest) - Primary AI agent framework
- **pydantic** (v2.x) - Data validation and serialization
- **streamlit** (latest) - Web application framework
- **rich** (latest) - Enhanced console output and logging
- **python-dotenv** (latest) - Environment variable management

### 4.2. Development Dependencies
- **pytest** (latest) - Testing framework
- **pytest-asyncio** (latest) - Async testing support
- **black** (latest) - Code formatting
- **flake8** (latest) - Code linting
- **mypy** (latest) - Static type checking

### 4.3. External Services
- **OpenAI API** - Primary LLM provider
- **Anthropic API** - Secondary LLM provider
- **Azure OpenAI** - Enterprise LLM option

## 5. Tool Usage Patterns

### 5.1. Version Control
- **Git** with feature branch workflow
- **Conventional Commits** for clear commit messages
- **Pull Request** reviews for all changes

### 5.2. Code Quality & Formatting
- **Black** - Automatic code formatting with 88-character line length
- **Flake8** - Linting with E203, W503 exceptions for Black compatibility
- **MyPy** - Static type checking with strict mode for new code
- **Pre-commit hooks** (planned) - Automated quality checks

### 5.3. Testing Strategy
- **Pytest** - Unit and integration testing
- **Atomic Agents Mock Providers** - LLM testing without API calls
- **BaseIOSchema Validation** - Data model testing
- **Coverage Target** - ≥85% unit coverage, ≥70% integration coverage

### 5.4. Documentation
- **Docstrings** - Required for all BaseIOSchema models and public functions
- **Type Hints** - Comprehensive type annotations
- **Memory Bank** - Architectural and project documentation
- **README** files for major modules

## 6. Environment Variables

### 6.1. LLM Provider Configuration
```bash
# OpenAI Configuration
OPENAI_API_KEY="sk-..."                    # OpenAI API key
OPENAI_MODEL="gpt-4"                       # Default OpenAI model
OPENAI_MAX_TOKENS=4000                     # Token limit per request
OPENAI_TEMPERATURE=0.7                     # Response creativity

# Anthropic Configuration  
ANTHROPIC_API_KEY="sk-ant-..."             # Anthropic API key
ANTHROPIC_MODEL="claude-3-sonnet-20240229" # Default Anthropic model
ANTHROPIC_MAX_TOKENS=4000                  # Token limit per request

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY="..."                # Azure OpenAI key
AZURE_OPENAI_ENDPOINT="https://..."       # Azure endpoint URL
AZURE_OPENAI_API_VERSION="2024-02-15-preview" # API version
```

### 6.2. Application Configuration
```bash
# Application Settings
APP_NAME="LL-AI Marketing Assistant"      # Application display name
APP_VERSION="2.0.0"                       # Current version
DEBUG_MODE=false                           # Enable debug features
ENVIRONMENT="development"                  # Environment (dev/staging/prod)

# Database Configuration (if applicable)
DATABASE_URL="sqlite:///llai.db"          # Database connection string
DATABASE_POOL_SIZE=5                      # Connection pool size

# Logging Configuration
LOG_LEVEL="INFO"                          # Logging level (DEBUG/INFO/WARNING/ERROR)
LOG_FILE_PATH="logs/llai.log"            # Log file location
LOG_MAX_FILE_SIZE=10485760                # Max log file size (10MB)
LOG_BACKUP_COUNT=5                        # Number of backup log files
ENABLE_RICH_LOGGING=true                  # Enable Rich console logging
```

### 6.3. Development & Testing
```bash
# Development Settings
PYTEST_TIMEOUT=30                         # Test timeout in seconds
MOCK_LLM_RESPONSES=true                   # Use mock responses in tests
TEST_DATA_PATH="tests/data"               # Test data directory

# Performance Monitoring
ENABLE_PERFORMANCE_LOGGING=true          # Log performance metrics
PERFORMANCE_LOG_THRESHOLD=1.0            # Log operations slower than 1s
```

### 6.4. Security & Compliance
```bash
# Security Settings
SECURE_HEADERS=true                       # Enable security headers
RATE_LIMIT_ENABLED=true                   # Enable API rate limiting
MAX_REQUESTS_PER_MINUTE=60               # Rate limit threshold

# Data Privacy
ANONYMIZE_LOGS=true                       # Remove PII from logs
AUDIT_LOGGING=true                        # Enable audit trail
```

## 7. Migration-Specific Technical Context

### 7.1. Bridge Architecture
- **Model Adapters** - Convert between Legion and Atomic Agents data formats
- **Configuration Bridge** - Map legacy config to centralized system
- **Error Translation** - Convert legacy errors to structured format

### 7.2. Testing Strategy During Migration
- **Parallel Testing** - Both Legion and Atomic Agents implementations
- **Compatibility Tests** - Ensure bridge adapters work correctly
- **Performance Benchmarks** - Compare old vs new implementations

### 7.3. Deployment Strategy
- **Feature Flags** - Toggle between Legion and Atomic Agents implementations
- **Gradual Rollout** - Phase-by-phase migration with rollback capability
- **Monitoring** - Enhanced logging during migration period

---

**Technical Evolution Timeline:**
- **Phase 1 (Current):** Foundation setup with bridge adapters and utilities
- **Phase 2:** Agent migration with parallel implementations
- **Phase 3:** Tool standardization and optimization
- **Phase 4:** UI modernization and user experience improvements
- **Phase 5:** Performance optimization and legacy code removal
