# Phone-a-Thon Pledge Workflow - Complete Process

**Version:** 1.0
**Created:** 2025-11-15
**Purpose:** Document complete pledge-to-payment workflow with acknowledgments

---

## Overview

When a donor makes a pledge during a phone call, we need to:

1. **Capture the pledge** in the system
2. **Send payment instructions** immediately (email OR mail)
3. **Send donation acknowledgment** letter
4. **Track pledge fulfillment**
5. **Convert to donation** when payment received

---

## Enhanced Data Model

### Updated `call_logs` Table

```sql
ALTER TABLE call_logs ADD COLUMN acknowledgment_sent BOOLEAN DEFAULT false;
ALTER TABLE call_logs ADD COLUMN acknowledgment_sent_date TIMESTAMPTZ;
ALTER TABLE call_logs ADD COLUMN acknowledgment_method TEXT; -- 'email', 'mail'
ALTER TABLE call_logs ADD COLUMN payment_instructions_sent BOOLEAN DEFAULT false;
ALTER TABLE call_logs ADD COLUMN payment_instructions_method TEXT; -- 'email', 'mail'

-- Constraint
ALTER TABLE call_logs ADD CONSTRAINT valid_acknowledgment_method
    CHECK (acknowledgment_method IN ('email', 'mail', NULL));
```

### Pledge Status Tracking

```sql
-- Already in call_logs table:
pledge_status TEXT DEFAULT 'pending'
-- Values: 'pending', 'paid', 'cancelled'

-- Add more detail:
ALTER TABLE call_logs ADD COLUMN pledge_sent_to_donor_date TIMESTAMPTZ;
ALTER TABLE call_logs ADD COLUMN pledge_payment_due_date DATE; -- 30 days from call
ALTER TABLE call_logs ADD COLUMN pledge_reminder_sent_count INTEGER DEFAULT 0;
ALTER TABLE call_logs ADD COLUMN pledge_last_reminder_date TIMESTAMPTZ;
```

---

## Caller Interface Updates

### When Pledge is Captured

**Updated Call Action Panel:**

```
┌─────────────────────────────────────────────────────┐
│ PLEDGE CAPTURED ✓                                   │
├─────────────────────────────────────────────────────┤
│ Amount: $300                                        │
│ Method: Check                                       │
├─────────────────────────────────────────────────────┤
│ SEND PAYMENT INSTRUCTIONS                           │
│                                                     │
│ How should we send payment instructions?            │
│                                                     │
│ ○ Email (instant) - Recommended                    │
│   jeff@example.com                                  │
│                                                     │
│ ○ Mail (3-5 days)                                   │
│   Jeff Stein                                        │
│   123 Main St                                       │
│   Portland, OR 97201                                │
│                                                     │
│ ☑ Also send donation acknowledgment letter         │
│                                                     │
├─────────────────────────────────────────────────────┤
│ [Preview Email] [Send & Next Contact →]            │
└─────────────────────────────────────────────────────┘
```

**Logic:**

```typescript
interface PledgeConfirmation {
  callLogId: string
  donorName: string
  donorEmail: string | null
  donorAddress: Address | null
  pledgeAmount: number
  paymentMethod: 'check' | 'credit_card' | 'online' | 'cash'
  deliveryMethod: 'email' | 'mail'
  sendAcknowledgment: boolean
}

async function handlePledgeConfirmation(pledge: PledgeConfirmation) {
  // 1. Determine delivery method
  const deliveryMethod = pledge.deliveryMethod ||
    (pledge.donorEmail ? 'email' : 'mail')

  // 2. Send payment instructions
  if (deliveryMethod === 'email') {
    await sendPaymentInstructionsEmail(pledge)
  } else {
    await generatePaymentInstructionsLetter(pledge)
  }

  // 3. Send acknowledgment (if requested)
  if (pledge.sendAcknowledgment) {
    if (deliveryMethod === 'email') {
      await sendAcknowledgmentEmail(pledge)
    } else {
      await generateAcknowledgmentLetter(pledge)
    }
  }

  // 4. Update call log
  await supabase.from('call_logs').update({
    payment_instructions_sent: true,
    payment_instructions_method: deliveryMethod,
    acknowledgment_sent: pledge.sendAcknowledgment,
    acknowledgment_method: deliveryMethod,
    pledge_sent_to_donor_date: new Date(),
    pledge_payment_due_date: addDays(new Date(), 30)
  }).eq('id', pledge.callLogId)

  // 5. Show success toast
  toast.success(
    deliveryMethod === 'email'
      ? 'Payment instructions emailed to donor'
      : 'Letter queued for mailing'
  )
}
```

