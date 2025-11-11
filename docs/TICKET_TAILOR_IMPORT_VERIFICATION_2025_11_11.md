# Ticket Tailor Import Verification
**Date**: November 11, 2025
**Task**: Verify Ticket Tailor opt-ins against Kajabi unsubscribed list

## ⚠️ CRITICAL FINDING

Out of **323 Ticket Tailor contacts** who said "Yes" to emails:
- **115 contacts (35.6%)** have PREVIOUSLY UNSUBSCRIBED in Kajabi
- **208 contacts (64.4%)** are safe to import

## Summary

We must respect the unsubscribe preferences of contacts who previously opted out. Even though these 115 contacts said "Yes" to emails via Ticket Tailor, they had previously unsubscribed in Kajabi and their unsubscribe preference should be honored.

### Files Generated

1. **IMPORT_TO_KAJABI_ticket_tailor_new_subscribers.csv** (323 contacts)
   - Original list from Ticket Tailor analysis
   - ⚠️ DO NOT USE - Contains 115 unsubscribed contacts

2. **IMPORT_TO_KAJABI_ticket_tailor_VERIFIED_CLEAN.csv** (208 contacts) ✓ USE THIS
   - Verified clean list with unsubscribed contacts removed
   - Safe to import into Kajabi
   - All contacts verified as NOT in unsubscribed list

## Verification Results

### Original Ticket Tailor Import List
- **Total contacts**: 323
- **Source**: Ticket Tailor customers who said "Yes" to emails
- **Status**: NOT already in Kajabi subscribed list (as of 10/11)

### Cross-Check Against Kajabi Unsubscribed List
- **Kajabi unsubscribed**: 2,268 emails (as of 11/10/2025)
- **Conflicts found**: 115 contacts

### Clean Verified List
- **Safe to import**: 208 contacts
- **File**: `IMPORT_TO_KAJABI_ticket_tailor_VERIFIED_CLEAN.csv`
- **Columns**: Name, Email
- **Verification**: None of these 208 appear in Kajabi unsubscribed list

## Contacts Removed (115 Previously Unsubscribed)

These contacts said "Yes" in Ticket Tailor but had previously unsubscribed in Kajabi:

