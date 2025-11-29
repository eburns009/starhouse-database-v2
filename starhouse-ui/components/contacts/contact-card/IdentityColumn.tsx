'use client'

import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  AtSign,
  Phone,
  MapPin,
  Tag,
  Users,
  Key,
  FileText,
  Plus,
  X,
  CheckCircle,
  Mail,
  Loader2,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { createClient } from '@/lib/supabase/client'
import { CollapsibleSection } from './CollapsibleSection'
import type { Contact, ContactEmail, ContactTag } from '@/lib/types/contact'
import type { ContactRole, ContactNote } from './types'

interface IdentityColumnProps {
  contact: Contact
  contactEmails: ContactEmail[]
  contactTags: ContactTag[]
  contactRoles: ContactRole[]
  contactNotes: ContactNote[]
  onTagsUpdated: () => void
  onNotesUpdated: () => void
}

/**
 * Left column: Identity details (emails, phones, addresses, tags, roles, notes)
 * FAANG Standard: Follows two-column layout from UI research
 */
export function IdentityColumn({
  contact,
  contactEmails,
  contactTags,
  contactRoles,
  contactNotes,
  onTagsUpdated,
  onNotesUpdated,
}: IdentityColumnProps) {
  const [newTag, setNewTag] = useState('')
  const [addingTag, setAddingTag] = useState(false)
  const [newNoteSubject, setNewNoteSubject] = useState('')
  const [newNoteContent, setNewNoteContent] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [showAddNote, setShowAddNote] = useState(false)

  // External IDs for debugging
  // Cast to any for fields that may exist in database but not in TypeScript types
  const contactAny = contact as Record<string, unknown>
  const externalIds = [
    { label: 'Kajabi', value: contact.kajabi_id },
    { label: 'Kajabi Member', value: contact.kajabi_member_id },
    { label: 'PayPal', value: contactAny.paypal_payer_id as string | null },
    { label: 'QuickBooks', value: contact.quickbooks_id },
    { label: 'Ticket Tailor', value: contact.ticket_tailor_id },
    { label: 'Zoho', value: contact.zoho_id },
    { label: 'Mailchimp', value: contact.mailchimp_id },
  ].filter(id => id.value)

  // Phone numbers (extract from contact)
  const phones = [
    contact.phone && { number: contact.phone, label: 'Primary', source: contact.source_system },
    contact.paypal_phone && contact.paypal_phone !== contact.phone && { number: contact.paypal_phone, label: 'PayPal', source: 'paypal' },
  ].filter(Boolean) as Array<{ number: string; label: string; source: string }>

  // Addresses
  const addresses = [
    (contact.address_line_1 || contact.city) && {
      label: 'Billing',
      line1: contact.address_line_1,
      line2: contact.address_line_2,
      city: contact.city,
      state: contact.state,
      postalCode: contact.postal_code,
      country: contact.country,
    },
    (contact.shipping_address_line_1 || contact.shipping_city) && {
      label: 'Shipping',
      line1: contact.shipping_address_line_1,
      line2: contact.shipping_address_line_2,
      city: contact.shipping_city,
      state: contact.shipping_state,
      postalCode: contact.shipping_postal_code,
      country: contact.shipping_country,
    },
  ].filter(Boolean) as Array<{
    label: string
    line1: string | null
    line2: string | null
    city: string | null
    state: string | null
    postalCode: string | null
    country: string | null
  }>

  const handleAddTag = async () => {
    const normalized = newTag.trim().toLowerCase()
    if (!normalized) return

    setAddingTag(true)
    try {
      const supabase = createClient()

      // Check if tag exists
      const { data: existingTag } = await supabase
        .from('tags')
        .select('id')
        .eq('name_norm', normalized)
        .single()

      let tagId: string

      if (existingTag) {
        tagId = existingTag.id
      } else {
        const { data: newTagData, error: createError } = await supabase
          .from('tags')
          .insert({
            name: newTag.trim(),
            name_norm: normalized,
            description: 'Added manually via UI',
          })
          .select('id')
          .single()

        if (createError) throw createError
        tagId = newTagData.id
      }

      // Insert into junction table
      const { error: junctionError } = await supabase
        .from('contact_tags')
        .insert({
          contact_id: contact.id,
          tag_id: tagId,
        })

      if (junctionError && junctionError.code !== '23505') {
        throw junctionError
      }

      setNewTag('')
      onTagsUpdated()
    } catch (err) {
      console.error('Error adding tag:', err)
      alert('Failed to add tag')
    } finally {
      setAddingTag(false)
    }
  }

  const handleRemoveTag = async (contactTagId: string) => {
    try {
      const supabase = createClient()
      await supabase.from('contact_tags').delete().eq('id', contactTagId)
      onTagsUpdated()
    } catch (err) {
      console.error('Error removing tag:', err)
    }
  }

  const handleSaveNote = async () => {
    if (!newNoteSubject.trim() || !newNoteContent.trim()) return

    setSavingNote(true)
    try {
      const supabase = createClient()
      await supabase.from('contact_notes').insert({
        contact_id: contact.id,
        subject: newNoteSubject.trim(),
        content: newNoteContent.trim(),
        note_type: 'general',
        author_name: 'User',
      })

      setNewNoteSubject('')
      setNewNoteContent('')
      setShowAddNote(false)
      onNotesUpdated()
    } catch (err) {
      console.error('Error saving note:', err)
      alert('Failed to save note')
    } finally {
      setSavingNote(false)
    }
  }

  return (
    <div className="space-y-3">
      {/* All Emails */}
      <CollapsibleSection
        title="Emails"
        count={contactEmails.length}
        icon={<AtSign className="h-4 w-4" />}
        defaultOpen={true}
        isEmpty={contactEmails.length === 0}
        emptyMessage={`Primary email: ${contact.email}`}
      >
        <div className="space-y-2">
          {contactEmails.map((email) => (
            <div
              key={email.id}
              className={`rounded-md border p-2.5 ${
                email.is_primary ? 'border-primary bg-primary/5' : 'border-border'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <a
                    href={`mailto:${email.email}`}
                    className="text-sm font-mono text-primary hover:underline break-all"
                  >
                    {email.email}
                  </a>
                  <div className="flex flex-wrap items-center gap-1 mt-1">
                    {email.is_primary && (
                      <Badge variant="default" className="text-[10px] px-1.5 py-0">
                        Primary
                      </Badge>
                    )}
                    {email.is_outreach && (
                      <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-blue-100 text-blue-700">
                        <Mail className="h-2.5 w-2.5 mr-0.5" />
                        Outreach
                      </Badge>
                    )}
                    {email.verified && (
                      <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-green-100 text-green-700">
                        <CheckCircle className="h-2.5 w-2.5 mr-0.5" />
                        Verified
                      </Badge>
                    )}
                  </div>
                </div>
                <Badge variant="outline" className="text-[10px] capitalize flex-shrink-0">
                  {email.source}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Phone Numbers */}
      <CollapsibleSection
        title="Phones"
        count={phones.length}
        icon={<Phone className="h-4 w-4" />}
        isEmpty={phones.length === 0}
        emptyMessage="No phone numbers on file"
      >
        <div className="space-y-2">
          {phones.map((phone, idx) => (
            <div key={idx} className="rounded-md border border-border p-2.5">
              <div className="flex items-center justify-between">
                <a
                  href={`tel:${phone.number}`}
                  className="text-sm font-mono text-primary hover:underline"
                >
                  {phone.number}
                </a>
                <div className="flex items-center gap-1.5">
                  <Badge variant="outline" className="text-[10px]">
                    {phone.label}
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Addresses */}
      <CollapsibleSection
        title="Addresses"
        count={addresses.length}
        icon={<MapPin className="h-4 w-4" />}
        isEmpty={addresses.length === 0}
        emptyMessage="No addresses on file"
      >
        <div className="space-y-2">
          {addresses.map((addr, idx) => (
            <div key={idx} className="rounded-md border border-border p-2.5">
              <div className="flex items-start justify-between gap-2">
                <div className="text-sm space-y-0.5">
                  {addr.line1 && <p>{addr.line1}</p>}
                  {addr.line2 && <p className="text-muted-foreground">{addr.line2}</p>}
                  <p className="text-muted-foreground">
                    {[addr.city, addr.state, addr.postalCode].filter(Boolean).join(', ')}
                  </p>
                  {addr.country && addr.country !== 'US' && (
                    <p className="text-muted-foreground">{addr.country}</p>
                  )}
                </div>
                <Badge variant="outline" className="text-[10px] flex-shrink-0">
                  {addr.label}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Tags */}
      <CollapsibleSection
        title="Tags"
        count={contactTags.length}
        icon={<Tag className="h-4 w-4" />}
        defaultOpen={contactTags.length > 0}
        isEmpty={false}
      >
        <div className="space-y-3">
          {/* Add Tag Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !addingTag && handleAddTag()}
              placeholder="Add a tag..."
              className="flex-1 rounded-md border border-input bg-background px-2.5 py-1.5 text-sm"
              disabled={addingTag}
            />
            <Button
              size="sm"
              onClick={handleAddTag}
              disabled={!newTag.trim() || addingTag}
              className="h-8 px-2"
            >
              {addingTag ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
            </Button>
          </div>

          {/* Tags List */}
          {contactTags.length === 0 ? (
            <p className="text-sm text-muted-foreground italic text-center py-2">
              No tags yet
            </p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {contactTags.map((ct) => {
                const isKajabiTag = !ct.tags.description?.includes('manually')
                return (
                  <Badge
                    key={ct.id}
                    variant="secondary"
                    className={`text-xs ${
                      isKajabiTag
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                        : ''
                    }`}
                  >
                    {ct.tags.name}
                    {isKajabiTag && <span className="ml-1 text-[9px] opacity-60">K</span>}
                    <button
                      onClick={() => handleRemoveTag(ct.id)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                )
              })}
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* Roles */}
      <CollapsibleSection
        title="Roles"
        count={contactRoles.length}
        icon={<Users className="h-4 w-4" />}
        isEmpty={contactRoles.length === 0}
        emptyMessage="No roles assigned"
      >
        <div className="space-y-2">
          {contactRoles.map((role) => (
            <div key={role.id} className="rounded-md border border-border p-2.5">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium capitalize">{role.role}</span>
                <Badge
                  variant={role.status === 'active' ? 'default' : 'secondary'}
                  className="text-[10px]"
                >
                  {role.status}
                </Badge>
              </div>
              {role.started_at && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  Since {formatDate(role.started_at)}
                  {role.ended_at && ` — Ended ${formatDate(role.ended_at)}`}
                </p>
              )}
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* External IDs (collapsed by default) */}
      <CollapsibleSection
        title="External IDs"
        count={externalIds.length}
        icon={<Key className="h-4 w-4" />}
        isEmpty={externalIds.length === 0}
        emptyMessage="No external IDs linked"
      >
        <div className="space-y-1">
          {externalIds.map((id, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs py-1">
              <span className="text-muted-foreground">{id.label}</span>
              <code className="font-mono text-[11px] bg-muted px-1.5 py-0.5 rounded">
                {id.value}
              </code>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Staff Notes */}
      <CollapsibleSection
        title="Staff Notes"
        count={contactNotes.length}
        icon={<FileText className="h-4 w-4" />}
        defaultOpen={true}
        isEmpty={false}
      >
        <div className="space-y-3">
          {/* Add Note Toggle */}
          {!showAddNote ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAddNote(true)}
              className="w-full"
            >
              <Plus className="h-3.5 w-3.5 mr-1.5" />
              Add Note
            </Button>
          ) : (
            <div className="space-y-2 rounded-md border border-border bg-muted/30 p-3">
              <input
                type="text"
                value={newNoteSubject}
                onChange={(e) => setNewNoteSubject(e.target.value)}
                placeholder="Subject"
                className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-sm"
              />
              <textarea
                value={newNoteContent}
                onChange={(e) => setNewNoteContent(e.target.value)}
                placeholder="Note content..."
                rows={3}
                className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-sm resize-none"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleSaveNote}
                  disabled={savingNote || !newNoteSubject.trim() || !newNoteContent.trim()}
                >
                  {savingNote ? 'Saving...' : 'Save'}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setShowAddNote(false)
                    setNewNoteSubject('')
                    setNewNoteContent('')
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Notes List */}
          {contactNotes.length === 0 && !showAddNote ? (
            <p className="text-sm text-muted-foreground italic text-center py-2">
              No notes yet
            </p>
          ) : (
            <div className="space-y-2">
              {contactNotes.map((note) => (
                <div key={note.id} className="rounded-md border border-border p-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium">{note.subject || 'Note'}</p>
                    {note.is_pinned && (
                      <Badge variant="secondary" className="text-[10px]">Pinned</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1 whitespace-pre-wrap line-clamp-3">
                    {note.content}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    {formatDate(note.created_at)} • {note.author_name}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </CollapsibleSection>
    </div>
  )
}