---

## Email Templates

### 1. Payment Instructions by Method

**Check Payment:**

```typescript
// emails/pledge-payment-check.tsx
import { Email, Heading, Text, Section, Button } from '@react-email/components'

export function PledgePaymentCheckEmail({
  donorName,
  pledgeAmount,
  callDate,
  callerName,
  campaignName
}: PledgeEmailProps) {
  return (
    <Email>
      <Heading>Thank you for your pledge!</Heading>

      <Text>Dear {donorName},</Text>

      <Text>
        Thank you so much for your generous pledge of <strong>{formatCurrency(pledgeAmount)}</strong>
        during our call on {formatDate(callDate)}!
      </Text>

      <Text>
        Your support of our {campaignName} will make a real difference in our community.
      </Text>

      <Section style={{ background: '#f5f5f5', padding: '20px', margin: '20px 0' }}>
        <Heading as="h3">How to Send Your Check:</Heading>

        <Text style={{ margin: '10px 0' }}>
          <strong>1. Make check payable to:</strong><br/>
          All Seasons Chalice Church
        </Text>

        <Text style={{ margin: '10px 0' }}>
          <strong>2. Write in memo line:</strong><br/>
          {campaignName} - Phone Pledge
        </Text>

        <Text style={{ margin: '10px 0' }}>
          <strong>3. Mail to:</strong><br/>
          All Seasons Chalice Church<br/>
          Attn: Development<br/>
          123 Church Street<br/>
          Portland, OR 97201
        </Text>

        <Text style={{ margin: '10px 0' }}>
          <strong>Amount:</strong> {formatCurrency(pledgeAmount)}
        </Text>
      </Section>

      <Text>
        Your tax-deductible receipt will be mailed to you once we receive your donation.
      </Text>

      <Text>
        Questions? Reply to this email or call us at (555) 123-4567.
      </Text>

      <Text>
        With gratitude,<br/>
        {callerName}<br/>
        All Seasons Chalice Church
      </Text>

      <Section style={{ borderTop: '1px solid #ccc', marginTop: '40px', paddingTop: '20px' }}>
        <Text style={{ fontSize: '12px', color: '#666' }}>
          Pledge Date: {formatDate(callDate)}<br/>
          Pledge Amount: {formatCurrency(pledgeAmount)}<br/>
          Payment Method: Check<br/>
          Tax ID: XX-XXXXXXX (501(c)(3) tax-exempt organization)
        </Text>
      </Section>
    </Email>
  )
}
```

**Credit Card Payment:**

```typescript
// emails/pledge-payment-credit-card.tsx
export function PledgePaymentCreditCardEmail({
  donorName,
  pledgeAmount,
  callDate,
  callerName,
  campaignName,
  onlinePaymentLink
}: PledgeEmailProps) {
  return (
    <Email>
      <Heading>Thank you for your pledge!</Heading>

      <Text>Dear {donorName},</Text>

      <Text>
        Thank you for your pledge of <strong>{formatCurrency(pledgeAmount)}</strong>!
      </Text>

      <Section style={{ background: '#f5f5f5', padding: '20px', margin: '20px 0' }}>
        <Heading as="h3">Pay Online with Credit Card:</Heading>

        <Text>
          Click the button below to securely complete your donation:
        </Text>

        <Button
          href={onlinePaymentLink}
          style={{
            background: '#007bff',
            color: '#fff',
            padding: '12px 24px',
            borderRadius: '4px',
            textDecoration: 'none',
            display: 'inline-block',
            margin: '20px 0'
          }}
        >
          Donate {formatCurrency(pledgeAmount)} Now
        </Button>

        <Text style={{ fontSize: '14px', color: '#666' }}>
          Or copy this link: {onlinePaymentLink}
        </Text>
      </Section>

      <Text>
        <strong>Alternative: Pay by Phone</strong><br/>
        Call us at (555) 123-4567 and we can process your card over the phone.
      </Text>

      <Text>
        Your tax-deductible receipt will be emailed immediately after payment.
      </Text>

      <Text>
        With gratitude,<br/>
        {callerName}<br/>
        All Seasons Chalice Church
      </Text>

      <Section style={{ borderTop: '1px solid #ccc', marginTop: '40px', paddingTop: '20px' }}>
        <Text style={{ fontSize: '12px', color: '#666' }}>
          Pledge Date: {formatDate(callDate)}<br/>
          Pledge Amount: {formatCurrency(pledgeAmount)}<br/>
          Payment Method: Credit Card<br/>
          Tax ID: XX-XXXXXXX
        </Text>
      </Section>
    </Email>
  )
}
```