```
1wideopensky@gmail.com - Leah Elaine Barber
adam@engle.com - Adam Engle
afoster@thirdbody.net - Angela Foster
anabelbeauty@gmail.com - Anabel Cuadros
andrea.belforti@gmail.com - Andrea Belforti
andreabeak@gmail.com - Andrea Lucero Vea
anean@aol.com - Anean Christensen
ansemanco@gmail.com - Anja Semanco
arnold.kovacs@gmail.com - Kovács Arnold
audrey.r.frederick@gmail.com - Audrey Frederick
aureliatara@aol.com - Aurelia aka Rev Barbara J Taylor
ayglover@gmail.com - Allie Glover
ayisha@comcast.net - Ayisha Wilhoit
barbara@soulmedicinejourney.com - Barbara M.V. Scott
bethslp123@gmail.com - beth Landry-Murphy
bevschu2@yahoo.com - BEVERLY SCHUBECK
blissmeander@gmail.com - Joanna & Andrey
blond_robert@yahoo.com - Robert Blond
brand.mckee@gmail.com - Brandon McKee
brookemagnaghi@gmail.com - Brooke Magnaghi
buy@peecloths.com - Cherie S
carlbclark@gmail.com - Carl Clark
carpenterleahs@gmail.com - Leah Carpenter
casandragon9@gmail.com - Casandra Owens
cboerder@hotmail.com - Cath Boerder
celinagarciarn@gmail.com - Celina Garcia
chicks@bresnan.net - Carole Hicks
chrismcgihon@gmail.com - Christophwr McGihon
christianepelmas@gmail.com - Christiane Pelmas
chrisvannote03@gmail.com - Chris Vannote
dalewis2121@gmail.com - Anna Lewis
dan.j.shires@gmail.com - Daniel Shires
daye2daye@gmail.com - Chris Daye
dayna.a.larson@gmail.com - Dayna A Larson
dmaccormick29@gmail.com - Daniel MacCormick
dustin.spencer.art@gmail.com - Dustin Spencer
ellanomerrill@gmail.com - Ella Merrill
erezsf@gmail.com - Erez Ascher
fanconikendra@gmail.com - Kendra Diane Fanconi
gregtemple64@gmail.com - Greg Temple & Kirsten Warner
guntherw33@gmail.com - Ellen & Gunther Weil
henriette.gregorio@gmail.com - Henriette Gregorio
info@awarenesswithyou.com - Roxanne Solomon
isabel.grieb@hin.ch - Isabel Grieb
janheartlight@msn.com - Jan de Ville
jardineart@gmail.com - Leigh Jardine
jennifer.macdon87@gmail.com - Jen MacDonald
jennymilwid@gmail.com - Jenny Milwid
jonkofler@yahoo.com - jonathan kofler
jrbauer01@gmail.com - John R. Bauer
justincanetti@gmail.com - Justin Canetti
kaleigh.hinkley@gmail.com - Kaleigh R Hinkley
katcap007@gmail.com - Kathy Rutschmann
kathenam@gmail.com - Kathena Marie Rose
katweb923@gmail.com - Katherine Webster
kimberley.lewis@gmail.com - Kim Lewis
kingstone@maxkingrealty.com - Brett Kingstone
knridings@gmail.com - Kaitlyn ridings
l.meyers726@gmail.com - Laura Meyers Britt Ripley
lamare@netvision.net.il - Muzikant Ohela & Zafrir
lindalewellyn@comcast.net - Linda Lewellyn
lisa.vonweise@mac.com - LISA VON WEISE
liveamazed@gmail.com - Sheila Ryan
livingmovement@protonmail.com - Micaela Moore
lsznip@gmail.com - Lauren Sznip
luv2dancetam@gmail.com - Tamera Snyder
lynnaea@earthlink.net - Lynnaea Lumbard
maja.jankowska30@gmail.com - Maja Jankowska
margaret@tangibleresults.com.au - Margaret Munoz
marian@revolutionaryagreements.com - Marian & Glenn Head
marthapeacock103@gmail.com - martha peacock
maura222@gmail.com - Maura Grace
mccloskey12@yahoo.com - Colleen McCloskey
merikulewis@gmail.com - Meriku lewis
mh@michellehouchens.com - michelle houchens
michemellor@gmail.com - Miche Mellor
mrs_meschke@hotmail.com - Erin Meschke
mutable1@gmail.com - Keith Fowler
nasraheck@gmail.com - Nasra Heck
nicolemkiley@gmail.com - Nicole Kiley
onychavandermeer@gmail.com - onycha vandermeer
patbarrett1@icloud.com - Patricia Barrett
paulnfoley@outlook.com - Paul Foley
pcadair@sover.net - Caitlin Adair
perky@awarenessgeneration.com - Kristen Ujazdowski
pmettmoss@gmail.com - Patricia Mettler-Moss
randall.lafleur@gmail.com - Randall LaFleur
rebeccaowillems@yahoo.com - Rebecca Worthington
reginagelfo@gmail.com - Regina Gelfo
retfrog23@yahoo.com - Linda Molyneux
roush.mike@gmail.com - Michael Roush
russellcanseco@gmail.com - Russell Diez Canseco
sabrina.desnoyers.1@gmail.com - Sabrina Desnoyers
sagewaye@gmail.com - Sage Hamilton/Christopher Sassano
samiadler7@gmail.com - Sami adler
sdevine99@gmail.com - Sue Devine
sdmckay09@gmail.com - Sarah McKay
sephalily@gmail.com - Lily Sepha Blodgett
seth.e.pearson@gmail.com - Seth Pearson
sherri.begleiter@gmail.com - Sherri begleiter
silkyoak7@optusnet.com.au - Beth McCarthy
soniabrooks@yahoo.com - sonia brooks
stevedonnellyemail@gmail.com - Stephen Donnelly
susanbrasher@reality.org - Susan Wu
suse.wozniak@gmail.com - Susan Wozniak
tal.liza616@gmail.com - Taliza Mizrahi
tanya@tjoptics.com - Tanya Jewell
tcannon@sandwich.net - Taffy Cannon
thismunashaheen@gmail.com - Muna Shaheen
thombanjo@yahoo.com - Josh Schlossberg
tk@tesskennedy.com - Tess Kennedy
tnnoel17@gmail.com - Tara Noel
todd@schaffner.live - Todd Schaffner
victorien.mulliez@gmail.com - Victorien Mulliez
zukidreams@pm.me - Tony Howard
```

## Recommendation

**USE ONLY THE VERIFIED CLEAN FILE FOR IMPORT**

File to import: `kajabi 3 files review/IMPORT_TO_KAJABI_ticket_tailor_VERIFIED_CLEAN.csv`

This file contains:
- **208 verified contacts**
- **Name and Email columns only**
- **None have previously unsubscribed**
- **Safe to import into Kajabi**

## Legal & Compliance Note

It is critical to respect unsubscribe preferences for:
- **CAN-SPAM Act compliance** (US law)
- **GDPR compliance** (if applicable)
- **Customer trust and reputation**
- **Email deliverability** (ISPs monitor complaint rates)

Even though these 115 contacts checked "Yes" to receive emails at a Ticket Tailor event, they had previously unsubscribed from Kajabi. Their most recent preference (unsubscribe) should be honored unless they explicitly re-subscribe through Kajabi's own opt-in process.

## Next Steps

1. ✓ Use **IMPORT_TO_KAJABI_ticket_tailor_VERIFIED_CLEAN.csv** for import
2. Import 208 new subscribers into Kajabi
3. Consider adding a note in your process to check unsubscribe status before importing from external sources

## Files Location

All files in: `/workspaces/starhouse-database-v2/kajabi 3 files review/`

- `IMPORT_TO_KAJABI_ticket_tailor_VERIFIED_CLEAN.csv` ✓ **USE THIS**
- `IMPORT_TO_KAJABI_ticket_tailor_new_subscribers.csv` (original - do not use)

## Verification Script

Analysis performed by: `scripts/verify_import_against_unsubscribed.py`
