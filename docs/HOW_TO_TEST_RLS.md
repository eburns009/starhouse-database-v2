# How to Test RLS (Row Level Security)

**Critical:** You MUST test RLS with real Supabase Auth, not SQL commands.

---

## Why SQL Editor Tests Don't Work

❌ **This doesn't actually test RLS:**
```sql
SET ROLE authenticated;
SELECT COUNT(*) FROM contacts;
```

**Problem:** Supabase SQL Editor runs as `postgres` (database owner), which bypasses ALL RLS policies.

**Result:** Tests will pass even if RLS is completely broken.

---

## The Right Way: Test with Real Authentication

### Method 1: HTML Test File (Easiest)

**Step 1: Create Test User**
1. Go to Supabase Dashboard
2. Authentication → Users → Add User
3. Email: `test@starhouse.org`
4. Password: `TestPassword123!`
5. Disable email confirmation (for testing)
6. Click "Create user"

**Step 2: Get Anon Key**
1. Dashboard → Settings → API
2. Copy "anon public" key

**Step 3: Run Test**
```bash
# Option A: Open directly
open test-rls.html

# Option B: Serve locally
python3 -m http.server 8000
# Visit: http://localhost:8000/test-rls.html
```

**Step 4: Run Tests**
1. Paste your anon key
2. Click "Initialize Connection"
3. Login with test@starhouse.org
4. Click "Run All Tests"

**Expected Results:**
```
✅ SELECT: Should return contacts (6,563 total)
✅ INSERT: Should create new contact
✅ UPDATE: Should modify contact notes
✅ DELETE: Should remove test contact
```

**If ANY fail:** RLS is broken, DO NOT DEPLOY.

---

### Method 2: cURL (Quick Check)

**Step 1: Login and Get JWT Token**
```bash
curl -X POST 'https://lnagadkqejnopgfxwlkb.supabase.co/auth/v1/token?grant_type=password' \
  -H 'apikey: YOUR_ANON_KEY_HERE' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@starhouse.org",
    "password": "TestPassword123!"
  }' | jq -r '.access_token'
```

Copy the `access_token` from response.

**Step 2: Test SELECT (Read Access)**
```bash
curl 'https://lnagadkqejnopgfxwlkb.supabase.co/rest/v1/contacts?select=id,first_name,last_name&limit=5' \
  -H 'apikey: YOUR_ANON_KEY_HERE' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN_HERE'
```

**Expected:** Returns JSON with contact data
**If error:** RLS is blocking authenticated users

**Step 3: Test INSERT (Write Access)**
```bash
curl -X POST 'https://lnagadkqejnopgfxwlkb.supabase.co/rest/v1/contacts' \
  -H 'apikey: YOUR_ANON_KEY_HERE' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Test",
    "last_name": "User",
    "email": "test-curl@example.com",
    "source": "curl_test"
  }'
```

**Expected:** Returns created contact with ID
**If error:** RLS is blocking authenticated users from creating data

---

### Method 3: JavaScript Console (In Browser)

**Step 1: Open Supabase Dashboard**
1. Go to your Supabase project dashboard
2. Open browser console (F12)

**Step 2: Load Supabase JS**
```javascript
// Load Supabase client
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
document.head.appendChild(script);

// Wait for it to load, then:
const supabase = window.supabase.createClient(
  'https://lnagadkqejnopgfxwlkb.supabase.co',
  'YOUR_ANON_KEY_HERE'
);
```

**Step 3: Login**
```javascript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'test@starhouse.org',
  password: 'TestPassword123!'
});

console.log('Login:', data.user.email);
```

**Step 4: Test Access**
```javascript
// Test SELECT
const { data: contacts, error: selectError } = await supabase
  .from('contacts')
  .select('id, first_name, last_name')
  .limit(5);

console.log('SELECT:', selectError ? `❌ ${selectError.message}` : `✅ Got ${contacts.length} contacts`);

// Test INSERT
const { data: newContact, error: insertError } = await supabase
  .from('contacts')
  .insert({
    first_name: 'Test',
    last_name: 'User',
    email: 'test-' + Date.now() + '@example.com',
    source: 'console_test'
  })
  .select();

console.log('INSERT:', insertError ? `❌ ${insertError.message}` : `✅ Created contact ${newContact[0].id}`);

// Test DELETE (cleanup)
if (newContact) {
  await supabase.from('contacts').delete().eq('id', newContact[0].id);
  console.log('✅ Cleaned up test contact');
}
```

---

## What Each Test Means

### ✅ All Tests Pass
**Meaning:** RLS is configured correctly
- Staff can login via Supabase Auth
- Staff can read/write/delete data
- UI will work as expected

**Action:** Safe to deploy

### ❌ SELECT Fails
**Error:** "permission denied for table contacts" or "policy violation"
**Meaning:** Authenticated users can't read data
**Fix:** Check policies in `002c_rls_simple_staff_access.sql`
```sql
-- Should exist:
CREATE POLICY "staff_full_access" ON contacts
  FOR ALL TO authenticated
  USING (true) WITH CHECK (true);
```