**Online Payment:**

```typescript
// emails/pledge-payment-online.tsx
export function PledgePaymentOnlineEmail({
  donorName,
  pledgeAmount,
  callDate,
  callerName,
  campaignName,
  donationPageLink
}: PledgeEmailProps) {
  return (
    <Email>
      <Heading>Thank you for your pledge!</Heading>

      <Text>Dear {donorName},</Text>

      <Text>
        Thank you for your pledge of <strong>{formatCurrency(pledgeAmount)}</strong>!
      </Text>

      <Section style={{ background: '#f5f5f5', padding: '20px', margin: '20px 0' }}>
        <Heading as="h3">Complete Your Donation Online:</Heading>

        <Button
          href={donationPageLink}
          style={{
            background: '#28a745',
            color: '#fff',
            padding: '16px 32px',
            borderRadius: '4px',
            textDecoration: 'none',
            display: 'inline-block',
            margin: '20px 0',
            fontSize: '18px'
          }}
        >
          Donate {formatCurrency(pledgeAmount)}
        </Button>

        <Text>
          Our secure online donation form accepts:
        </Text>
        <ul>
          <li>Credit/Debit Cards</li>
          <li>PayPal</li>
          <li>Bank Transfer (ACH)</li>
        </ul>
      </Section>

      <Text>
        Your tax receipt will be emailed immediately after your donation is processed.
      </Text>

      <Text>
        Questions? Reply to this email or call (555) 123-4567.
      </Text>

      <Text>
        With gratitude,<br/>
        {callerName}<br/>
        All Seasons Chalice Church
      </Text>
    </Email>
  )
}
```

### 2. Donation Acknowledgment Email

```typescript
// emails/pledge-acknowledgment.tsx
export function PledgeAcknowledgmentEmail({
  donorName,
  pledgeAmount,
  callDate,
  callerName,
  campaignName,
  donorHistory
}: AcknowledgmentEmailProps) {
  return (
    <Email>
      <Heading>Your generosity makes a difference!</Heading>

      <Text>Dear {donorName},</Text>

      <Text>
        On behalf of everyone at All Seasons Chalice Church, I want to express
        our heartfelt gratitude for your pledge of <strong>{formatCurrency(pledgeAmount)}</strong>
        to support our {campaignName}.
      </Text>

      <Text>
        {donorHistory.isRecurring && (
          <>
            As a loyal supporter who has given {donorHistory.donationCount} times over
            the years, your continued commitment means the world to us.
          </>
        )}
        {!donorHistory.isRecurring && donorHistory.donationCount > 1 && (
          <>
            Thank you for being a valued supporter! This is your {ordinal(donorHistory.donationCount)}
            gift to our organization.
          </>
        )}
        {donorHistory.donationCount === 1 && (
          <>
            We're so grateful to welcome you as a new supporter of our mission!
          </>
        )}
      </Text>

      <Section style={{ background: '#f0f8ff', padding: '20px', margin: '20px 0', borderLeft: '4px solid #007bff' }}>
        <Heading as="h3" style={{ marginTop: 0 }}>Your Impact:</Heading>

        <Text>
          Your {formatCurrency(pledgeAmount)} gift will help us:
        </Text>
        <ul>
          <li>Support [specific program/service]</li>
          <li>Serve [number] community members</li>
          <li>Advance [mission goal]</li>
        </ul>
      </Section>

      <Text>
        We've sent separate payment instructions via email. If you have any questions
        or need assistance, please don't hesitate to reach out.
      </Text>

      <Text>
        Thank you again for your commitment to our community and mission.
      </Text>

      <Text>
        With deep appreciation,<br/>
        <br/>
        {callerName}<br/>
        Development Team<br/>
        All Seasons Chalice Church
      </Text>

      <Section style={{ borderTop: '1px solid #ccc', marginTop: '40px', paddingTop: '20px' }}>
        <Text style={{ fontSize: '12px', color: '#666' }}>
          <strong>Your Giving History:</strong><br/>
          Total Donated: {formatCurrency(donorHistory.totalDonated)}<br/>
          Number of Gifts: {donorHistory.donationCount}<br/>
          Supporter Since: {formatYear(donorHistory.firstDonationDate)}<br/>
          <br/>
          All Seasons Chalice Church is a 501(c)(3) tax-exempt organization.<br/>
          Tax ID: XX-XXXXXXX
        </Text>
      </Section>
    </Email>
  )
}
```

