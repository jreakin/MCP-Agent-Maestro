# Role-Specific Documentation

This directory contains role-specific documentation to help agents understand their responsibilities and access relevant information quickly.

## Directory Structure

- `worker/` - Implementation patterns, file status checking, coding standards
- `frontend/` - Component patterns, Playwright usage, UI/UX guidelines
- `security/` - Security review checklists, vulnerability patterns, best practices
- `research/` - Architecture analysis, read-only exploration guides, design patterns
- `manager/` - Coordination patterns, task delegation, project overview

## Usage

Agents querying the RAG system will automatically receive role-appropriate documentation based on their agent role and capabilities.

## Adding Role Documentation

1. Create markdown files in the appropriate role directory
2. Use clear headings and code examples
3. Include relevant patterns and best practices
4. The RAG system will automatically index these files

