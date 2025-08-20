# Create Research Documentation

This rule guides the creation of a comprehensive research document for a new feature. The goal is to gather all necessary context, patterns, and documentation to ensure a smooth, one-pass implementation by an AI agent.

The agent will only have access to the codebase and the final research document you create. It is critical that your research findings are included or clearly referenced. The agent has web search capabilities, so providing URLs to documentation and examples is highly effective.

## Research Process

1.  **Codebase Analysis (Internal Research)**

    - Search for similar features, components, or logic within the current codebase.
    - Identify existing conventions, principles, patterns, and architectural choices to follow for consistency.
    - Note any relevant modules, services, or APIs that will need to be integrated.
    - Note how we can build upon the existing architecture rather than introducing completely new paradigms. Identify extension points in the current design and leverage them for new functionality.
    - Before creating new pages, components, or flows, conduct a thorough inventory of existing elements in the codebase. Search for similar functionality using relevant keywords and file patterns. Identify opportunities to reuse or extend existing components rather than creating duplicates. When similar features exist, analyze them to understand if they can be parameterized or adapted instead of duplicated. Maintain a mental model of the application’s structure to recognize when proposed solutions might create redundant elements. When similar pages or flows are needed, consider creating abstracted components that can be reused with different data or configurations, promoting DRY (Don’t Repeat Yourself) principles.

2.  **External Research**

    - Find official documentation for any libraries, frameworks, or APIs to be used.
    - Search for best practices, implementation examples (from GitHub repos, StackOverflow, blogs), and common pitfalls related to the feature.
    - Is it better to off this to a No-Code backend platform, such as N8N or Make? You should consider an external backend when a functionality you want to create depends on multiple steps, triggers, and complex integrations.

    - **You must find at least 5-7 high-quality resources.**

3.  **User Clarification** (if needed)
    - Before writing the PRD, the AI _must_ ask clarifying questions to gather sufficient detail. The goal is to understand the "what" and "why" of the feature, not necessarily the "how" (which the developer will figure out). Make sure to provide options in letter/number lists so I can respond easily with my selections.
    - For any Github repos, ask the user to manually add it into gitingest.com or code2tutorial.com to get a markdown format that can be inserted to the research doc.

---

## Research Doc Template

Use the following Markdown structure to format your final research document.

### 1. Feature Overview

_(Briefly describe the feature to be implemented, its purpose, and the high-level requirements.)_

### 2. Research & Resources

#### 2.1. Internal Codebase Analysis

For this section, provide a structured, actionable summary that enables consistent, reusable, and non-redundant implementation. The output should include:

- **Summary Table of Relevant Code**  
  | Area/Feature | File(s) | Description | Reuse/Extension Opportunity |
  |--------------|---------|-------------|----------------------------|
  | | | | |

- **Existing Patterns & Conventions**

  - List and describe any architectural patterns, naming conventions, or design principles relevant to the new feature.

- **Reusable Components/Modules**

  - Identify components, modules, or services that can be reused or extended. For each, provide:
    - File path
    - Brief description
    - How it could be adapted or extended

- **Integration Points**

  - List any modules, services, or APIs that the new feature should integrate with. Note any extension points or hooks.

- **Potential Redundancies**

  - Highlight areas where similar functionality exists, and recommend whether to reuse, extend, or refactor.

- **Backward Compatibility Considerations**

  - Note any changes that could impact existing features, and how to avoid breaking them.

- **Summary of Recommendations**
  - A concise summary of how to proceed, referencing the findings above.

#### 2.2. External Documentation & Examples

_(Provide a list of all external documentation. For each resource, provide a link, a brief description, and a detailed explanation of how it should be used. This is the most critical section.)_

_(Reference specific files and code blocks codebase thjat should be used as a template. Explain what aspects should be mimicked.)_

**(List at least 5-7 resources here)**

**Example Format:**

**Resource 1: [Name of Resource, e.g., React Docs - Handling Events]**

- **URL**: [Link to the documentation]
- **Description**: Official React documentation on handling user events.
- **How to Use**:
  - **Event Persistence**: The section on `event.persist()` is critical. We must call this if we need to access an event asynchronously to prevent it from being nullified.
  - **Passing Handlers**: Follow the patterns here for passing event handlers as props to child components.

### 3. Implementation Plan

#### 3.1. Approach & Pseudocode

Reflect on 5-7 different possible sources of the problem, distill those down to 2-3 most likely sources. Analyze the root cause thoroughly, plan your approach carefully, then give your top 3 recommended approach.

_(For each approach, outline the proposed implementation strategy. Use pseudocode to illustrate the logic and structure.)_

- **Comment non-obvious code** and ensure everything is understandable to a junior developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

```pseudocode
function NewFeatureComponent({ userId }) {
  // Use the useApi hook to fetch user data
  const { data, error, isLoading } = useApi(`/users/${userId}`);

  // Handle loading and error states
  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage message={error.message} />;

  // Render the component with the fetched data
  return <UserProfile data={data} />;
}
```

#### 3.2. Key Considerations & Gotchas

_(List any library quirks, version-specific issues, or potential challenges identified during research.)_

Capture important details such as, Authentication requirements, Rate limits or quotas, Common pitfalls, performance requirements

- **Gotcha 1**: The charting library we use does not automatically re-render on data updates. We must manually trigger a chart update.
- **Gotcha 2**: Ensure all API calls handle the new rate-limiting headers.

---

**_CRITICAL INSTRUCTIONS_**

1.  **_AFTER you are done researching and exploring the codebase, STOP and ask the user if they have any documentation or URLs for external research before proceeding.._**
2.  **_ULTRATHINK about the feature and plan your approach based on the template above._**
3.  **_WRITE the research doc. Be thorough. Do not spare any expense on research._**

---

## Output

- **Format:** Markdown (`.md`)
- **Location:** `3-tasks/`
- **Filename:** `research-[feature-name].md`

## Quality Checklist

- [ ] Is the feature overview clear and concise?
- [ ] Have we done comprehensive internal research?
- [ ] Are there at least 5-7 high-quality external resources?
- [ ] Is the "How to Use" for each resource specific and actionable?
- [ ] Are relevant code patterns clearly identified?
- [ ] Is the implementation plan logical and supported by pseudocode?
- [ ] Are potential gotchas documented?

Remember: The goal is one-pass implementation success through comprehensive context.

```

```

```

```
