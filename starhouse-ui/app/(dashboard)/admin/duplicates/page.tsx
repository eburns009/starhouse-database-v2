'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Loader2, AlertTriangle, Mail, Phone, MapPin } from 'lucide-react'
import { formatName, formatDate } from '@/lib/utils'
import type { Contact } from '@/lib/types/contact'

interface DuplicateGroup {
  group_id: string
  reason: string
  contact_count: number
  contacts: Contact[]
}

type FilterType = 'all' | 'high' | 'medium' | 'low'

export default function DuplicatesPage() {
  const [groups, setGroups] = useState<DuplicateGroup[]>([])
  const [filter, setFilter] = useState<FilterType>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadDuplicates() {
      setLoading(true)
      const supabase = createClient()

      // Get all contacts with duplicate flags
      const { data: contacts, error } = await supabase
        .from('contacts')
        .select('*')
        .not('potential_duplicate_group', 'is', null)
        .is('deleted_at', null)
        .order('potential_duplicate_group')
        .order('created_at', { ascending: true })

      if (error) {
        console.error('Error loading duplicates:', error)
        setLoading(false)
        return
      }

      if (!contacts) {
        setLoading(false)
        return
      }

      // Group by duplicate_group
      const groupMap = new Map<string, DuplicateGroup>()

      contacts.forEach((contact: Contact) => {
        const groupId = contact.potential_duplicate_group!
        if (!groupMap.has(groupId)) {
          groupMap.set(groupId, {
            group_id: groupId,
            reason: contact.potential_duplicate_reason || 'Unknown',
            contact_count: 0,
            contacts: [],
          })
        }
        const group = groupMap.get(groupId)!
        group.contacts.push(contact)
        group.contact_count++
      })

      setGroups(Array.from(groupMap.values()))
      setLoading(false)
    }

    loadDuplicates()
  }, [])

  // Filter groups by confidence level
  const filteredGroups = groups.filter((group) => {
    if (filter === 'all') return true
    if (filter === 'high')
      return (
        group.reason.toLowerCase().includes('phone') ||
        group.reason.toLowerCase().includes('address')
      )
    if (filter === 'medium')
      return (
        group.reason.toLowerCase().includes('address') &&
        !group.reason.toLowerCase().includes('phone')
      )
    if (filter === 'low')
      return (
        !group.reason.toLowerCase().includes('phone') &&
        !group.reason.toLowerCase().includes('address')
      )
    return true
  })

  const highCount = groups.filter(
    (g) =>
      g.reason.toLowerCase().includes('phone') ||
      g.reason.toLowerCase().includes('address')
  ).length
  const mediumCount = groups.filter(
    (g) =>
      g.reason.toLowerCase().includes('address') &&
      !g.reason.toLowerCase().includes('phone')
  ).length
  const lowCount = groups.filter(
    (g) =>
      !g.reason.toLowerCase().includes('phone') &&
      !g.reason.toLowerCase().includes('address')
  ).length

  if (loading) {
    return (
      <div className="container mx-auto p-8">
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Duplicate Contacts</h1>
        <p className="mt-2 text-muted-foreground">
          Review and manage potential duplicate contacts
        </p>
      </div>

      {/* Stats Cards */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Groups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{groups.length}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              {groups.reduce((sum, g) => sum + g.contact_count, 0)} contacts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              High Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{highCount}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              Same name + phone/address
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Medium Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {mediumCount}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Same name + address
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Low Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{lowCount}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              Same name only
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filter buttons */}
      <div className="mb-6 flex flex-wrap gap-2">
        <Button
          onClick={() => setFilter('all')}
          variant={filter === 'all' ? 'default' : 'outline'}
        >
          All ({groups.length})
        </Button>
        <Button
          onClick={() => setFilter('high')}
          variant={filter === 'high' ? 'default' : 'outline'}
          className={
            filter === 'high'
              ? 'bg-red-600 hover:bg-red-700'
              : 'border-red-300 text-red-700 hover:bg-red-50'
          }
        >
          High Confidence ({highCount})
        </Button>
        <Button
          onClick={() => setFilter('medium')}
          variant={filter === 'medium' ? 'default' : 'outline'}
          className={
            filter === 'medium'
              ? 'bg-yellow-600 hover:bg-yellow-700'
              : 'border-yellow-300 text-yellow-700 hover:bg-yellow-50'
          }
        >
          Medium Confidence ({mediumCount})
        </Button>
        <Button
          onClick={() => setFilter('low')}
          variant={filter === 'low' ? 'default' : 'outline'}
          className={
            filter === 'low'
              ? 'bg-green-600 hover:bg-green-700'
              : 'border-green-300 text-green-700 hover:bg-green-50'
          }
        >
          Low Confidence ({lowCount})
        </Button>
      </div>

      {/* Duplicate groups */}
      {filteredGroups.length === 0 && (
        <Card className="p-8">
          <div className="text-center">
            <div className="mb-4 rounded-full bg-muted p-6 inline-block">
              <AlertTriangle className="h-12 w-12 text-muted-foreground" />
            </div>
            <h3 className="mb-2 text-lg font-medium">No duplicates found</h3>
            <p className="text-sm text-muted-foreground">
              {filter === 'all'
                ? 'All contacts are unique'
                : 'Try a different filter'}
            </p>
          </div>
        </Card>
      )}

      <div className="space-y-4">
        {filteredGroups.map((group) => (
          <Card key={group.group_id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">
                    {formatName(
                      group.contacts[0]?.first_name,
                      group.contacts[0]?.last_name
                    )}
                  </CardTitle>
                  <div className="mt-2 flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={
                        group.reason.toLowerCase().includes('phone') ||
                        group.reason.toLowerCase().includes('address')
                          ? 'border-red-500 text-red-700 bg-red-50'
                          : group.reason.toLowerCase().includes('address')
                          ? 'border-yellow-500 text-yellow-700 bg-yellow-50'
                          : 'border-green-500 text-green-700 bg-green-50'
                      }
                    >
                      {group.reason}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {group.contact_count} accounts
                    </span>
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={() => {
                    alert(
                      'Merge functionality coming soon! For now, please manually review and consolidate these contacts.'
                    )
                  }}
                >
                  Merge
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Contact cards */}
              <div className="grid gap-3 md:grid-cols-2">
                {group.contacts.map((contact) => (
                  <div
                    key={contact.id}
                    className="rounded-lg border border-border/50 bg-muted/30 p-4 transition-colors hover:bg-accent/50"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">
                            {contact.email}
                          </span>
                        </div>
                        {contact.email_subscribed && (
                          <Badge variant="secondary" className="text-xs">
                            Subscribed
                          </Badge>
                        )}
                      </div>

                      {contact.phone && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Phone className="h-4 w-4" />
                          {contact.phone}
                        </div>
                      )}

                      {contact.city && contact.state && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <MapPin className="h-4 w-4" />
                          {contact.city}, {contact.state}
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {contact.source_system}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(contact.created_at)}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            window.location.href = `/contacts?id=${contact.id}`
                          }}
                        >
                          View details
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
