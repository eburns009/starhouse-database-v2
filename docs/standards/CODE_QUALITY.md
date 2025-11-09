# Code Quality Standards

**Last Updated:** October 30, 2025
**Applies To:** All code in this repository

---

## Overview

This document defines code quality standards for the StarHouse Database V2 project. All code must meet these standards before being merged to `main`.

---

## General Principles

### 1. Readability First
- Code is read 10x more than written
- Optimize for the next developer (or future you)
- Prefer clarity over cleverness

### 2. Consistency
- Follow existing patterns in the codebase
- Use linters and formatters
- Code should look like one person wrote it

### 3. Testability
- Write code that's easy to test
- Avoid global state
- Use dependency injection

### 4. Performance
- Optimize only when needed
- Measure before optimizing
- Document performance-critical sections

---

## TypeScript Standards

### Strict Mode
```typescript
// tsconfig.json - REQUIRED
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### No `any` Types
```typescript
// ❌ BAD
function handleData(data: any) {
  return data.value;
}

// ✅ GOOD
interface DataPayload {
  value: string;
  timestamp: Date;
}

function handleData(data: DataPayload): string {
  return data.value;
}
```

### Explicit Return Types
```typescript
// ❌ BAD
async function fetchUser(id: string) {
  return await supabase.from('users').select().eq('id', id);
}

// ✅ GOOD
interface User {
  id: string;
  email: string;
  name: string;
}

async function fetchUser(id: string): Promise<User | null> {
  const { data, error } = await supabase
    .from('users')
    .select()
    .eq('id', id)
    .single();

  if (error) throw error;
  return data;
}
```

### Error Handling
```typescript
// ❌ BAD - Swallowing errors
try {
  await riskyOperation();
} catch (e) {
  // Silent failure
}

// ✅ GOOD - Proper error handling
try {
  await riskyOperation();
} catch (error) {
  if (error instanceof ValidationError) {
    logger.warn('Validation failed', { error });
    return fallbackValue;
  }

  logger.error('Operation failed', { error: error.message, stack: error.stack });
  throw error; // Re-throw if can't handle
}
```

---

## Python Standards

### Type Hints (Required)
```python
# ❌ BAD
def calculate_total(transactions):
    return sum(t['amount'] for t in transactions)

# ✅ GOOD
from typing import List, Dict

def calculate_total(transactions: List[Dict[str, float]]) -> float:
    """Calculate total from list of transactions."""
    return sum(t['amount'] for t in transactions)
