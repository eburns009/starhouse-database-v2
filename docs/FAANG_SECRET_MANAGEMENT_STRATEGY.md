# FAANG-Inspired Secret Management Strategy
**Date**: 2025-11-19
**Status**: Roadmap (Current: Manual → Target: Automated)

---

## Current State (Manual PAT)

**What you're doing now**:
```bash
# Manual steps
1. Visit GitHub settings
2. Create PAT manually
3. Run: env -u GITHUB_TOKEN gh auth login
4. Paste PAT
5. Run: ./scripts/setup-github-secrets.sh
```

**FAANG Verdict**: ⚠️ Acceptable for MVP, but not scalable

---

## Tier 1: Improved Manual Process (Implement NOW)

### What FAANG Would Fix First

**Problem**: Codespace `GITHUB_TOKEN` conflicts with PAT auth

**Google/Meta Solution**: Environment variable precedence

```bash
# Add to .devcontainer/devcontainer.json
{
  "postCreateCommand": "bash .devcontainer/setup-auth.sh",
  "remoteEnv": {
    "GITHUB_TOKEN_CODESPACE": "${localEnv:GITHUB_TOKEN}",
    "GITHUB_TOKEN": ""  // Clear the auto-token
  }
}
```

**Create**: `.devcontainer/setup-auth.sh`
```bash
#!/bin/bash
# Auto-prompt for PAT on Codespace creation

if [ -z "$GH_TOKEN" ]; then
    echo "🔑 GitHub authentication required for CI/CD"
    echo "Create PAT: https://github.com/settings/tokens"
    echo "Required scopes: repo, workflow, admin:repo_hook"
    echo ""
    gh auth login
fi

# Verify scopes
if ! gh auth status 2>&1 | grep -q "repo.*workflow"; then
    echo "❌ Missing required scopes!"
    exit 1
fi

echo "✅ GitHub authentication configured"
```

**Benefit**: One-time setup per Codespace

---

## Tier 2: OIDC (No Secrets) - Recommended Target

### What Amazon/Google Do

**Implementation** (30 min setup):

1. **Enable OIDC in Supabase** (if supported)
   - Contact Supabase support for Workload Identity
   - Alternative: Use intermediate service (AWS Lambda)

2. **Update GitHub Actions**:
```yaml
# .github/workflows/deploy-supabase.yml
jobs:
  deploy:
    permissions:
      id-token: write  # OIDC token
      contents: read

    steps:
      - name: Get Supabase Token via OIDC
        id: supabase-auth
        run: |
          # GitHub provides OIDC token automatically
          GITHUB_TOKEN=$(curl -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
            "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=supabase")

          # Exchange OIDC token for Supabase token
          SUPABASE_TOKEN=$(curl -X POST https://api.supabase.io/v1/auth/oidc \
            -H "Authorization: Bearer $GITHUB_TOKEN" \
            -d '{"provider": "github"}' | jq -r '.access_token')

          echo "::add-mask::$SUPABASE_TOKEN"
          echo "token=$SUPABASE_TOKEN" >> $GITHUB_OUTPUT

      - name: Deploy
        env:
          SUPABASE_ACCESS_TOKEN: ${{ steps.supabase-auth.outputs.token }}
        run: supabase functions deploy
```

**Benefits**:
- ✅ No GitHub secrets to manage
- ✅ Tokens expire after 1 hour
- ✅ No rotation needed
- ✅ Audit trail built-in

**Drawback**: Requires Supabase OIDC support (may not exist yet)

---

## Tier 3: Secrets Manager (What Meta/Netflix Use)

### Architecture

```
GitHub Actions → AWS Secrets Manager → Supabase API
                  ↓
            Automatic rotation (Lambda)
```

### Implementation

**1. Store secrets in AWS**:
```bash
aws secretsmanager create-secret \
  --name supabase/access-token \
  --secret-string "sbp_your_token_here" \
  --description "Supabase Management API token"

aws secretsmanager create-secret \
  --name supabase/project-id \
  --secret-string "lnagadkqejnopgfxwlkb"
```

**2. Configure rotation**:
```python
# Lambda function: rotate-supabase-token
import boto3
import requests

def lambda_handler(event, context):
    # Call Supabase API to create new management token
    response = requests.post(
        'https://api.supabase.io/v1/tokens/rotate',
        headers={'Authorization': f'Bearer {old_token}'}
    )

    new_token = response.json()['access_token']

    # Update secret
    client = boto3.client('secretsmanager')
    client.put_secret_value(
        SecretId='supabase/access-token',
        SecretString=new_token
    )
```

