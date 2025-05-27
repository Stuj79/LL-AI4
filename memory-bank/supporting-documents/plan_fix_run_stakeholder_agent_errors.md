# Plan: Resolving Import Errors for `run_stakeholder_agent.py`

**Date:** 2025-05-27

**Goal:**
Enable successful execution of the `examples/run_stakeholder_agent.py` script by resolving outstanding Python import errors. This script is intended to demonstrate the functionality of the refactored `StakeholderIdentificationAgent`.

**Context & Current Issues:**
The execution of `run_stakeholder_agent.py` is currently blocked by two main types of import errors:
1.  A missing custom exception class (`LegalMarketingAgentError`).
2.  Lingering dependencies on the old `legion` framework in modules that are indirectly imported.

**Developer Implementation Steps:**

**Step 1: Define and Add the Missing `LegalMarketingAgentError`**

*   **Problem:** The script fails with `ImportError: cannot import name 'LegalMarketingAgentError' from 'llai.utils.exceptions_atomic'`. This occurs because `llai/agents/legal_marketing_base_agent.py` tries to import this custom exception, but it's not defined in `llai/utils/exceptions_atomic.py`.
*   **Action:** Add the necessary class definitions to `llai/utils/exceptions_atomic.py`.

    1.  **Open the file:** `llai/utils/exceptions_atomic.py`
    2.  **Add the schema definition:** Locate the section `# --- Specific Exception Schemas ---` and add the following Python code block:
        ```python
        class LegalMarketingAgentErrorSchema(AppBaseException):
            """Schema for legal marketing specific errors."""
            error_type: str = Field("LegalMarketingAgentError", description="Type of error")
            # Add any specific fields relevant to legal marketing errors if needed later
            # For example:
            # compliance_area: Optional[str] = Field(None, description="Specific compliance area related to the error")
        ```
    3.  **Add the exception class definition:** Locate the section `# --- Exception Classes ---` and add the following Python code block:
        ```python
        class LegalMarketingAgentError(AtomicException):
            """Exception for legal marketing specific errors."""
            pass
        ```
    4.  **Save the file.** This change should resolve the `ImportError` for `LegalMarketingAgentError`.

**Step 2: Address Lingering `legion` Framework Dependencies**

*   **Problem:** After resolving the first error, the script might fail with `ModuleNotFoundError: No module named 'legion'`. This is because `llai/agents/__init__.py` can import other agent modules (like `llai.agents.content.py`) which still contain `from legion import ...` statements. The `legion` library is not part of the new `llai-atomic` environment.
*   **Action:** Temporarily modify imports to prevent loading unmigrated, `legion`-dependent code when running the `StakeholderIdentificationAgent` example.

    1.  **Investigate `llai/agents/__init__.py`:**
        *   Open this file.
        *   Identify any lines that import agents or modules that are *not yet refactored* and might still depend on `legion`. The traceback specifically mentioned an issue originating from an import of `llai.agents.content`.
        *   **Temporarily comment out** these problematic imports. For example:
            ```python
            # from .content import ContentInventoryAgent, ContentCategorizationAgent, ContentQualityAssessmentAgent # TODO: Refactor from Legion
            # from .discovery import SomeOtherDiscoveryAgent # TODO: Refactor from Legion
            ```
        *   **Important:** Be careful to only comment out what's necessary to stop the `legion` import error for *this specific example script*. Do not comment out imports essential for `StakeholderIdentificationAgent` or `LegalMarketingBaseAgent` themselves.

    2.  **Inspect and Modify `llai/agents/content.py` (and similar files if needed):**
        *   Open `llai/agents/content.py`.
        *   Find the line `from legion import agent, tool`.
        *   Comment out or delete this line:
            ```python
            # from legion import agent, tool # TODO: Remove Legion dependency, refactor agent
            ```
        *   If, after these changes, running the example script reveals other `ModuleNotFoundError: No module named 'legion'` errors pointing to different files, apply a similar approach: locate the `legion` import in the offending file and comment it out, or comment out its import from `llai/agents/__init__.py` if the entire module is unmigrated.

    3.  **Save all modified files.**

**Step 3: Test the Example Script**

1.  **Activate the Conda environment:**
    ```bash
    conda activate llai-atomic
    ```
2.  **Navigate to the project root directory** in your terminal:
    ```bash
    cd "g:/Other computers/My computer (2)/Clients/LL-AI4"
    ```
3.  **Run the script:**
    ```bash
    python examples/run_stakeholder_agent.py
    ```
4.  The script should now ideally run without the previously encountered import errors. If new, different import errors arise, they will need to be diagnosed based on their specific messages.

**Important Long-Term Note for the Developer:**
The modifications in Step 2 (commenting out imports) are **temporary workarounds** to allow the `run_stakeholder_agent.py` example to function. The correct long-term solution is the full refactoring of all agents (e.g., `ContentInventoryAgent`, `PlatformInventoryAgent`, etc.) to remove all dependencies on the `legion` framework and align them with the Atomic Agents patterns. These refactoring tasks should be tracked as part of the overall project plan.
