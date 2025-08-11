
# 🛠️ **Development Workflow Guide**

---

## 🚀 **Phase 1: Project Initialization**

### 1.1 Setup New Project

- [ ] **Initialize in Lovable and pull to Cursor:** Use the `initialize-Lovable-Project.md` file
  - Specify Tailwind v3, not v4
  - Port over to Cursor and initialize the git repo locally
  - Ensure global cursor rules and Claude.MD rules are properly configured for automatic reading

### 1.2 CSS Configuration

- [ ] **Add CSS Foundation**

  - Find a TweakCN CSS file and copy it to your `index.css` file. delete your app.css file.
  - Ensure it's in the correct Tailwind version and uses HSL format
  - **Don't install via pnpm** (it causes bugs)
  - Use `@1a. css-validation-tweakcn.md` for necessary instructions

  Make sure the check the CSS file first. And then check the fonts as the tailwind config doesn't have font families configured. Needs to be added .

  https://tweakcn.com/ Use the generate feature to copy styles from other companies.

---

## 📋 **Phase 2: Product Planning**

### 2.1 Product Roadmap Development

- [ ] **Generate Product Roadmap**
  - Use `generate-ProductRoadmap.mdc` to create comprehensive product roadmap
- [ ] **MVP Feature Selection**
  - From the generated roadmap, select only features essential for the Minimum Viable Product (MVP)

---

## 🎨 **Phase 3: Design Implementation**

### 3.1 HTML Prototype Development

- [ ] **Create UI Implementation Plan**

  - Based on MVP features and screenshots, use `@1b. generate-ui-implementation-plan.md`
  - This creates a skeleton of all UI elements that need implementation
  - Reference `2a.` and manually integrate CSS and design principles (not system)

- [ ] **Create HTML Variants**

  - Use `2b` and `2c` to create variants in HTML
  - This helps visualize and build out prototypes
  - **Tip:** Use Stagewise or Lovable's UI to select elements before making changes

- [ ] **Review HTML Mockups**
  - Validate the HTML prototypes before proceeding

### 3.2 ShadCN Implementation

- [ ] **Create ShadCN Implementation Plan**

  - Use `2d` with finalized HTML prototype, screenshots, design system, and CSS
  - **Important:** Feed information step-by-step to prevent context overload

- [ ] **Integrate ShadCN Components**

  - Update plan with `3a` to use ShadCN components via MCP

- [ ] **Enhance Implementation Details**

  - Use `3b` to focus on more detailed implementation

- [ ] **Ship with ShadCN**
  - Finalize with `3c` using ShadCN MCP and instructions
  - **Quality Check:** Verify all CSS and design system elements are properly applied
  - **Tip:** Use Stagewise or Lovable's UI to select elements before making changes

### 3.3 Advanced UI Extensions

- [ ] **Add 21st-dev Extensions**
  - Choose desired 21st dev UI components
  - Use pnpm to manually change components
  - **Avoid 'copy prompt'** - manually create reference components, import, and update

---

## 🚢 **Phase 4: Deployment & Version Control**

### 4.1 Post-Screen Completion Workflow (Lovable)

- [ ] **Code Quality & Documentation**

  - Refactor code using `cursor-auto-refactoring-codebase.md`
  - Add documentation using `add.JSDOC.md`
  - Generate README using `generate-read-me.md` or repomix
  - Update repo with improved cursor and claude.md rules using repomix

- [ ] **Version Control Management**
  - Push changes to GitHub after completing the first screen
  - Push into Lovable

---

## 🏗️ **Phase 5: Post-MVP Development**

### 5.1 Core Infrastructure Setup

- [ ] **Authentication Setup**

  - Implement user authentication system

- [ ] **Database Configuration**

  - Create database using Supabase

- [ ] **Payment Integration**

  - Set up payments via Lovable
  - Direct integration with Supabase and Stripe

- [ ] **Email Integration**
  - Add Resend email integration

---

## ⚙️ **Phase 6: Backend Development**

### 6.1 Backend Logic Implementation

- [ ] **Research Phase**

  - Run `create research doc.mdc` (skip to PRD if feature is simple)
    - Internal evaluation of the codebase
    - External research
    - use https://code2tutorial.com/ and https://gitingest.com/ and https://repomix.com/ to give examples
    - Use MCPs like the brave MCP to do extra research
    - Use MCPs like context7 to get API docs.

- [ ] **Requirements Documentation**

  - Use `generate PRD document` (after research document completion)
    - Detail implementation for the feature

- [ ] **Task Generation**

  - Use `generate tasks from PRD.mdc` (once PRD is satisfactory)
    - Generate comprehensive task list

- [ ] **Task Execution**
  - Use `task list.mdc`
    - Execute tasks (provide AI with execution guidance)

### 6.2 Post-Backend Development Workflow

- [ ] **Code Quality & Documentation**
  - Refactor code using `cursor-auto-refactoring-codebase.md`
  - Add documentation using `add.Docstring.md`
  - Generate README using `generate-read-me.md` or repomix
  - Update repo with improved cursor and claude.md rules using repomix
  - Reference: [Repomix](https://repomix.com)

### 6.3 Testing Implementation

- [ ] **Unit Testing Setup**
  - Configure Jest/Vitest for component testing
  - Aim for 80%+ test coverage on critical business logic

---

## 📚 **General Guidelines & Best Practices**

### Development Standards

- [ ] **Always create a README file** after completing major tasks using `generate-read-me.mdc`
- [ ] **Commit locally** to Git frequently - things will break
- [ ] **Use voice dictation** for efficiency

### Version Control Best Practices

- [ ] **Be cautious with remote commits** - only commit when confident you've reached a real checkpoint
- [ ] **Manage Lovable-Cursor conflicts** - forgetting to pull will cause bugs

### Workflow Efficiency

- [ ] Use Stagewise or Lovable's UI to select elements before requesting changes
- [ ] Feed information step-by-step to prevent AI context overload
- [ ] Manually create and import reference components rather than using 'copy prompt'
