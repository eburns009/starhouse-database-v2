# Kajabi Address Fix Guide - 3 Critical Contacts

## Overview
You have 3 contacts in Kajabi with incorrectly structured addresses that need manual correction.

---

## 1. Ed Burns (eburns009@gmail.com) ✅ EASIEST

**Current Kajabi Data (INCORRECT):**
```
Billing Address Line 1: 1144 Rozel Ave
Billing Address Line 2: 3472 Sunshine Canyon Rd  ← WRONG! Different address
City: Southampton
State: PA
Zip: 18966
```

**What This Should Be:**
```
Billing Address Line 1: 1144 Rozel Ave
Billing Address Line 2: [BLANK]
City: Southampton
State: PA
Zip: 18966
```

**Action Steps:**
1. Log into Kajabi: https://app.kajabi.com
2. Go to People → Search for "eburns009@gmail.com"
3. Click on Ed Burns' profile
4. Click "Edit" on billing address
5. **Clear the "Address Line 2" field** (remove "3472 Sunshine Canyon Rd")
6. Keep Line 1 as "1144 Rozel Ave"
7. Keep City/State/Zip as Southampton, PA 18966
8. Save

**Note:** The Boulder address (3472 Sunshine Canyon Rd) is already correctly stored in shipping address.

---

## 2. Tataya Bailey (tataya@prismaleadership.com) ⚠️ NEEDS RESEARCH

**Current Kajabi Data (INCORRECT):**
```
Billing Address Line 1: 425 Fairway View Dr
Billing Address Line 2: 1023 Walnut Street, Ste 100 Galvanize  ← Different address!
City: Prescott
State: AZ
Zip: 86303
```

**Issue:** Two completely different addresses. Need to determine which is current/correct.

**Action Steps:**
1. Log into Kajabi → People → Search "tataya@prismaleadership.com"
2. Check her recent order history - which address was used for recent purchases?
3. Check if she has a shipping address on file
4. **Contact Tataya if unclear** - ask which address is current
5. Once determined:
   - Keep the current address in Line 1
   - **Clear Line 2**
   - Update City/State/Zip to match the current address

**Likely Scenario:** 
- "1023 Walnut Street" looks like a business address (Galvanize is a coworking space in Boulder)
- "425 Fairway View Dr" in Prescott might be home address
- **Recommendation:** Use most recent billing/shipping address from her latest transaction

---

## 3. Laura Blanco (blancogutierrezlaura@gmail.com) 🇪🇸 SPAIN

**Current Kajabi Data (UNCLEAR):**
```
Billing Address Line 1: Avenida de los Frutales 14
Billing Address Line 2: 119 Aldea de la Luna  ← Different street address
City: Estepona
State: MA
Zip: 29680
Country: Spain
```

**Issue:** Two different street addresses in the same Spanish city.

**Action Steps:**
1. Log into Kajabi → People → Search "blancogutierrezlaura@gmail.com"
2. Check her recent purchase history - which address was used?
3. Check if "Aldea de la Luna" is actually part of the same building/complex as "Avenida de los Frutales 14"
   - In Spain, sometimes multiple street names refer to the same location
4. **If they're different addresses:**
   - Keep the most recent one in Line 1
   - **Clear Line 2**
5. **If Line 2 is part of the same address:**
   - Leave as is (no fix needed)

**Note:** Spanish addresses can be complex with urbanizations/complexes. Verify before changing.

---

## After Kajabi Fixes - Database Cleanup (Optional)

Once you've fixed the 3 profiles in Kajabi, you can optionally clean up the duplicate addresses in your database:

```sql
-- Fix Ed Burns (after Kajabi fix)
UPDATE contacts 
SET address_line_2 = NULL 
WHERE email = 'eburns009@gmail.com';

-- Fix Tataya Bailey (after determining correct address in Kajabi)
UPDATE contacts 
SET address_line_2 = NULL 
WHERE email = 'tataya@prismaleadership.com';

-- Fix Laura Blanco (after confirming in Kajabi)
-- Only run if Line 2 was confirmed as incorrect
UPDATE contacts 
SET address_line_2 = NULL 
WHERE email = 'blancogutierrezlaura@gmail.com';
```

---

## Why This Happened

**Root Cause:** Kajabi's address form allows users to enter:
- Line 1: [First complete address]
- Line 2: [Second complete address]

But the system assumes Line 1 + Line 2 share the same city/state/zip, which is only true if Line 2 is an apartment/suite number.

**Solution:** Always ensure Line 2 is only used for unit/apt/suite numbers, never for completely different addresses.

---

## Summary

| Contact | Status | Priority | Action |
|---------|--------|----------|--------|
| Ed Burns | Clear fix needed | HIGH | Remove Line 2 from billing address |
| Tataya Bailey | Research needed | HIGH | Determine current address, remove Line 2 |
| Laura Blanco | Verify needed | MEDIUM | Check if addresses are same location |