```

### Docstrings (Required for Public Functions)
```python
def update_contact(contact_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update contact record in database.

    Args:
        contact_id: UUID of contact to update
        updates: Dictionary of fields to update

    Returns:
        True if update successful, False otherwise

    Raises:
        ValueError: If contact_id is invalid
        DatabaseError: If database operation fails
    """
    pass
```

### PEP 8 Compliance
```bash
# Use Black for formatting
black scripts/

# Use pylint for linting
pylint scripts/ --max-line-length=100

# Use mypy for type checking
mypy scripts/ --strict
```

---

## React/JSX Standards

### Functional Components Only
```jsx
// ❌ BAD - Class components
class UserList extends React.Component {
  render() {
    return <div>{this.props.users.map(...)}</div>;
  }
}

// ✅ GOOD - Functional with hooks
function UserList({ users }: { users: User[] }): JSX.Element {
  return (
    <div>
      {users.map(user => <UserCard key={user.id} user={user} />)}
    </div>
  );
}
```

### Props Interface
```tsx
// ❌ BAD - No prop types
function Button({ onClick, label }) {
  return <button onClick={onClick}>{label}</button>;
}

// ✅ GOOD - TypeScript interface
interface ButtonProps {
  onClick: () => void;
  label: string;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

function Button({ onClick, label, disabled = false, variant = 'primary' }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {label}
    </button>
  );
}
```

### Hooks Rules
```tsx
// ❌ BAD - Conditional hooks
function Component({ shouldFetch }) {
  if (shouldFetch) {
    const data = useFetch('/api/data'); // ❌ Conditional hook
  }
}

// ✅ GOOD - Hooks at top level
function Component({ shouldFetch }) {
  const data = useFetch(shouldFetch ? '/api/data' : null);
}
```

---

## Database Standards

### Always Use Indexes
```sql
-- ❌ BAD - No index on foreign key
CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  contact_id UUID NOT NULL -- Missing index!
);

-- ✅ GOOD - Indexed foreign key
CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  contact_id UUID NOT NULL,
  FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE INDEX idx_transactions_contact_id ON transactions(contact_id);
```

### Use Constraints
```sql
-- ❌ BAD - No validation
CREATE TABLE contacts (
  email TEXT
);

-- ✅ GOOD - Constraints
CREATE TABLE contacts (
  email CITEXT NOT NULL UNIQUE,
  CONSTRAINT email_format CHECK (email ~* '^[^@]+@[^@]+\.[^@]+$')
);
```

### Never SELECT *
```sql
-- ❌ BAD
SELECT * FROM contacts WHERE id = '123';

-- ✅ GOOD - Explicit columns
SELECT id, email, first_name, last_name FROM contacts WHERE id = '123';
```

---

## Testing Standards

### Test Coverage
- **Minimum:** 80% overall
- **Critical Paths:** 100% (payment, authentication)
- **New Code:** Must have tests before merge

### Test Structure
```typescript
// ✅ GOOD - Descriptive test names
describe('ContactsList', () => {
  describe('when loading', () => {
    it('should display loading spinner', () => {
      // Test
    });
  });

  describe('when loaded with contacts', () => {
    it('should display contact list', () => {
      // Test
    });

    it('should allow filtering by email', () => {
      // Test
    });
  });

  describe('when error occurs', () => {
    it('should display error message', () => {
      // Test
    });

    it('should provide retry button', () => {
      // Test
    });
  });
});
```

### Test Isolation
```typescript
// ❌ BAD - Tests depend on each other
let sharedState;

test('first test', () => {
  sharedState = doSomething();
});

test('second test', () => {
  expect(sharedState).toBe(...); // ❌ Depends on previous test
});

// ✅ GOOD - Independent tests
describe('feature', () => {
  let state;

  beforeEach(() => {
    state = createFreshState();
  });

  test('first test', () => {
    // Use state
  });

  test('second test', () => {
    // Use fresh state
  });
});
```

---

## Documentation Standards

### Code Comments
```typescript
// ❌ BAD - Obvious comment
// Increment counter
counter++;

// ❌ BAD - Outdated comment
// TODO: Fix this hack (from 2 years ago)
const value = data?.value;

// ✅ GOOD - Explains why
// Use optional chaining because PayPal webhooks sometimes
// omit this field for free transactions
const value = data?.value ?? 0;

// ✅ GOOD - Documents complex logic
/**
 * Calculate prorated refund amount.
 *
 * Formula: (days_remaining / total_days) * original_amount
 * Edge case: If cancelled on last day, refund $0
 */
function calculateRefund(subscription: Subscription): number {
  // Implementation
}
```

### README Requirements
Every directory with significant code needs a README:

```markdown
# Directory Name

## Purpose
Brief description of what this directory contains.

## Key Files
- `file1.ts`: Description
- `file2.ts`: Description

## Usage
How to use/run the code in this directory.

## Testing
How to test this code.
```

---

## Security Standards

### Never Hardcode Secrets
```typescript
// ❌ CRITICAL - Hardcoded secret
const API_KEY = 'sk_live_abc123';

// ✅ GOOD - Environment variable
const API_KEY = Deno.env.get('API_KEY');
if (!API_KEY) throw new Error('API_KEY not set');
```

### Validate All Input
```typescript
// ❌ BAD - No validation
function createUser(email: string) {
  await db.insert({ email });
}

// ✅ GOOD - Validated input
function createUser(email: string) {
  if (!isValidEmail(email)) {
    throw new ValidationError('Invalid email format');
  }
  if (email.length > 255) {
    throw new ValidationError('Email too long');
  }
  await db.insert({ email: email.toLowerCase() });
}
```

### Sanitize Error Messages
```typescript
// ❌ BAD - Leaks internal details
catch (error) {
  return { error: error.message }; // Might expose database structure
}

// ✅ GOOD - Generic message
catch (error) {
  logger.error('Operation failed', { error }); // Log details
  return { error: 'Internal server error' }; // Generic to client
}
```

---

## Performance Standards

### Pagination Required
```typescript
// ❌ BAD - Load all records
const contacts = await supabase.from('contacts').select();

// ✅ GOOD - Paginated
const contacts = await supabase
  .from('contacts')
  .select()
  .range(0, 49)  // Load 50 at a time
  .order('created_at', { ascending: false });
```

### Avoid N+1 Queries
```typescript
// ❌ BAD - N+1 queries
const contacts = await getContacts();
for (const contact of contacts) {
  contact.transactions = await getTransactions(contact.id); // N queries!
}

// ✅ GOOD - Single query with join
const contacts = await supabase
  .from('contacts')
  .select(`
    *,
    transactions (*)
  `)
  .limit(50);
```

### Cache Expensive Operations
```typescript
// ❌ BAD - Recompute every time
function getDashboardStats() {
  return {
    totalRevenue: await calculateTotalRevenue(), // Expensive!
    activeUsers: await countActiveUsers(),
    // ...
  };
}

// ✅ GOOD - Cache for 5 minutes
const statsCache = new Map();
function getDashboardStats() {
  const cached = statsCache.get('stats');
  if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
    return cached.data;
  }

  const stats = {
    totalRevenue: await calculateTotalRevenue(),
    activeUsers: await countActiveUsers(),
  };

  statsCache.set('stats', { data: stats, timestamp: Date.now() });
  return stats;
}
```

---

## Code Review Checklist

### Before Submitting PR

- [ ] All tests passing locally
- [ ] Linter passing (no warnings)
- [ ] Type checking passing (no `any` types)
- [ ] Code formatted (Prettier/Black)
- [ ] Added tests for new code
- [ ] Updated documentation
- [ ] No console.log() statements
- [ ] No commented-out code
- [ ] Branch up to date with main

### Reviewer Checklist

- [ ] Code follows style guide
- [ ] Tests are comprehensive
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] Error handling proper
- [ ] Documentation clear
- [ ] No breaking changes (or documented)
- [ ] PR description explains "why"

---

## Enforcement

### Pre-commit Hooks
```bash
# Automatically run on git commit
- Run tests
- Run linter
- Check formatting
- Block commit if any fail
```

### CI Pipeline
```yaml
# Runs on every PR
- Run all tests (required)
- Check coverage ≥ 80% (required)
- Run linter (required)
- Security scan (required)
- Build check (required)
```

### Merge Requirements
- ✅ All CI checks passing
- ✅ At least 1 approval
- ✅ Branch up to date
- ✅ No unresolved comments

---

## Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [React Best Practices](https://react.dev/learn/thinking-in-react)
- [SQL Style Guide](https://www.sqlstyle.guide/)

---

**Next Steps:**
1. Review this guide
2. Set up linting and formatting
3. Enable pre-commit hooks
4. Start enforcing in code reviews