---

## Snail Mail Letters

### 1. Payment Instructions Letter (PDF)

```typescript
// lib/pdf/pledge-payment-letter.ts
import { jsPDF } from 'jspdf'

export function generatePaymentInstructionsLetter(pledge: PledgeData): Blob {
  const doc = new jsPDF()

  // Letterhead
  doc.setFontSize(16)
  doc.text('All Seasons Chalice Church', 105, 20, { align: 'center' })
  doc.setFontSize(10)
  doc.text('123 Church Street, Portland, OR 97201', 105, 28, { align: 'center' })
  doc.text('(555) 123-4567 | info@allseasonschurch.org', 105, 34, { align: 'center' })

  // Date
  doc.setFontSize(11)
  doc.text(formatDate(new Date()), 20, 50)

  // Donor address
  doc.text(pledge.donorName, 20, 65)
  if (pledge.donorAddress) {
    doc.text(pledge.donorAddress.line1, 20, 72)
    if (pledge.donorAddress.line2) {
      doc.text(pledge.donorAddress.line2, 20, 79)
      doc.text(`${pledge.donorAddress.city}, ${pledge.donorAddress.state} ${pledge.donorAddress.zip}`, 20, 86)
    } else {
      doc.text(`${pledge.donorAddress.city}, ${pledge.donorAddress.state} ${pledge.donorAddress.zip}`, 20, 79)
    }
  }

  // Greeting
  doc.text(`Dear ${pledge.donorName},`, 20, 105)

  // Body
  const bodyText = `Thank you for your generous pledge of ${formatCurrency(pledge.pledgeAmount)} to support our ${pledge.campaignName}! Your commitment to our mission means the world to us.`

  const wrappedBody = doc.splitTextToSize(bodyText, 170)
  doc.text(wrappedBody, 20, 115)

  // Payment Instructions Box
  doc.setDrawColor(0, 123, 255)
  doc.setLineWidth(0.5)
  doc.rect(20, 135, 170, 60)

  doc.setFontSize(12)
  doc.setFont(undefined, 'bold')
  doc.text('How to Send Your Donation:', 25, 145)
  doc.setFont(undefined, 'normal')
  doc.setFontSize(11)

  if (pledge.paymentMethod === 'check') {
    doc.text('1. Make check payable to: All Seasons Chalice Church', 25, 155)
    doc.text(`2. Write in memo line: ${pledge.campaignName} - Phone Pledge`, 25, 162)
    doc.text('3. Mail to: All Seasons Chalice Church', 25, 169)
    doc.text('           Attn: Development', 25, 176)
    doc.text('           123 Church Street', 25, 183)
    doc.text('           Portland, OR 97201', 25, 190)
  } else {
    doc.text('Visit our website to donate online:', 25, 155)
    doc.setTextColor(0, 123, 255)
    doc.text('www.allseasonschurch.org/donate', 25, 162)
    doc.setTextColor(0, 0, 0)
    doc.text('Or call us at (555) 123-4567 to donate by phone.', 25, 175)
  }

  // Additional text
  doc.setFontSize(11)
  const closingText = 'Your tax-deductible receipt will be mailed to you once we receive your donation. If you have any questions, please don\'t hesitate to contact us.'
  const wrappedClosing = doc.splitTextToSize(closingText, 170)
  doc.text(wrappedClosing, 20, 210)

  // Signature
  doc.text('With gratitude,', 20, 235)
  doc.text(pledge.callerName, 20, 250)
  doc.text('Development Team', 20, 257)

  // Footer
  doc.setFontSize(9)
  doc.setTextColor(100, 100, 100)
  doc.text('All Seasons Chalice Church is a 501(c)(3) tax-exempt organization. Tax ID: XX-XXXXXXX', 105, 280, { align: 'center' })

  return doc.output('blob')
}
```

