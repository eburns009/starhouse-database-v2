'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, X } from 'lucide-react'
import { ContactSearchResults } from '@/components/contacts/ContactSearchResults'
import { ContactDetailCard } from '@/components/contacts/ContactDetailCard'

export default function ContactsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null)

  return (
    <div className="container mx-auto h-full p-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold">Contacts</h1>
          <p className="text-muted-foreground">
            Search by name, email, or phone number
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-8">
          <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search contacts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-12 pr-12 text-base"
            autoFocus
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-2 top-1/2 -translate-y-1/2"
              onClick={() => setSearchQuery('')}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Results or Detail Card */}
        {selectedContactId ? (
          <ContactDetailCard
            contactId={selectedContactId}
            onClose={() => setSelectedContactId(null)}
          />
        ) : (
          <ContactSearchResults
            searchQuery={searchQuery}
            onSelectContact={setSelectedContactId}
          />
        )}
      </div>
    </div>
  )
}
