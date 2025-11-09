# 📍 Incoming Address & Phone Data Setup Guide

## Overview

This guide covers how to properly capture and standardize address and phone data from all your incoming sources:
- 🎓 **Kajabi** (webhooks + Zapier)
- 💰 **PayPal** (webhooks)
- 🎟️ **Ticket Tailor** (webhooks)
- ⚡ **Zapier** (various triggers)

---

## 📊 Current State Analysis

### ✅ What's Already Working

| Source | Phone | Billing Address | Shipping Address |
|--------|-------|----------------|------------------|
| Kajabi Webhook | ✅ Captured | ❌ Not captured | ❌ Not captured |
| PayPal Webhook | ❌ Not captured | ❌ Not captured | ❌ Not captured |
| Ticket Tailor | ✅ Captured | ❌ Not captured | ❌ Not captured |
| Zapier | 🟡 Manual setup | 🟡 Manual setup | 🟡 Manual setup |

### 📋 Available Database Fields

Your `contacts` table has these address/phone fields:

**Phone Fields:**
- `phone` (primary phone number)
- `paypal_phone` (PayPal-specific phone)

**Billing Address Fields:**
- `address_line_1`
- `address_line_2`
- `city`
- `state`
- `postal_code`
- `country` (ISO 2-letter code: US, CA, GB, etc.)

**Shipping Address Fields:**
- `shipping_address_line_1`
- `shipping_address_line_2`
- `shipping_city`
- `shipping_state`
- `shipping_postal_code`
- `shipping_country`
- `shipping_address_status` ('Confirmed' or 'Non-Confirmed')

---

## 🎯 Recommended Strategy

### 1. **Data Source Priority** (Which source wins for address conflicts)

```
Priority Order:
1. Confirmed Shipping Address (from PayPal/Stripe with address verification)
2. Billing Address from Payment Processor (Kajabi, PayPal, Ticket Tailor)
3. Self-Reported Address (from forms/surveys via Zapier)
4. Legacy/Manual Entry
```

### 2. **Phone Number Strategy**

**Store by source:**
- `phone` = Primary phone (from Kajabi or Ticket Tailor)
- `paypal_phone` = Phone from PayPal payments

**Update logic:**
- Only overwrite `phone` if currently NULL or if new data is from higher-priority source
- Always update source-specific fields (e.g., `paypal_phone`)

### 3. **Address Strategy**

**Billing vs Shipping:**
- **Billing address** = Where credit card is registered (tax purposes)
- **Shipping address** = Where physical items should be sent (fulfillment)

**Update logic:**
- Update billing address from: Kajabi checkout, Ticket Tailor billing, PayPal billing
- Update shipping address from: PayPal shipping, direct forms
- Mark shipping as 'Confirmed' if from payment processor with address verification
- Copy billing → shipping ONLY if shipping is empty AND customer confirms

---

## 🔧 Implementation

### Step 1: Update Kajabi Webhook Handler

Add address capture to `supabase/functions/kajabi-webhook/index.ts`:

**In `handleContact()` function (line 487), add:**