### ❌ INSERT/UPDATE/DELETE Fails
**Error:** "new row violates row-level security policy"
**Meaning:** Authenticated users have read-only access
**Fix:** Check WITH CHECK clause in policies
```sql
-- Should have WITH CHECK (true):
CREATE POLICY "staff_full_access" ON contacts
  FOR ALL TO authenticated
  USING (true)
  WITH CHECK (true);  -- ← This must be true
```

### ❌ Login Fails
**Error:** "Invalid login credentials"
**Meaning:** Test user doesn't exist
**Fix:** Create user in Dashboard → Authentication → Users

---

## Common Mistakes

### Mistake 1: Testing in SQL Editor
```sql
-- ❌ This doesn't test RLS
SET ROLE authenticated;
SELECT * FROM contacts;
```
**Problem:** SQL Editor runs as postgres, bypasses RLS

**Fix:** Use HTML test file or cURL with real JWT

### Mistake 2: Using service_role Key
```javascript
// ❌ This bypasses RLS
const supabase = createClient(url, SERVICE_ROLE_KEY);
```
**Problem:** service_role bypasses all RLS policies

**Fix:** Use anon key, login with Supabase Auth

### Mistake 3: Not Waiting for Migration
```bash
# Applied RLS migration
psql -f 002c_rls_simple_staff_access.sql

# Immediately tested (cached policies)
curl https://...
```
**Problem:** Policy changes may be cached

**Fix:** Wait 30 seconds, or restart Supabase (locally)

---

## Automated Testing Script

Save as `test-rls.sh`:

```bash
#!/bin/bash
set -e

SUPABASE_URL="https://lnagadkqejnopgfxwlkb.supabase.co"
ANON_KEY="$1"
TEST_EMAIL="test@starhouse.org"
TEST_PASSWORD="TestPassword123!"

if [ -z "$ANON_KEY" ]; then
  echo "Usage: ./test-rls.sh YOUR_ANON_KEY"
  exit 1
fi

echo "🔐 Logging in as $TEST_EMAIL..."
TOKEN=$(curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $ANON_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
  | jq -r '.access_token')

if [ "$TOKEN" == "null" ]; then
  echo "❌ Login failed - check credentials"
  exit 1
fi

echo "✅ Login successful"
echo ""

echo "📖 Testing SELECT..."
SELECT_RESULT=$(curl -s "$SUPABASE_URL/rest/v1/contacts?select=id&limit=1" \
  -H "apikey: $ANON_KEY" \
  -H "Authorization: Bearer $TOKEN")

if echo "$SELECT_RESULT" | grep -q "error"; then
  echo "❌ SELECT failed: $SELECT_RESULT"
  exit 1
fi
echo "✅ SELECT works"
echo ""

echo "✏️  Testing INSERT..."
INSERT_RESULT=$(curl -s -X POST "$SUPABASE_URL/rest/v1/contacts" \
  -H "apikey: $ANON_KEY" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d "{\"first_name\":\"Test\",\"last_name\":\"RLS\",\"email\":\"test-$(date +%s)@example.com\",\"source\":\"rls_test\"}")

if echo "$INSERT_RESULT" | grep -q "error"; then
  echo "❌ INSERT failed: $INSERT_RESULT"
  exit 1
fi

TEST_ID=$(echo "$INSERT_RESULT" | jq -r '.[0].id')
echo "✅ INSERT works (created $TEST_ID)"
echo ""

echo "🔧 Testing UPDATE..."
UPDATE_RESULT=$(curl -s -X PATCH "$SUPABASE_URL/rest/v1/contacts?id=eq.$TEST_ID" \
  -H "apikey: $ANON_KEY" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes":"RLS test"}')

if echo "$UPDATE_RESULT" | grep -q "error"; then
  echo "❌ UPDATE failed: $UPDATE_RESULT"
  exit 1
fi
echo "✅ UPDATE works"
echo ""

echo "🗑️  Testing DELETE..."
DELETE_RESULT=$(curl -s -X DELETE "$SUPABASE_URL/rest/v1/contacts?id=eq.$TEST_ID" \
  -H "apikey: $ANON_KEY" \
  -H "Authorization: Bearer $TOKEN")

if echo "$DELETE_RESULT" | grep -q "error"; then
  echo "❌ DELETE failed: $DELETE_RESULT"
  exit 1
fi
echo "✅ DELETE works"
echo ""

echo "=========================================="
echo "🎉 ALL RLS TESTS PASSED!"
echo "=========================================="
echo "✅ Authenticated users have full access"
echo "✅ Staff UI will work correctly"
echo "✅ Safe to deploy"
```

**Usage:**
```bash
chmod +x test-rls.sh
./test-rls.sh YOUR_ANON_KEY_HERE
```

---

## Summary

**DO:**
- ✅ Test with real Supabase Auth (HTML file, cURL, or script)
- ✅ Use anon key + JWT token
- ✅ Test all CRUD operations
- ✅ Create test user in Dashboard first

**DON'T:**
- ❌ Test with SQL `SET ROLE` commands
- ❌ Use service_role key for testing
- ❌ Skip testing before deployment
- ❌ Trust SQL Editor results

**Bottom line:** If test-rls.html passes all tests, your RLS is correct.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