### 2. Acknowledgment Letter (PDF)

```typescript
// lib/pdf/pledge-acknowledgment-letter.ts
export function generateAcknowledgmentLetter(pledge: PledgeData): Blob {
  const doc = new jsPDF()

  // Letterhead (same as above)
  doc.setFontSize(16)
  doc.text('All Seasons Chalice Church', 105, 20, { align: 'center' })
  doc.setFontSize(10)
  doc.text('123 Church Street, Portland, OR 97201', 105, 28, { align: 'center' })

  // Date
  doc.setFontSize(11)
  doc.text(formatDate(new Date()), 20, 50)

  // Donor address
  doc.text(pledge.donorName, 20, 65)
  // ... (address block same as above)

  // Greeting
  doc.text(`Dear ${pledge.donorName},`, 20, 105)

  // Acknowledgment message
  const acknowledgment = `On behalf of everyone at All Seasons Chalice Church, I want to express our heartfelt gratitude for your pledge of ${formatCurrency(pledge.pledgeAmount)} to support our ${pledge.campaignName}.`

  const wrappedAck = doc.splitTextToSize(acknowledgment, 170)
  doc.text(wrappedAck, 20, 115)

  // Impact section
  doc.setFont(undefined, 'bold')
  doc.text('Your Impact:', 20, 140)
  doc.setFont(undefined, 'normal')

  const impactText = `Your generous gift will help us [specific impact: serve X families, support Y programs, advance Z mission]. Because of supporters like you, we can continue to make a difference in our community.`
  const wrappedImpact = doc.splitTextToSize(impactText, 170)
  doc.text(wrappedImpact, 20, 148)

  // Donor history (if applicable)
  if (pledge.donorHistory.donationCount > 1) {
    const historyText = `As a valued supporter who has given ${pledge.donorHistory.donationCount} times since ${formatYear(pledge.donorHistory.firstDonationDate)}, your continued commitment means the world to us. Together, you have contributed ${formatCurrency(pledge.donorHistory.totalDonated)} to our mission.`
    const wrappedHistory = doc.splitTextToSize(historyText, 170)
    doc.text(wrappedHistory, 20, 175)
  }

  // Payment reminder
  doc.setFontSize(10)
  doc.setTextColor(100, 100, 100)
  const reminderText = 'Separate payment instructions have been sent via mail. If you have any questions or need assistance, please contact us at (555) 123-4567.'
  const wrappedReminder = doc.splitTextToSize(reminderText, 170)
  doc.text(wrappedReminder, 20, 205)

  // Closing
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(11)
  doc.text('Thank you again for your commitment to our community and mission.', 20, 225)
  doc.text('With deep appreciation,', 20, 240)
  doc.text(pledge.callerName, 20, 255)
  doc.text('Development Team', 20, 262)

  // Footer
  doc.setFontSize(9)
  doc.setTextColor(100, 100, 100)
  doc.text('All Seasons Chalice Church is a 501(c)(3) tax-exempt organization. Tax ID: XX-XXXXXXX', 105, 280, { align: 'center' })

  return doc.output('blob')
}
```

---

## Updated Workflow

### When Pledge is Made (During Call)

```typescript
// In caller interface, after clicking outcome button
async function handlePledgeMade({
  callLogId,
  contactId,
  pledgeAmount,
  paymentMethod,
  notes
}: PledgeInput) {

  // 1. Save call log with pledge
  const { data: callLog } = await supabase
    .from('call_logs')
    .update({
      pledge_amount: pledgeAmount,
      pledge_payment_method: paymentMethod,
      notes: notes,
      pledge_status: 'pending'
    })
    .eq('id', callLogId)
    .select()
    .single()

  // 2. Show pledge confirmation modal
  showPledgeConfirmationModal({
    callLog,
    contact: currentContact
  })
}
```

### Pledge Confirmation Modal