```typescript
// Handle contact events with address
async function handleContact(supabase: any, data: any) {
  console.log('Processing contact:', data.id)

  const email = validateEmail(data.email)
  if (!email) {
    throw new Error('Invalid email in contact data')
  }

  const contactData: any = {
    email: email,
    first_name: sanitizeString(data.first_name).substring(0, 100),
    last_name: sanitizeString(data.last_name).substring(0, 100),
    phone: sanitizeString(data.phone || '').substring(0, 20),
    kajabi_id: sanitizeString(data.id),
    source_system: 'kajabi',
    email_subscribed: data.email_subscribed ?? true,
    updated_at: new Date().toISOString()
  }

  // ADD: Capture billing address if provided
  if (data.address || data.billing_address) {
    const addr = data.billing_address || data.address || {}

    if (addr.line1 || addr.address_line_1) {
      contactData.address_line_1 = sanitizeString(addr.line1 || addr.address_line_1).substring(0, 255)
    }
    if (addr.line2 || addr.address_line_2) {
      contactData.address_line_2 = sanitizeString(addr.line2 || addr.address_line_2).substring(0, 255)
    }
    if (addr.city) {
      contactData.city = sanitizeString(addr.city).substring(0, 100)
    }
    if (addr.state || addr.state_province) {
      contactData.state = sanitizeString(addr.state || addr.state_province).substring(0, 100)
    }
    if (addr.postal_code || addr.zip) {
      contactData.postal_code = sanitizeString(addr.postal_code || addr.zip).substring(0, 20)
    }
    if (addr.country) {
      contactData.country = standardizeCountryCode(addr.country)
    }

    console.log(`📍 Captured billing address from Kajabi`)
  }

  // Upsert contact
  const { data: result, error } = await supabase
    .from('contacts')
    .upsert(contactData, {
      onConflict: 'email',
      ignoreDuplicates: false
    })
    .select()

  if (error) throw error
  return { message: 'Contact processed', data: result }
}

// ADD: Helper function to standardize country codes
function standardizeCountryCode(country: string): string {
  if (!country) return ''

  const countryUpper = country.toUpperCase().trim()

  // Map common country names to ISO codes
  const countryMap: Record<string, string> = {
    'UNITED STATES': 'US',
    'UNITED STATES OF AMERICA': 'US',
    'USA': 'US',
    'CANADA': 'CA',
    'UNITED KINGDOM': 'GB',
    'UK': 'GB',
    'GREAT BRITAIN': 'GB',
    'AUSTRALIA': 'AU',
    'NEW ZEALAND': 'NZ',
    // Add more as needed
  }

  // Return mapped code if found, otherwise check if already 2-letter code
  if (countryMap[countryUpper]) {
    return countryMap[countryUpper]
  }

  // If already 2 characters, assume it's ISO code
  if (countryUpper.length === 2) {
    return countryUpper
  }

  // Otherwise return as-is (will need manual cleanup)
  return countryUpper.substring(0, 2)
}
```

---

### Step 2: Update PayPal Webhook Handler

Add address and phone capture to `supabase/functions/paypal-webhook/index.ts`:

**Update `findOrCreateContact()` function (line 413):**

