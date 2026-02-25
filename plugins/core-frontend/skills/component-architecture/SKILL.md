---
name: core-frontend:component-architecture
description: "Framework-agnostic component patterns: composition (slots/children/render props), compound components, headless components, controlled vs uncontrolled, prop drilling vs context, and component API design."
user-invocable: false
---

# Component Architecture Quick Reference

## Core Composition Patterns

### Children / Slots / Content Projection

The most fundamental composition pattern: a component accepts child content to render in a designated area. Every framework has this concept under different names.

| Framework | Mechanism | Named slots |
|-----------|-----------|-------------|
| React | `children` prop, render props | Named props (`header`, `footer`) |
| Svelte | `{@render children()}`, `{#snippet}` | Named snippets |
| Vue | `<slot>`, `<slot name="x">` | Named slots |
| Angular | `<ng-content>`, `<ng-content select>` | Content projection |
| Web Components | `<slot>`, `<slot name="x">` | Named slots |

**When to use:** Any component that wraps content — layouts, cards, modals, toolbars, list items.

### Compound Components

A group of components that work together, sharing implicit state. The parent manages state; children consume it via context.

```
<Tabs>
  <TabList>
    <Tab>Account</Tab>
    <Tab>Security</Tab>
  </TabList>
  <TabPanels>
    <TabPanel>Account settings...</TabPanel>
    <TabPanel>Security settings...</TabPanel>
  </TabPanels>
</Tabs>
```

**Characteristics:**
- Parent owns the state (active tab, open accordion item)
- Children access shared state via context/injection (not props)
- Children can be reordered, wrapped, or customized without breaking functionality
- The API reads like natural markup

**When to use:** Tabs, accordions, select/option, menu systems, form field groups, radio groups.

### Headless Components

Components that provide behavior and state management without any DOM or styling. The consumer provides all rendering.

**What headless components handle:**
- Keyboard navigation (arrow keys, Enter, Escape)
- ARIA attributes (roles, states, properties)
- Focus management (trapping, restoration)
- State machines (open/closed, selected, active)

**What the consumer handles:**
- All DOM structure
- All styling and layout
- Animation and transitions

**Popular headless libraries:**
- React: Radix UI Primitives, React Aria (Adobe), Downshift
- Svelte: Bits UI, Melt UI
- Vue: Radix Vue, Headless UI
- Angular: Angular CDK
- Framework-agnostic: Shoelace (web components), Zag.js (state machines)

**When to use:** Complex interactive widgets where you need full styling control — selects, comboboxes, date pickers, dialogs, popovers.

### Render Props / Function-as-Child

A component calls a consumer-provided function, passing state and helpers. The consumer decides what to render. Headless components are the modern evolution of this pattern.

## Controlled vs Uncontrolled

| Aspect | Controlled | Uncontrolled |
|--------|-----------|-------------|
| State lives in | Parent component | Component itself (internal) |
| Value source | Props from parent | Internal state / DOM |
| Update mechanism | Parent callback | Internal handler + optional event |
| Use case | Forms with validation, synced state | Simple inputs, file uploads |
| Complexity | Higher (parent manages all state) | Lower (component self-manages) |

**Best practice:** Default to uncontrolled with an optional controlled override. Accept a `value` prop and an `onChange` callback. If `value` is provided, the component is controlled. If not, it manages its own state internally.

```
// Pseudocode: controlled/uncontrolled pattern
function Input({ value: controlledValue, onChange, defaultValue }) {
  // If value prop exists, component is controlled
  const isControlled = controlledValue !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue);

  const value = isControlled ? controlledValue : internalValue;

  function handleChange(newValue) {
    if (!isControlled) setInternalValue(newValue);
    onChange?.(newValue);
  }
}
```

## Prop Drilling vs Context/Injection

### Prop Drilling

Passing data through intermediate components that don't use it.

```
App -> Layout -> Sidebar -> UserMenu -> Avatar
                                         ^
                                    needs user data
```

**When prop drilling is fine:**
- 1-2 levels deep
- Data is used by intermediate components too
- The prop path is obvious and stable

### Context / Dependency Injection

Providing data to deeply nested components without passing through every level.

| Framework | Mechanism |
|-----------|-----------|
| React | `createContext` + `useContext` |
| Svelte | `setContext` + `getContext` |
| Vue | `provide` + `inject` |
| Angular | Dependency Injection (services) |

**When to use context:**
- Theme/design token values
- Authenticated user data
- Locale/i18n settings
- Feature flags
- Compound component shared state

**When NOT to use context:**
- Frequently changing data (causes re-renders in React)
- Data only needed 1-2 levels deep (just pass props)
- Application state that should be in a state manager

## Component API Design Principles

### 1. Sensible Defaults

Every prop should have a reasonable default. The component should be useful with zero props.

### 2. Composition Over Configuration

Prefer accepting children/slots over adding props for every variation.

```
// Bad: configuration explosion
<Card title="Hello" subtitle="World" icon="star" footer="..." />

// Good: composition
<Card>
  <CardHeader>
    <Icon name="star" />
    <h2>Hello</h2>
    <p>World</p>
  </CardHeader>
  <CardBody>...</CardBody>
  <CardFooter>...</CardFooter>
</Card>
```

### 3. Spread Unknown Props

Forward unknown props to the root DOM element so consumers can add `class`, `id`, `data-*`, `aria-*` attributes.

### 4. Consistent Naming

| Convention | Examples |
|-----------|---------|
| Boolean props | `disabled`, `open`, `loading` (not `isDisabled`) |
| Event callbacks | `onChange`, `onClose`, `onSelect` |
| Render slots | `header`, `footer`, `children` |
| Variants | `variant="primary"`, `size="sm"` |

### 5. Single Responsibility

Each component does one thing. If a component needs a comment like "this handles X AND Y", split it.

## Additional Resources

- [component-reference.md](component-reference.md) — Component organization patterns, file structure conventions, component testing strategies, performance patterns, error boundaries