```tsx
function PledgeConfirmationModal({ callLog, contact }: Props) {
  const [deliveryMethod, setDeliveryMethod] = useState<'email' | 'mail'>(
    contact.email ? 'email' : 'mail'
  )
  const [sendAcknowledgment, setSendAcknowledgment] = useState(true)

  async function handleSend() {
    // Send payment instructions
    if (deliveryMethod === 'email') {
      await sendPaymentInstructionsEmail({
        donorName: formatName(contact.first_name, contact.last_name),
        donorEmail: contact.email!,
        pledgeAmount: callLog.pledge_amount,
        paymentMethod: callLog.pledge_payment_method,
        campaignName: callLog.call_campaign.name,
        callerName: callLog.caller_name,
        callDate: callLog.call_date
      })

      // Send acknowledgment email (separate)
      if (sendAcknowledgment) {
        await sendAcknowledgmentEmail({
          donorName: formatName(contact.first_name, contact.last_name),
          donorEmail: contact.email!,
          pledgeAmount: callLog.pledge_amount,
          campaignName: callLog.call_campaign.name,
          callerName: callLog.caller_name,
          callDate: callLog.call_date,
          donorHistory: {
            totalDonated: contact.total_donated,
            donationCount: contact.donation_count,
            firstDonationDate: contact.first_donation_date,
            isRecurring: contact.is_recurring_donor
          }
        })
      }
    } else {
      // Generate PDFs for mailing
      const paymentPDF = generatePaymentInstructionsLetter({
        donorName: formatName(contact.first_name, contact.last_name),
        donorAddress: {
          line1: contact.address_line_1,
          line2: contact.address_line_2,
          city: contact.city,
          state: contact.state,
          zip: contact.postal_code
        },
        pledgeAmount: callLog.pledge_amount,
        paymentMethod: callLog.pledge_payment_method,
        campaignName: callLog.call_campaign.name,
        callerName: callLog.caller_name
      })

      // Upload to storage for printing
      await supabase.storage
        .from('pledge-letters')
        .upload(`payment-instructions/${callLog.id}.pdf`, paymentPDF)

      if (sendAcknowledgment) {
        const ackPDF = generateAcknowledgmentLetter({
          donorName: formatName(contact.first_name, contact.last_name),
          donorAddress: {
            line1: contact.address_line_1,
            line2: contact.address_line_2,
            city: contact.city,
            state: contact.state,
            zip: contact.postal_code
          },
          pledgeAmount: callLog.pledge_amount,
          campaignName: callLog.call_campaign.name,
          callerName: callLog.caller_name,
          donorHistory: {
            totalDonated: contact.total_donated,
            donationCount: contact.donation_count,
            firstDonationDate: contact.first_donation_date
          }
        })

        await supabase.storage
          .from('pledge-letters')
          .upload(`acknowledgment/${callLog.id}.pdf`, ackPDF)
      }
    }

    // Update call log
    await supabase.from('call_logs').update({
      payment_instructions_sent: true,
      payment_instructions_method: deliveryMethod,
      acknowledgment_sent: sendAcknowledgment,
      acknowledgment_method: deliveryMethod,
      pledge_sent_to_donor_date: new Date(),
      pledge_payment_due_date: addDays(new Date(), 30)
    }).eq('id', callLog.id)

    toast.success(
      deliveryMethod === 'email'
        ? 'Emails sent to donor!'
        : 'Letters queued for printing and mailing'
    )

    closeModal()
    loadNextContact()
  }

  return (
    <Dialog open onOpenChange={closeModal}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Send Payment Instructions & Acknowledgment</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Pledge Summary */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Pledge Amount</p>
                  <p className="text-2xl font-bold">{formatCurrency(callLog.pledge_amount)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Payment Method</p>
                  <p className="font-medium capitalize">{callLog.pledge_payment_method}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Delivery Method */}
          <div className="space-y-3">
            <Label>How should we send instructions?</Label>

            <RadioGroup value={deliveryMethod} onValueChange={setDeliveryMethod}>
              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                <RadioGroupItem value="email" id="email" disabled={!contact.email} />
                <Label htmlFor="email" className="flex-1">
                  <div className="font-medium">Email (Instant)</div>
                  <div className="text-sm text-muted-foreground">
                    {contact.email || 'No email address on file'}
                  </div>
                </Label>
                {deliveryMethod === 'email' && <Badge>Recommended</Badge>}
              </div>

              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                <RadioGroupItem value="mail" id="mail" disabled={!contact.address_line_1} />
                <Label htmlFor="mail" className="flex-1">
                  <div className="font-medium">Postal Mail (3-5 days)</div>
                  <div className="text-sm text-muted-foreground">
                    {contact.address_line_1
                      ? `${contact.address_line_1}, ${contact.city}, ${contact.state}`
                      : 'No mailing address on file'
                    }
                  </div>
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Acknowledgment Option */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="acknowledgment"
              checked={sendAcknowledgment}
              onCheckedChange={setSendAcknowledgment}
            />
            <Label htmlFor="acknowledgment" className="font-normal">
              Also send donation acknowledgment letter (recommended)
            </Label>
          </div>

          {/* Preview Buttons */}
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => previewEmail('payment')}>
              Preview Payment Email
            </Button>
            {sendAcknowledgment && (
              <Button variant="outline" onClick={() => previewEmail('acknowledgment')}>
                Preview Acknowledgment
              </Button>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={closeModal}>
            Skip for Now
          </Button>
          <Button onClick={handleSend}>
            {deliveryMethod === 'email' ? 'Send Emails' : 'Queue for Mailing'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

---

## Follow-Up Workflow

### Automated Reminders (For Unpaid Pledges)

```typescript
// Scheduled job: Runs daily
async function sendPledgeReminders() {
  // Get pledges pending for 7+ days
  const { data: overdueP pledges } = await supabase
    .from('call_logs')
    .select(`
      *,
      contacts (*),
      call_campaigns (name)
    `)
    .eq('pledge_status', 'pending')
    .not('pledge_amount', 'is', null)
    .lte('pledge_sent_to_donor_date', subDays(new Date(), 7))
    .lt('pledge_reminder_sent_count', 3) // Max 3 reminders

  for (const pledge of overduePledges) {
    // Determine reminder level
    const daysSincePledge = daysBetween(pledge.pledge_sent_to_donor_date, new Date())
    const reminderLevel =
      daysSincePledge >= 21 ? 'final' :
      daysSincePledge >= 14 ? 'second' :
      'first'

    // Send reminder email
    await sendReminderEmail({
      donor: pledge.contacts,
      pledge,
      reminderLevel
    })

    // Update reminder count
    await supabase.from('call_logs').update({
      pledge_reminder_sent_count: pledge.pledge_reminder_sent_count + 1,
      pledge_last_reminder_date: new Date()
    }).eq('id', pledge.id)
  }
}