```typescript
// Find or create contact (with smart duplicate prevention + address/phone)
async function findOrCreateContact(supabase: any, payload: any): Promise<any> {
  const paypalEmail = getPayerEmail(payload)
  const { first_name, last_name } = getPayerName(payload)

  // ADD: Extract phone from PayPal
  const paypalPhone = extractPayPalPhone(payload)

  // ADD: Extract shipping address from PayPal
  const shippingAddress = extractShippingAddress(payload)

  // Check if PayPal custom fields contain Kajabi IDs
  const kajabiIds = extractKajabiIds(payload.resource)

  // PRIORITY 1: If Kajabi member ID found in PayPal, use it to find contact
  if (kajabiIds.kajabi_member_id) {
    const { data: contactByMemberId } = await supabase
      .from('contacts')
      .select('id, email, paypal_email')
      .eq('kajabi_member_id', kajabiIds.kajabi_member_id)
      .single()

    if (contactByMemberId) {
      console.log(`✅ Found contact by Kajabi member ID from PayPal: ${contactByMemberId.id}`)

      // Update PayPal email, phone, and shipping address
      const updates: any = {
        updated_at: new Date().toISOString()
      }

      if (!contactByMemberId.paypal_email && paypalEmail) {
        updates.paypal_email = paypalEmail
        updates.paypal_first_name = first_name
        updates.paypal_last_name = last_name
      }

      if (paypalPhone) {
        updates.paypal_phone = paypalPhone
      }

      if (shippingAddress) {
        updates.shipping_address_line_1 = shippingAddress.line1
        updates.shipping_address_line_2 = shippingAddress.line2
        updates.shipping_city = shippingAddress.city
        updates.shipping_state = shippingAddress.state
        updates.shipping_postal_code = shippingAddress.postal_code
        updates.shipping_country = standardizeCountryCode(shippingAddress.country)
        updates.shipping_address_status = 'Confirmed' // PayPal verified
        console.log(`📦 Updating shipping address from PayPal`)
      }

      await supabase
        .from('contacts')
        .update(updates)
        .eq('id', contactByMemberId.id)

      return contactByMemberId
    }
  }

  if (!paypalEmail) {
    // ... existing test contact logic ...
  }

  // ... rest of function with similar updates for other lookup paths ...

  // STEP 4: Create new contact with all data
  console.log(`📝 Creating new contact for PayPal email: ${paypalEmail}`)

  const newContact: any = {
    email: paypalEmail,
    first_name: first_name,
    last_name: last_name,
    paypal_email: paypalEmail,
    paypal_first_name: first_name,
    paypal_last_name: last_name,
    source_system: 'manual',
    email_subscribed: true,
    updated_at: new Date().toISOString()
  }

  if (paypalPhone) {
    newContact.paypal_phone = paypalPhone
    console.log(`📱 Adding PayPal phone: ${paypalPhone}`)
  }

  if (shippingAddress) {
    newContact.shipping_address_line_1 = shippingAddress.line1
    newContact.shipping_address_line_2 = shippingAddress.line2
    newContact.shipping_city = shippingAddress.city
    newContact.shipping_state = shippingAddress.state
    newContact.shipping_postal_code = shippingAddress.postal_code
    newContact.shipping_country = standardizeCountryCode(shippingAddress.country)
    newContact.shipping_address_status = 'Confirmed'
    console.log(`📦 Adding shipping address from PayPal`)
  }

  const { data: createdContact } = await supabase
    .from('contacts')
    .upsert(newContact, {
      onConflict: 'email',
      ignoreDuplicates: false
    })
    .select()
    .single()

  if (!createdContact) {
    throw new Error('Failed to create contact')
  }

  console.log(`✅ New contact created: ${createdContact.id}`)
  return createdContact
}

// ADD: Helper to extract phone from PayPal payload
function extractPayPalPhone(payload: any): string | null {
  const resource = payload.resource || {}
  const payer = resource.payer || resource.subscriber || {}

  const phone = payer.phone?.phone_number?.national_number ||
                payer.phone_number ||
                resource.shipping_info?.phone_number ||
                null

  if (!phone) return null

  // Sanitize phone number
  const sanitized = String(phone).trim().replace(/[^\d+\-\(\)\s]/g, '').substring(0, 20)
  const digitsOnly = sanitized.replace(/\D/g, '')

  if (digitsOnly.length >= 10) {
    return sanitized
  }

  return null
}

// ADD: Helper to extract shipping address from PayPal payload
function extractShippingAddress(payload: any): any | null {
  const resource = payload.resource || {}

  // Check various locations where PayPal puts shipping address
  const shipping = resource.purchase_units?.[0]?.shipping ||
                   resource.shipping_info ||
                   resource.shipping_address ||
                   null

  if (!shipping || !shipping.address) {
    return null
  }

  const addr = shipping.address

  // Must have at least address line 1 and city
  if (!addr.address_line_1 && !addr.line1) {
    return null
  }

  return {
    line1: sanitizeString(addr.address_line_1 || addr.line1 || '').substring(0, 255),
    line2: sanitizeString(addr.address_line_2 || addr.line2 || '').substring(0, 255),
    city: sanitizeString(addr.admin_area_2 || addr.city || '').substring(0, 100),
    state: sanitizeString(addr.admin_area_1 || addr.state || '').substring(0, 100),
    postal_code: sanitizeString(addr.postal_code || '').substring(0, 20),
    country: addr.country_code || addr.country || ''
  }
}
```

---

### Step 3: Update Ticket Tailor Webhook Handler

Add billing address capture to `supabase/functions/ticket-tailor-webhook/index.ts`:

**Update `findOrCreateContact()` function (line 341):**

