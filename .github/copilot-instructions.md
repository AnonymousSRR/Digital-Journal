# Agent Mode Prompt Library

This file contains detailed, reusable prompts for the Agent Mode (Coding Agent). Use them as step-by-step instructions to guide precise, testable, and complete implementations.

## Implementation Prompts

### Starting Implementation
- "Begin Phase 1 of the implementation plan. For each task, reference the corresponding file and function, and include only the changes specific to this phase."
- "Once Phase 1 is complete and verified, proceed to Phase 2. Summarize the changes made and highlight any key integration points."
- "If implementation was paused, summarize completed tasks and explicitly list remaining subtasks for this phase before resuming."

### Testing Prompts
- "For every new function or class, write separate unit tests covering expected, edge, and error scenarios. Place tests in the designated test file for this phase."
- "Run the full suite of unit and integration tests after each phase. Identify, debug, and fix any failures before continuing."
- "Ensure your new tests clearly document what aspect of the implementation they verify, and group related tests into small, focused methods."

### Completion Prompts
- "Before marking the phase as complete, cross-check that all todos and requirements from the implementation plan for this phase are addressed. Document any deviations or technical decisions."
- "Confirm all specified tests pass and no regressions are introduced. List any additional manual validation steps required to fully complete this phase."
- "After finishing all phases, perform a final code review to verify clarity, adherence to project guidelines, and elimination of code smells."


