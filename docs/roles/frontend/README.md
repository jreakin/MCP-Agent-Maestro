# Frontend Agent Documentation

## Overview

Frontend agents specialize in UI/UX implementation, component development, and browser-based testing.

## Key Responsibilities

- Implement React/UI components
- Follow design system guidelines
- Use Playwright for visual validation
- Ensure responsive design
- Integrate with backend APIs

## Component Patterns

### React Component Structure

```typescript
export function ComponentName({ props }: Props) {
  // Component logic
  return <div>...</div>
}
```

### State Management

- Use Zustand for global state
- Use React Query for server state
- Keep component state local when possible

## Playwright Usage

- Use Playwright for visual testing
- Validate UI interactions
- Check responsive layouts
- Test accessibility

## Best Practices

- Follow component library patterns
- Ensure accessibility (a11y)
- Test across browsers
- Optimize for performance

