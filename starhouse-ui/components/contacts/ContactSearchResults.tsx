'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Avatar } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { formatName, getInitials } from '@/lib/utils'
import { Mail, Phone, MapPin, Loader2 } from 'lucide-react'
import type { Database } from '@/lib/types/database'

type Contact = Database['public']['Tables']['contacts']['Row']

interface ContactSearchResultsProps {
  searchQuery: string
  onSelectContact: (id: string) => void
}

export function ContactSearchResults({
  searchQuery,
  onSelectContact,
}: ContactSearchResultsProps) {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setContacts([])
      return
    }

    const searchContacts = async () => {
      setLoading(true)
      const supabase = createClient()

      // Tokenized search: Split query into words and search across ALL name fields
      // This handles complex cases like:
      // - Multiple first names: "Lynn Amber Ryan"
      // - Couples: "Sue Johnson and Mike Moritz"
      // - Business names split across fields
      const words = searchQuery.trim().split(/\s+/)

      // Search these fields for each word
      const searchFields = [
        'first_name',
        'last_name',
        'additional_name',
        'paypal_first_name',
        'paypal_last_name',
        'paypal_business_name',
        'email',
        'phone'
      ]

      // For each word, check if it appears in ANY field
      // Example: "Lynn Amber Ryan" becomes:
      // (first_name ILIKE '%lynn%' OR last_name ILIKE '%lynn%' OR ... OR
      //  first_name ILIKE '%amber%' OR last_name ILIKE '%amber%' OR ... OR
      //  first_name ILIKE '%ryan%' OR last_name ILIKE '%ryan%' OR ...)
      const conditions = words.flatMap(word =>
        searchFields.map(field => `${field}.ilike.%${word}%`)
      )

      const { data, error } = await supabase
        .from('contacts')
        .select('*')
        .is('deleted_at', null)
        .or(conditions.join(','))
        .order('created_at', { ascending: false })
        .limit(20)

      if (error) {
        console.error('Search error:', error)
      }

      if (!error && data) {
        setContacts(data)
      }

      setLoading(false)
    }

    // Debounce search
    const timer = setTimeout(searchContacts, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  if (!searchQuery) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 rounded-full bg-primary/10 p-6">
          <Mail className="h-12 w-12 text-primary" />
        </div>
        <h3 className="mb-2 text-lg font-medium">Start searching</h3>
        <p className="text-sm text-muted-foreground">
          Enter a name, email, or phone number to find contacts
        </p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (contacts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 rounded-full bg-muted p-6">
          <Mail className="h-12 w-12 text-muted-foreground" />
        </div>
        <h3 className="mb-2 text-lg font-medium">No contacts found</h3>
        <p className="text-sm text-muted-foreground">
          Try a different search term
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        {contacts.length} {contacts.length === 1 ? 'contact' : 'contacts'} found
      </p>

      {contacts.map((contact) => (
        <Card
          key={contact.id}
          className="cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:shadow-lg"
          onClick={() => onSelectContact(contact.id)}
        >
          <div className="flex items-center gap-4 p-4">
            <Avatar
              initials={getInitials(contact.first_name, contact.last_name)}
              className="h-14 w-14 flex-shrink-0"
            />

            <div className="flex-1 space-y-1 overflow-hidden">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">
                  {formatName(contact.first_name, contact.last_name)}
                </h3>
                {contact.email_subscribed && (
                  <Badge variant="secondary" className="text-xs">
                    Subscribed
                  </Badge>
                )}
              </div>

              <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                {contact.email && (
                  <div className="flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5" />
                    <span className="truncate">{contact.email}</span>
                  </div>
                )}
                {contact.phone && (
                  <div className="flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5" />
                    <span>{contact.phone}</span>
                  </div>
                )}
                {contact.city && contact.state && (
                  <div className="flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5" />
                    <span>
                      {contact.city}, {contact.state}
                    </span>
                  </div>
                )}
              </div>

              {contact.source_system && (
                <Badge variant="outline" className="text-xs capitalize">
                  {contact.source_system.replace('_', ' ')}
                </Badge>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
