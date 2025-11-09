/**
 * Contact Module Types
 * StarHouse CRM - Contact Management
 */

// Activity types for timeline
export const ACTIVITY_TYPES = {
  WEBHOOK: 'webhook',
  TRANSACTION: 'transaction',
  TAG: 'tag',
  NOTE: 'note',
  ROLE: 'role',
  SUBSCRIPTION: 'subscription'
}

// Note types
export const NOTE_TYPES = {
  CALL: 'call',
  EMAIL: 'email',
  MEETING: 'meeting',
  GENERAL: 'general',
  SYSTEM: 'system',
  DONATION: 'donation',
  EVENT: 'event',
  ISSUE: 'issue'
}

// Email types
export const EMAIL_TYPES = {
  PERSONAL: 'personal',
  WORK: 'work',
  OTHER: 'other'
}

// Contact roles
export const CONTACT_ROLES = {
  MEMBER: 'member',
  DONOR: 'donor',
  VOLUNTEER: 'volunteer',
  ATTENDEE: 'attendee',
  SUBSCRIBER: 'subscriber',
  STAFF: 'staff',
  BOARD: 'board',
  PARTNER: 'partner'
}

// External identity systems
export const EXTERNAL_SYSTEMS = {
  KAJABI: 'kajabi',
  KAJABI_MEMBER: 'kajabi_member',
  PAYPAL: 'paypal',
  TICKET_TAILOR: 'ticket_tailor',
  ZOHO: 'zoho',
  QUICKBOOKS: 'quickbooks',
  MAILCHIMP: 'mailchimp',
  STRIPE: 'stripe'
}
