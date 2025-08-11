# Claude Code Instructions

## Subagents

use the error-debugger and validation-gates subagents

Invoke it this way: Use the error-debugger subagent to check my recent changes

## Parent directories (for monorepos)

root/CLAUDE.md # General project info
root/frontend/CLAUDE.md # Frontend-specific context
root/backend/CLAUDE.md # Backend-specific context

##Thinking Scale

Select Thinking Mode

Default

Think

Think hard

Think hardest (This option is checked)

Think harder

Ultrathink

## Setup and Configuration

### MCP Servers to Add

Ask Claude to add these MCPs:

- https://github.com/mendableai/firecrawl-mcp-server
- https://github.com/Jpisnice/shadcn-ui-mcp-server
- https://github.com/upstash/context7

### CCUNDO Integration

Add CCUNDO to claude:

- https://github.com/RonitSachdev/ccundo

## Core Workflow

### Initialization

1. Always use `/init` to initialize a claude.md
2. Then run `/ide`
3. Use Shift tab to switch between auto run mode and plan mode
4. Always start with plan mode

### Context Management

- Claude code shows you how full your context window is
- Run `/compact` to clear the claude code context window, but keep a summary
- `/clear` removes all context window and resets the general claude.md rules

### File References

- Claude code's fuzzy searching/indexing is not as good
- Make sure to either drag the file in or use `@` to reference files

### Starting Claude

- Type in claude to start
- Use kimi 2 using export
- `/export` lets you copy the history of the chat to clipboard
- `/resume` lets you go back to an old chat
- `#` lets you hard code memories

## Terminal Commands

### Navigation Shortcuts

- Control A to go to first line
- Control K to delete
- Control W to delete words

### Permission Bypass

You can use `claude --dangerously-skip-permissions` to bypass all permission checks and let Claude work uninterrupted until completion.

## Best Practices

### Stochastic Nature Utilization

One of the most powerful LLM/CodeGen agent patterns I find most people are NOT utilizing is the stochastic nature they have. Having an abundance mindset, and not hesitating to run the same prompt multiple times. Being able to fork context is a HUGE help in this workflow, as at any point you can branch off to see what variations Claude Code (etc) may come up with.

### Context Management Strategy

- Make sure to do `/init` to update the claude.md file. It follows this very strongly.
- Make sure to new tab, resume, and ask give a separate instance for reviewing plans.
- Make sure to use double escape to reset the context if you have already come up with a good context, and then basically create new tabs, create `/resume`, and try it again.

## Documentation Reference

Figure this out: https://docs.anthropic.com/en/docs/claude-code/common-workflows

Search this doc for it.