**3. Update GitHub Actions**:
```yaml
jobs:
  deploy:
    permissions:
      id-token: write

    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActions

      - name: Fetch Supabase Secrets
        run: |
          SUPABASE_TOKEN=$(aws secretsmanager get-secret-value \
            --secret-id supabase/access-token \
            --query SecretString --output text)

          echo "::add-mask::$SUPABASE_TOKEN"
          echo "SUPABASE_ACCESS_TOKEN=$SUPABASE_TOKEN" >> $GITHUB_ENV
```

**Cost**: ~$1/month for secrets + ~$0.40/month for Lambda

---

## Tier 4: Internal API (Stripe Model)

### Architecture

```
GitHub Actions → Your API Gateway → Supabase
                      ↓
                  JWT validation
                  Rate limiting
                  Audit logging
```

**When to use**: When you have 10+ microservices with different secret needs

---

## Recommendation for Starhouse

### Phase 1: NOW (15 min)
✅ **Manual PAT with improved setup**
- Fix Codespace environment conflict
- Run: `env -u GITHUB_TOKEN gh auth login`
- Run: `./scripts/setup-github-secrets.sh`
- Set calendar reminder for 90-day rotation

### Phase 2: Next Month (2 hours)
🎯 **AWS Secrets Manager**
- Implement if you already use AWS
- Cost-effective (~$1.40/month)
- Automatic rotation
- Better security posture

### Phase 3: Future (When Supabase supports it)
🚀 **OIDC (Zero secrets)**
- Wait for Supabase to add OIDC provider support
- Check: https://github.com/supabase/supabase/discussions
- Best long-term solution

---

## What NOT to Do (Anti-patterns)

❌ **Don't**: Commit secrets to `.env` files
❌ **Don't**: Use organization-wide PATs (create bot accounts)
❌ **Don't**: Skip secret rotation (max 90 days)
❌ **Don't**: Use the Codespace `GITHUB_TOKEN` for secret management
❌ **Don't**: Share PATs across team members

---

## Decision Matrix

| Approach | Setup Time | Monthly Cost | Security | Scalability |
|----------|-----------|--------------|----------|-------------|
| Manual PAT | 15 min | $0 | ⚠️ Medium | 🔴 Low |
| Codespace Fix | 30 min | $0 | 🟡 Medium+ | 🟡 Medium |
| AWS Secrets | 2 hours | $1.40 | 🟢 High | 🟢 High |
| OIDC | N/A | $0 | ✅ Highest | ✅ Highest |

---

## FAANG Grade: Current Approach

**Manual PAT with setup script**: C+ (65/100)
- ✅ Works for small teams
- ✅ Better than no automation
- ❌ Doesn't scale
- ❌ Requires manual rotation
- ❌ Codespace conflict not handled

**With Tier 1 improvements**: B (80/100)
- ✅ One-time Codespace setup
- ✅ Validated scopes
- ✅ Clear documentation
- ⚠️ Still manual rotation

**With Tier 2 (AWS Secrets)**: A- (90/100)
- ✅ Automatic rotation
- ✅ Audit logs
- ✅ Scalable
- ⚠️ Adds infrastructure dependency

**With Tier 3 (OIDC)**: A+ (98/100)
- ✅ Zero-trust architecture
- ✅ No secret storage
- ✅ Short-lived tokens
- ✅ Industry best practice

---

## Action Plan

**Right now** (to unblock deployment):
```bash
# 1. Clear the Codespace token conflict
env -u GITHUB_TOKEN gh auth login
# Follow prompts, paste your PAT

# 2. Run setup script
./scripts/setup-github-secrets.sh

# 3. Verify
gh secret list

# 4. Test deployment
gh workflow run deploy-supabase.yml
```

**This week** (prevent future conflicts):
```bash
# Add to your Codespace config
cat << 'EOF' > .devcontainer/setup-auth.sh
#!/bin/bash
if ! gh auth status 2>&1 | grep -q "repo.*workflow"; then
    echo "Please authenticate with a PAT (not Codespace token)"
    env -u GITHUB_TOKEN gh auth login
fi
EOF

chmod +x .devcontainer/setup-auth.sh
```

**Next sprint** (production-ready):
- Evaluate AWS Secrets Manager vs OIDC
- Implement automatic rotation
- Set up monitoring/alerts

---

**Bottom Line**: Your current approach is **good enough to ship**. FAANG companies would improve it over time, not block deployment waiting for perfect infrastructure.