// Reminder email template
function ReminderEmail({ donorName, pledgeAmount, daysSincePledge, reminderLevel }) {
  const subject =
    reminderLevel === 'final' ? 'Final reminder: Your pledge of ' + formatCurrency(pledgeAmount) :
    reminderLevel === 'second' ? 'Friendly reminder: Your pledge' :
    'Quick reminder: Your pledge of ' + formatCurrency(pledgeAmount)

  const tone =
    reminderLevel === 'final' ? 'We wanted to reach out one last time...' :
    reminderLevel === 'second' ? 'We hope this message finds you well...' :
    'Thank you again for your generous pledge...'

  return (
    <Email>
      <Heading>{subject}</Heading>
      <Text>Dear {donorName},</Text>
      <Text>{tone}</Text>
      <Text>
        We wanted to follow up on the pledge you made {daysSincePledge} days ago
        during our phone campaign.
      </Text>
      {/* ... rest of template */}
    </Email>
  )
}
```

### Converting Pledge to Donation

```typescript
// When payment received
async function convertPledgeToDonation(callLogId: string) {
  const callLog = await getCallLog(callLogId)

  // 1. Create donation record
  const { data: donation } = await supabase
    .from('donations')
    .insert({
      contact_id: callLog.contact_id,
      donation_date: new Date(),
      amount: callLog.pledge_amount,
      payment_method: callLog.pledge_payment_method,
      source_system: 'phone_athon',
      external_id: `pledge-${callLogId}`,
      campaign_name: callLog.call_campaign.name,
      memo: `Phone pledge from ${formatDate(callLog.call_date)}`,
      thank_you_sent: callLog.acknowledgment_sent, // Already acknowledged
      tax_year: new Date().getFullYear()
    })
    .select()
    .single()

  // 2. Mark pledge as paid
  await supabase
    .from('call_logs')
    .update({ pledge_status: 'paid' })
    .eq('id', callLogId)

  // 3. Generate tax receipt
  await generateTaxReceipt(donation.id)

  // 4. Send receipt to donor
  await sendTaxReceiptEmail(donation.id)

  toast.success('Pledge converted to donation! Tax receipt sent.')
}
```

---

## Campaign Reports Update

### Pledge Status Report

```tsx
function PledgeStatusReport({ campaignId }: Props) {
  const pledges = usePledges(campaignId)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pledge Follow-Up Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Pledges</p>
              <p className="text-2xl font-bold">{pledges.total}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Paid</p>
              <p className="text-2xl font-bold text-green-600">{pledges.paid}</p>
              <p className="text-xs text-muted-foreground">
                {pledges.paidAmount} ({pledges.fulfillmentRate}%)
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="text-2xl font-bold text-amber-600">{pledges.pending}</p>
              <p className="text-xs text-muted-foreground">
                {pledges.pendingAmount}
              </p>
            </div>
          </div>

          {/* Pending Pledges Table */}
          <div>
            <h4 className="font-semibold mb-2">Pending Pledges</h4>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Donor</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Days Ago</TableHead>
                  <TableHead>Reminders</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pledges.pending.map(pledge => (
                  <TableRow key={pledge.id}>
                    <TableCell>{pledge.donor_name}</TableCell>
                    <TableCell>{formatCurrency(pledge.amount)}</TableCell>
                    <TableCell>
                      {daysBetween(pledge.pledge_date, new Date())} days
                    </TableCell>
                    <TableCell>
                      {pledge.reminder_count} sent
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        onClick={() => convertPledgeToDonation(pledge.id)}
                      >
                        Mark as Paid
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <Button variant="outline" onClick={() => exportPendingPledges(campaignId)}>
            Export Pending Pledges
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Summary: Complete Pledge Flow

```
1. DURING CALL
   ↓
   Donor pledges $300 by check
   ↓
   Caller captures in system
   ↓

2. IMMEDIATE CONFIRMATION
   ↓
   Modal appears: "Send payment instructions?"
   ↓
   Caller selects: Email ✓ (or Mail)
   ↓
   Caller checks: "Also send acknowledgment" ✓
   ↓
   Click "Send Emails"
   ↓

3. INSTANT DELIVERY (Email)
   ↓
   Email #1: Payment Instructions
   - How to write check
   - Where to mail
   - Amount due
   ↓
   Email #2: Acknowledgment
   - Thank you message
   - Impact statement
   - Donor history
   ↓

4. FOLLOW-UP REMINDERS
   ↓
   Day 7: Gentle reminder (if unpaid)
   Day 14: Second reminder
   Day 21: Final reminder
   ↓

5. PAYMENT RECEIVED
   ↓
   Staff clicks "Mark as Paid"
   ↓
   System creates donation record
   ↓
   Tax receipt generated
   ↓
   Tax receipt emailed to donor
   ↓

6. COMPLETE ✓
```

---

## Implementation Checklist

**Database:**
- [ ] Add acknowledgment fields to call_logs
- [ ] Add payment tracking fields
- [ ] Create indexes

**Email Templates:**
- [ ] Payment instructions (check)
- [ ] Payment instructions (credit card)
- [ ] Payment instructions (online)
- [ ] Acknowledgment email
- [ ] Reminder emails (3 levels)
- [ ] Tax receipt email

**PDF Letters:**
- [ ] Payment instructions letter
- [ ] Acknowledgment letter
- [ ] Letterhead design

**UI Components:**
- [ ] Pledge confirmation modal
- [ ] Delivery method selector
- [ ] Email preview
- [ ] Pledge status table
- [ ] Mark as paid button

**Backend Functions:**
- [ ] Send payment instructions
- [ ] Send acknowledgment
- [ ] Generate PDF letters
- [ ] Automated reminder job
- [ ] Convert pledge to donation
- [ ] Generate tax receipt

**Testing:**
- [ ] Test email delivery
- [ ] Test PDF generation
- [ ] Test reminder workflow
- [ ] Test pledge conversion
- [ ] Test with/without email address
- [ ] Test with/without mailing address

---

**This completes the pledge workflow with proper acknowledgments and payment instructions!**