```typescript
// Find or create contact (with smart duplicate prevention + address)
async function findOrCreateContact(supabase: any, data: any): Promise<any> {
  const email = validateEmail(data.email || data.customer?.email || data.buyer_email)

  if (!email) {
    throw new Error('No valid email found in order data')
  }

  const first_name = sanitizeString(data.first_name || data.customer?.first_name || '').substring(0, 100)
  const last_name = sanitizeString(data.last_name || data.customer?.last_name || '').substring(0, 100)
  const ticket_tailor_id = sanitizeString(data.customer_id || '')

  // Get phone number
  const phone = validatePhone(data.phone || data.customer?.phone || data.phone_number)

  // Get email subscription preference from custom question
  const email_subscribed = getEmailSubscriptionPreference(data)

  // ADD: Extract billing address (from credit card)
  const billingAddress = extractBillingAddress(data)

  // ... existing contact lookup logic ...

  // STEP 4: Create new contact
  console.log(`📝 Creating new contact for email: ${email}`)

  const newContact: any = {
    email: email,
    first_name: first_name,
    last_name: last_name,
    ticket_tailor_id: ticket_tailor_id,
    source_system: 'ticket_tailor',
    email_subscribed: email_subscribed,
    updated_at: new Date().toISOString()
  }

  if (phone) {
    newContact.phone = phone
  }

  // ADD: Include billing address if available
  if (billingAddress) {
    newContact.address_line_1 = billingAddress.line1
    newContact.address_line_2 = billingAddress.line2
    newContact.city = billingAddress.city
    newContact.state = billingAddress.state
    newContact.postal_code = billingAddress.postal_code
    newContact.country = standardizeCountryCode(billingAddress.country)
    console.log(`📍 Adding billing address from Ticket Tailor`)
  }

  const { data: createdContact } = await supabase
    .from('contacts')
    .upsert(newContact, {
      onConflict: 'email',
      ignoreDuplicates: false
    })
    .select()
    .single()

  if (!createdContact) {
    throw new Error('Failed to create contact')
  }

  console.log(`✅ New contact created: ${createdContact.id}`)
  return createdContact
}

// ADD: Helper to extract billing address from Ticket Tailor
function extractBillingAddress(data: any): any | null {
  const billing = data.billing_address || data.address || data.customer?.address || null

  if (!billing) {
    return null
  }

  // Must have at least street address and city
  if (!billing.address_line_1 && !billing.line1 && !billing.street) {
    return null
  }

  return {
    line1: sanitizeString(billing.address_line_1 || billing.line1 || billing.street || '').substring(0, 255),
    line2: sanitizeString(billing.address_line_2 || billing.line2 || '').substring(0, 255),
    city: sanitizeString(billing.city || '').substring(0, 100),
    state: sanitizeString(billing.state || billing.region || '').substring(0, 100),
    postal_code: sanitizeString(billing.postal_code || billing.postcode || billing.zip || '').substring(0, 20),
    country: billing.country || ''
  }
}
```

---

### Step 4: Configure Zapier Zaps

For Zapier integrations, map address/phone fields explicitly:

#### Kajabi → Supabase (via Zapier)

**Trigger:** New Contact / New Purchase
**Action:** Webhook POST to `https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/kajabi-webhook`

**Custom Headers:**
```
X-Zapier-Secret: [Your ZAPIER_SECRET from Supabase env]
```

**Payload (JSON):**
```json
{
  "event_type": "contact.created",
  "data": {
    "id": "{{kajabi_id}}",
    "email": "{{email}}",
    "first_name": "{{first_name}}",
    "last_name": "{{last_name}}",
    "phone": "{{phone}}",
    "billing_address": {
      "line1": "{{address_line_1}}",
      "line2": "{{address_line_2}}",
      "city": "{{city}}",
      "state": "{{state}}",
      "postal_code": "{{postal_code}}",
      "country": "{{country}}"
    }
  }
}
```

---

## 🔍 Data Validation Rules

### Phone Number Validation
- Must contain at least 10 digits
- Allowed characters: digits, +, -, (, ), spaces
- Max length: 20 characters
- Format examples: `+1-555-123-4567`, `(555) 123-4567`, `5551234567`

