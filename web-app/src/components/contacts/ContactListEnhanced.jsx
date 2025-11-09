import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../../lib/supabase'
import { CONTACT_ROLES } from '../../types/contacts'
import { useKeyboard } from '../../hooks/useKeyboard'
import { useToast } from '../../hooks/useToast'
import Button from '../ui/Button'
import Toast from '../ui/Toast'
import ContactForm from './ContactForm'
import AdvancedSearchFilters from './AdvancedSearchFilters'
import BulkActionsBar from './BulkActionsBar'
import ExportDialog from './ExportDialog'
import DuplicateDetection from './DuplicateDetection'
import KeyboardShortcutsHelp from './KeyboardShortcutsHelp'
import ProgramPartnerComplianceFilter, { ComplianceBadge } from './ProgramPartnerComplianceFilter'
import './ContactList.css'

const PAGE_SIZE = 50

export default function ContactListEnhanced({ onSelectContact }) {
  // Data state
  const [contacts, setContacts] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [contactTags, setContactTags] = useState({}) // Map of contact ID to tags array

  // UI state
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [showDuplicateDetection, setShowDuplicateDetection] = useState(false)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)

  // Selection state
  const [selectedIds, setSelectedIds] = useState([])

  // Search & filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [roleFilter, setRoleFilter] = useState('all') // all, member, donor, volunteer, program_partners
  const [subscriptionFilter, setSubscriptionFilter] = useState('all') // all, active, inactive
  const [advancedFilters, setAdvancedFilters] = useState({})

  // Pagination state
  const [currentPage, setCurrentPage] = useState(0)
  const [sortBy, setSortBy] = useState('updated_at')
  const [sortOrder, setSortOrder] = useState('desc')

  const { success, toasts, removeToast } = useToast()

  // Selection handlers
  function handleSelectAll(e) {
    e?.preventDefault()
    setSelectedIds(contacts.map(c => c.contact_id || c.id))
  }

  function handleClearSelection(e) {
    e?.preventDefault()
    setSelectedIds([])
  }

  function handleToggleSelect(contactId) {
    setSelectedIds(prev => {
      if (prev.includes(contactId)) {
        return prev.filter(id => id !== contactId)
      } else {
        return [...prev, contactId]
      }
    })
  }

  // Keyboard shortcuts
  useKeyboard('k', () => setShowAdvancedFilters(true), { ctrl: true })
  useKeyboard('n', () => setShowCreateModal(true), { ctrl: true })
  useKeyboard('f', () => setShowAdvancedFilters(true), { ctrl: true })
  useKeyboard('/', () => setShowKeyboardHelp(true), { ctrl: true })
  useKeyboard('?', () => setShowKeyboardHelp(true))
  useKeyboard('a', handleSelectAll, { ctrl: true })
  useKeyboard('a', handleClearSelection, { ctrl: true, shift: true })

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput)
      setCurrentPage(0) // Reset to first page on search
    }, 500)
    return () => clearTimeout(timer)
  }, [searchInput])

  // Fetch contacts when filters change
  useEffect(() => {
    fetchContacts()
  }, [searchQuery, roleFilter, subscriptionFilter, advancedFilters, currentPage, sortBy, sortOrder])

  // Fetch tags for displayed contacts
  useEffect(() => {
    if (contacts.length > 0) {
      fetchContactTags()
    }
  }, [contacts])

  const fetchContacts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const offset = currentPage * PAGE_SIZE

      // OPTION A: If searching, use search_contacts function
      if (searchQuery.trim()) {
        const { data, error: searchError } = await supabase
          .rpc('search_contacts', {
            p_query: searchQuery,
            p_limit: PAGE_SIZE,
            p_offset: offset
          })

        if (searchError) throw searchError

        setContacts(data || [])
        setTotalCount(data?.length || 0)
      }
      // OPTION B: Use optimized list view with filters
      else {
        let query = supabase
          .from('v_contact_list_with_subscriptions')
          .select('*', { count: 'exact' })

        // Apply role filter
        if (roleFilter === 'member') {
          query = query.eq('is_member', true)
        } else if (roleFilter === 'donor') {
          query = query.eq('is_donor', true)
        } else if (roleFilter === 'volunteer') {
          query = query.eq('is_volunteer', true)
        } else if (roleFilter === 'program_partners') {
          // Show all expected Program Partners
          query = query.eq('is_expected_program_partner', true)
        }

        // Apply subscription filter
        if (subscriptionFilter === 'active') {
          query = query.eq('has_active_subscription', true)
        } else if (subscriptionFilter === 'inactive') {
          query = query.eq('has_active_subscription', false)
        }

        // Apply sorting
        query = query.order(sortBy, { ascending: sortOrder === 'asc' })

        // Apply pagination
        query = query.range(offset, offset + PAGE_SIZE - 1)

        const { data, error: listError, count } = await query

        if (listError) throw listError

        setContacts(data || [])
        setTotalCount(count || 0)
      }
    } catch (err) {
      console.error('Error fetching contacts:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [searchQuery, roleFilter, subscriptionFilter, advancedFilters, currentPage, sortBy, sortOrder])

  async function fetchContactTags() {
    try {
      const contactIds = contacts.map(c => c.contact_id || c.id)

      const { data, error } = await supabase
        .from('contact_tags')
        .select(`
          contact_id,
          tag:tags (
            id,
            name,
            color
          )
        `)
        .in('contact_id', contactIds)

      if (error) throw error

      // Group tags by contact ID
      const tagsMap = {}
      data?.forEach(ct => {
        if (!tagsMap[ct.contact_id]) {
          tagsMap[ct.contact_id] = []
        }
        tagsMap[ct.contact_id].push(ct.tag)
      })

      setContactTags(tagsMap)
    } catch (err) {
      console.error('Error fetching contact tags:', err)
    }
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const formatCurrency = (amount) => {
    if (!amount) return '$0.00'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatDate = (date) => {
    if (!date) return 'Never'
    const d = new Date(date)
    const now = new Date()
    const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`
    return `${Math.floor(diffDays / 365)}y ago`
  }

  const getRoleBadges = (contact) => {
    const badges = []
    if (contact.is_member) badges.push({ label: 'Member', color: 'blue' })
    if (contact.is_donor) badges.push({ label: 'Donor', color: 'green' })
    if (contact.is_volunteer) badges.push({ label: 'Volunteer', color: 'purple' })
    return badges
  }

  const totalPages = Math.ceil(totalCount / PAGE_SIZE)

  return (
    <div className="contact-list-enhanced">
      {/* Header */}
      <div className="list-header">
        <div>
          <h1>Contacts</h1>
          <div className="header-stats">
            <span className="stat-badge">{totalCount.toLocaleString()} total</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDuplicateDetection(true)}
          >
            🔍 Find Duplicates
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAdvancedFilters(true)}
          >
            🔧 Advanced Filters
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowExportDialog(true)}
          >
            📥 Export
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowCreateModal(true)}
          >
            + New Contact
          </Button>
          <button
            onClick={() => setShowKeyboardHelp(true)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '20px',
              padding: '4px 8px'
            }}
            title="Keyboard shortcuts (Ctrl+/)"
          >
            ⌨️
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="filters-bar">
        {/* Search Input */}
        <div className="search-box">
          <input
            type="text"
            placeholder="Search by name, email, or phone..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="search-input"
          />
          {searchInput && (
            <button
              className="clear-search"
              onClick={() => {
                setSearchInput('')
                setSearchQuery('')
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Role Filter */}
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value)
            setCurrentPage(0)
          }}
          className="filter-select"
        >
          <option value="all">All Roles</option>
          <option value="member">Members Only</option>
          <option value="donor">Donors Only</option>
          <option value="volunteer">Volunteers Only</option>
          <option value="program_partners">🤝 Program Partners</option>
        </select>

        {/* Subscription Filter */}
        <select
          value={subscriptionFilter}
          onChange={(e) => {
            setSubscriptionFilter(e.target.value)
            setCurrentPage(0)
          }}
          className="filter-select"
        >
          <option value="all">All Subscriptions</option>
          <option value="active">Active Only</option>
          <option value="inactive">Inactive Only</option>
        </select>
      </div>

      {/* Bulk Actions Bar */}
      <BulkActionsBar
        selectedIds={selectedIds}
        onClearSelection={handleClearSelection}
        onActionComplete={(action) => {
          if (action === 'export') {
            setShowExportDialog(true)
          } else {
            fetchContacts()
          }
          setSelectedIds([])
        }}
      />

      {/* Results Info */}
      {searchQuery && (
        <div className="search-results-info">
          {loading ? (
            <span>Searching...</span>
          ) : (
            <span>
              Found {totalCount} {totalCount === 1 ? 'result' : 'results'} for "{searchQuery}"
              {contacts.length > 0 && contacts[0].match_score && (
                <span className="match-info">
                  {' '}(best match: {(contacts[0].match_score * 100).toFixed(0)}%)
                </span>
              )}
            </span>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading contacts...</p>
        </div>
      )}

      {/* Contact Table */}
      {!loading && contacts.length > 0 && (
        <>
          <div className="table-container">
            <table className="contacts-table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>
                    <input
                      type="checkbox"
                      checked={selectedIds.length === contacts.length && contacts.length > 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleSelectAll()
                        } else {
                          handleClearSelection()
                        }
                      }}
                    />
                  </th>
                  <th
                    onClick={() => handleSort('full_name')}
                    className="sortable"
                  >
                    Name {sortBy === 'full_name' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th>Email</th>
                  <th>Roles</th>
                  <th>Partner Status</th>
                  <th>Tags</th>
                  <th
                    onClick={() => handleSort('total_spent')}
                    className="sortable text-right"
                  >
                    Revenue {sortBy === 'total_spent' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center">Transactions</th>
                  <th>Member Status</th>
                  <th>Member Level</th>
                  <th>Billing</th>
                  <th>Member Since</th>
                  <th
                    onClick={() => handleSort('updated_at')}
                    className="sortable"
                  >
                    Last Activity {sortBy === 'updated_at' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((contact) => {
                  const contactId = contact.contact_id || contact.id
                  const tags = contactTags[contactId] || []

                  return (
                    <tr
                      key={contactId}
                      className="contact-row"
                      style={{ backgroundColor: selectedIds.includes(contactId) ? '#eff6ff' : 'transparent' }}
                    >
                      <td onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(contactId)}
                          onChange={() => handleToggleSelect(contactId)}
                        />
                      </td>
                      <td
                        className="contact-name"
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="name-cell">
                          <strong>{contact.full_name}</strong>
                          {contact.has_active_subscription && (
                            <span className="subscription-badge">✓</span>
                          )}
                        </div>
                      </td>
                      <td
                        className="contact-email"
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {contact.email}
                        {contact.match_type && (
                          <span className="match-type">{contact.match_type}</span>
                        )}
                      </td>
                      <td
                        className="contact-roles"
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="role-badges">
                          {getRoleBadges(contact).map((badge, idx) => (
                            <span
                              key={idx}
                              className={`role-badge role-${badge.color}`}
                            >
                              {badge.label}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {contact.is_expected_program_partner && (
                          <ComplianceBadge
                            status={contact.partner_compliance_status}
                            message={contact.partner_compliance_message}
                          />
                        )}
                      </td>
                      <td onClick={() => onSelectContact && onSelectContact(contactId)} style={{ cursor: 'pointer' }}>
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {tags.slice(0, 3).map(tag => (
                            <span
                              key={tag.id}
                              style={{
                                fontSize: '11px',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                backgroundColor: tag.color || '#e5e7eb',
                                color: '#374151',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {tag.name}
                            </span>
                          ))}
                          {tags.length > 3 && (
                            <span style={{ fontSize: '11px', color: '#6b7280' }}>
                              +{tags.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      <td
                        className="text-right"
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {formatCurrency(contact.total_spent)}
                      </td>
                      <td
                        className="text-center"
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {contact.transaction_count || 0}
                      </td>
                      {/* Member Status */}
                      <td
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {contact.subscription_status ? (
                          <span className={`status-badge status-${contact.subscription_status}`}>
                            {contact.subscription_status}
                          </span>
                        ) : (
                          <span style={{ color: '#9ca3af' }}>—</span>
                        )}
                      </td>

                      {/* Member Level */}
                      <td
                        className="contact-membership"
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {contact.membership_level ? (
                          <span>
                            {contact.membership_level}
                            {contact.is_legacy && (
                              <span style={{
                                fontSize: '10px',
                                marginLeft: '4px',
                                padding: '2px 4px',
                                background: '#fef5e7',
                                color: '#c05621',
                                borderRadius: '3px',
                                fontWeight: 600
                              }}>
                                LEGACY
                              </span>
                            )}
                          </span>
                        ) : '—'}
                      </td>

                      {/* Billing Period */}
                      <td
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer', fontSize: '13px' }}
                      >
                        {contact.is_annual === true ? (
                          <span style={{ color: '#7c3f19', fontWeight: 600 }}>Annual</span>
                        ) : contact.is_annual === false ? (
                          <span style={{ color: '#2c5282' }}>Monthly</span>
                        ) : (
                          <span style={{ color: '#9ca3af' }}>—</span>
                        )}
                      </td>

                      {/* Member Since */}
                      <td
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer', fontSize: '13px' }}
                      >
                        {contact.member_since ? formatDate(contact.member_since) : '—'}
                      </td>
                      <td
                        className="contact-activity"
                        onClick={() => onSelectContact && onSelectContact(contactId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {formatDate(contact.last_transaction_date || contact.updated_at)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <div className="pagination-info">
              Showing {currentPage * PAGE_SIZE + 1}–{Math.min((currentPage + 1) * PAGE_SIZE, totalCount)} of {totalCount}
            </div>
            <div className="pagination-controls">
              <button
                onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
                className="page-button"
              >
                ← Previous
              </button>
              <span className="page-indicator">
                Page {currentPage + 1} of {totalPages || 1}
              </span>
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage >= totalPages - 1}
                className="page-button"
              >
                Next →
              </button>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!loading && contacts.length === 0 && (
        <div className="empty-state">
          {searchQuery ? (
            <>
              <h3>No results found</h3>
              <p>Try adjusting your search or filters</p>
            </>
          ) : (
            <>
              <h3>No contacts</h3>
              <p>No contacts match the selected filters</p>
            </>
          )}
        </div>
      )}

      {/* Modals */}
      <ContactForm
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={(newContact) => {
          setShowCreateModal(false)
          success('Contact created successfully!')
          fetchContacts()
        }}
      />

      <AdvancedSearchFilters
        isOpen={showAdvancedFilters}
        onClose={() => setShowAdvancedFilters(false)}
        onApply={(filters) => {
          setAdvancedFilters(filters)
          setCurrentPage(0)
        }}
        initialFilters={advancedFilters}
      />

      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        selectedIds={selectedIds}
        currentFilters={{ searchQuery, roleFilter, subscriptionFilter, ...advancedFilters }}
      />

      <DuplicateDetection
        isOpen={showDuplicateDetection}
        onClose={() => setShowDuplicateDetection(false)}
        onResolved={() => {
          fetchContacts()
        }}
      />

      <KeyboardShortcutsHelp
        isOpen={showKeyboardHelp}
        onClose={() => setShowKeyboardHelp(false)}
      />

      {/* Toast Notifications */}
      <Toast toasts={toasts} onClose={removeToast} />
    </div>
  )
}
