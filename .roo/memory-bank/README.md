# Memory Bank: Weather Lab

## Purpose
This memory bank is Cline's complete knowledge base for the Weather Lab project. Since Cline's memory resets between sessions, these files are the **only** link to previous work. They must be maintained with precision and clarity.

## File Structure & Reading Order

### 1. Start Here: [`projectbrief.md`](./projectbrief.md)
**Foundation document** - Read this FIRST
- Core requirements and goals
- Key constraints
- Project structure overview
- Success criteria

### 2. Product Layer: [`productContext.md`](./productContext.md)
**Why and how the system works**
- Problem being solved
- User flow and experience
- Key features
- What makes this special

### 3. Architecture Layer: [`systemPatterns.md`](./systemPatterns.md)
**Deep technical patterns**
- Multi-agent hierarchy
- Design patterns (Sequential Agent, Session State, Two-Level Caching)
- Critical implementation paths (cache hit vs. miss)
- Component relationships
- Data flow diagrams

### 4. Technology Layer: [`techContext.md`](./techContext.md)
**Implementation details**
- Technology stack (Google ADK, Gemini, OpenWeather)
- Dependencies and setup
- Environment configuration
- Deployment considerations
- Known technical debt

### 5. Current State: [`activeContext.md`](./activeContext.md)
**What's happening NOW**
- Current work focus
- Recent changes
- Next steps and priorities
- Active decisions and rationale
- Important patterns and conventions

### 6. Progress Tracking: [`progress.md`](./progress.md)
**Status dashboard**
- What works (completed features)
- What's left to build (todo list)
- Known issues
- Performance metrics
- Milestone goals

## How to Use This Memory Bank

### When Starting Work
**MUST READ** (in order):
1. [`projectbrief.md`](./projectbrief.md) - Understand the project
2. [`activeContext.md`](./activeContext.md) - See current focus
3. [`progress.md`](./progress.md) - Check what's done vs. todo

**READ AS NEEDED**:
- [`systemPatterns.md`](./systemPatterns.md) - When implementing features
- [`techContext.md`](./techContext.md) - When setting up or troubleshooting
- [`productContext.md`](./productContext.md) - When making UX decisions

### When Updating Memory Bank

#### Trigger: "**update memory bank**" Command
User may request a memory bank update. When this happens, you MUST:
1. **Review ALL files** - Even if only some need updates
2. **Update [`activeContext.md`](./activeContext.md)** - Always current state
3. **Update [`progress.md`](./progress.md)** - Always status dashboard
4. **Update others as needed** - Based on what changed

#### Trigger: Significant Changes
Update memory bank after:
- Implementing new features
- Making architectural decisions
- Discovering new patterns
- Completing milestones
- Learning important project insights

#### What to Update
- **Always**: [`activeContext.md`](./activeContext.md), [`progress.md`](./progress.md)
- **Architecture changes**: [`systemPatterns.md`](./systemPatterns.md)
- **New tech/dependencies**: [`techContext.md`](./techContext.md)
- **Requirements change**: [`projectbrief.md`](./projectbrief.md)
- **UX/product decisions**: [`productContext.md`](./productContext.md)

### Best Practices

#### Keep It Current
- Update memory bank BEFORE completing a task
- Document decisions with rationale
- Capture learnings as they happen

#### Be Specific
- Include file paths and line numbers: `[agent.py:22-38](../../weather_agent/agent.py#L22-L38)`
- Add code examples when relevant
- Explain WHY, not just WHAT

#### Cross-Reference
- Link between files: `See [systemPatterns.md](./systemPatterns.md) for details`
- Reference project files: `[improvement-plan.md](../../weather_agent/improvement-plan.md)`
- Maintain consistency across files

#### Avoid Duplication
- Each file has a specific purpose
- Don't repeat detailed info - reference instead
- Keep projectbrief.md high-level, systemPatterns.md deep

## File Relationships

```
projectbrief.md (Foundation)
    ↓
    ├→ productContext.md (Why/How)
    ├→ systemPatterns.md (Architecture)
    └→ techContext.md (Implementation)
        ↓
    activeContext.md (Current State)
        ↓
    progress.md (Status Dashboard)
```

## Quick Reference

### When Implementing Features
Read: [`systemPatterns.md`](./systemPatterns.md) → [`activeContext.md`](./activeContext.md)

### When Debugging
Read: [`techContext.md`](./techContext.md) → [`systemPatterns.md`](./systemPatterns.md)

### When Planning
Read: [`activeContext.md`](./activeContext.md) → [`progress.md`](./progress.md)

### When Onboarding
Read: [`projectbrief.md`](./projectbrief.md) → [`productContext.md`](./productContext.md) → [`progress.md`](./progress.md)

## Version History

- **2025-12-26**: Initial memory bank creation
  - All 6 core files created
  - Captured complete system state as of Dec 26, 2025
  - Documented architecture, patterns, and optimization roadmap
  - Established baseline for future development