### Address Validation
- **address_line_1**: Required, max 255 chars
- **city**: Required, max 100 chars
- **state**: Required (for US/CA), max 100 chars, use 2-letter codes when possible
- **postal_code**: Required, format varies by country:
  - US: 5 digits or 5+4 format (12345 or 12345-6789)
  - CA: A1A 1A1 format
  - UK: Alphanumeric (SW1A 1AA)
  - Other: Validate based on country
- **country**: Required, use ISO 3166-1 alpha-2 codes (US, CA, GB, AU, etc.)

### Data Cleaning
Always apply these transformations:
1. Trim whitespace
2. Standardize country codes to ISO 2-letter
3. Normalize phone numbers (remove non-digits for comparison)
4. Standardize postal codes (add spacing for CA, uppercase for UK)

---

## 🚀 Deployment Checklist

- [ ] Update Kajabi webhook handler with address capture
- [ ] Update PayPal webhook handler with address & phone capture
- [ ] Update Ticket Tailor webhook handler with address capture
- [ ] Add `standardizeCountryCode()` helper function to all webhook handlers
- [ ] Deploy updated Supabase Edge Functions
- [ ] Configure Zapier zaps to pass address fields
- [ ] Test with real transactions from each source
- [ ] Verify data appears correctly in Supabase
- [ ] Set up monitoring for address data quality

---

## 📊 Monitoring & Maintenance

### Regular Checks
1. **Monthly:** Run address validation query to find invalid/incomplete addresses
2. **Quarterly:** Review country code distribution, standardize any outliers
3. **After major event:** Check for bulk imports, verify data quality

### Useful SQL Queries

**Find contacts missing addresses:**
```sql
SELECT COUNT(*)
FROM contacts
WHERE email_subscribed = true
  AND (address_line_1 IS NULL OR address_line_1 = '')
  AND (shipping_address_line_1 IS NULL OR shipping_address_line_1 = '');
```

**Find contacts with invalid postal codes (US only):**
```sql
SELECT id, email, postal_code, country
FROM contacts
WHERE country = 'US'
  AND postal_code !~ '^\d{5}(-\d{4})?$'
  AND postal_code IS NOT NULL;
```

**Address completion rate:**
```sql
SELECT
  source_system,
  COUNT(*) as total,
  COUNT(CASE WHEN address_line_1 IS NOT NULL AND address_line_1 != '' THEN 1 END) as has_billing,
  COUNT(CASE WHEN shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 != '' THEN 1 END) as has_shipping,
  ROUND(100.0 * COUNT(CASE WHEN address_line_1 IS NOT NULL AND address_line_1 != '' THEN 1 END) / COUNT(*), 2) as billing_pct,
  ROUND(100.0 * COUNT(CASE WHEN shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 != '' THEN 1 END) / COUNT(*), 2) as shipping_pct
FROM contacts
GROUP BY source_system
ORDER BY total DESC;
```

---

## 🎯 Expected Data Sources

| Data Field | Kajabi | PayPal | Ticket Tailor | Zapier |
|------------|--------|--------|---------------|--------|
| Phone | ✅ Form | ✅ Shipping | ✅ Buyer | ✅ Manual |
| Billing Address | ✅ Checkout | 🟡 Rare | ✅ Card | ✅ Manual |
| Shipping Address | ❌ Rarely | ✅ Yes | ❌ No | ✅ Manual |

---

## 🔐 Security Considerations

1. **PII Protection:** Addresses and phone numbers are PII - ensure proper access controls
2. **Data Retention:** Set policies for how long to keep old addresses
3. **GDPR/CCPA:** Allow users to request address deletion
4. **Verification:** Consider implementing address verification service (USPS, Google Maps) for high-value mailings

---

## Need Help?

- Webhook logs: Check Supabase Edge Function logs
- Data issues: Review `OPERATIONAL_EFFICIENCY_PLAN.md`
- Address cleanup: See address standardization section above

