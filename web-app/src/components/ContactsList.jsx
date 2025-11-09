import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import './ContactsList.css'

const PAGE_SIZE = 50

export default function ContactsList() {
  const [contacts, setContacts] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [selectedContact, setSelectedContact] = useState(null)
  const [totalCount, setTotalCount] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [page, setPage] = useState(0)
  const [viewMode, setViewMode] = useState('table') // 'table' or 'cards'

  // Filter states
  const [selectedTags, setSelectedTags] = useState([])
  const [selectedSubscription, setSelectedSubscription] = useState('')
  const [selectedProduct, setSelectedProduct] = useState('')
  const [availableTags, setAvailableTags] = useState([])
  const [availableSubscriptions, setAvailableSubscriptions] = useState([])
  const [availableProducts, setAvailableProducts] = useState([])
  const [showTagDropdown, setShowTagDropdown] = useState(false)

  useEffect(() => {
    fetchFilterOptions()
  }, [])

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchTerm(searchInput)
    }, 500) // Wait 500ms after user stops typing

    return () => clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    fetchContacts(true)
  }, [searchTerm, selectedTags, selectedSubscription, selectedProduct])

  async function fetchFilterOptions() {
    try {
      // Fetch products
      const { data: productsData, error: productsError } = await supabase
        .from('products')
        .select('id, name')
        .eq('active', true)
        .order('name')

      if (!productsError) {
        setAvailableProducts(productsData || [])
      }

      // Fetch unique tags
      const { data: tagsData, error: tagsError } = await supabase
        .from('tags')
        .select('id, name')
        .order('name')

      if (!tagsError) {
        setAvailableTags(tagsData || [])
      }

      // Fetch subscription statuses (active, canceled)
      const { data: subsData, error: subsError } = await supabase
        .from('subscriptions')
        .select('status')

      if (!subsError) {
        // Get unique statuses
        const uniqueStatuses = [...new Set(subsData?.map(s => s.status).filter(Boolean))]
        setAvailableSubscriptions(uniqueStatuses.sort())
      }
    } catch (err) {
      console.error('Error fetching filter options:', err)
    }
  }

  async function fetchContacts(reset = false) {
    try {
      if (reset) {
        setLoading(true)
        setPage(0)
        setContacts([])
      } else {
        setLoadingMore(true)
      }
      setError(null)

      const currentPage = reset ? 0 : page
      const from = currentPage * PAGE_SIZE
      const to = from + PAGE_SIZE - 1

      let contactIds = null

      // Get contact IDs for product filter (server-side)
      if (selectedProduct) {
        const { data: contactsWithProduct } = await supabase
          .from('contact_products')
          .select('contact_id')
          .eq('product_id', selectedProduct)

        contactIds = contactsWithProduct?.map(cp => cp.contact_id) || []

        // If no contacts have this product, return empty
        if (contactIds.length === 0) {
          setContacts([])
          setTotalCount(0)
          setHasMore(false)
          setLoading(false)
          setLoadingMore(false)
          return
        }
      }

      // Get contact IDs for tag filter (server-side) - multiple tags
      if (selectedTags.length > 0) {
        const { data: contactsWithTags } = await supabase
          .from('contact_tags')
          .select('contact_id')
          .in('tag_id', selectedTags)

        const tagContactIds = contactsWithTags?.map(ct => ct.contact_id) || []

        // If we already have product filter, intersect the sets
        if (contactIds) {
          contactIds = contactIds.filter(id => tagContactIds.includes(id))
        } else {
          contactIds = tagContactIds
        }

        // If no contacts match, return empty
        if (contactIds.length === 0) {
          setContacts([])
          setTotalCount(0)
          setHasMore(false)
          setLoading(false)
          setLoadingMore(false)
          return
        }
      }

      // Get contact IDs for subscription filter (server-side)
      if (selectedSubscription) {
        const { data: contactsWithSub } = await supabase
          .from('subscriptions')
          .select('contact_id')
          .eq('status', selectedSubscription)

        const subContactIds = contactsWithSub?.map(s => s.contact_id) || []

        // If we already have tag filter, intersect the sets
        if (contactIds) {
          contactIds = contactIds.filter(id => subContactIds.includes(id))
        } else {
          contactIds = subContactIds
        }

        // If no contacts match, return empty
        if (contactIds.length === 0) {
          setContacts([])
          setTotalCount(0)
          setHasMore(false)
          setLoading(false)
          setLoadingMore(false)
          return
        }
      }

      // Build the base query - sorted by most recent activity (updated_at)
      let query = supabase
        .from('contacts')
        .select('*', { count: 'exact' })
        .order('updated_at', { ascending: false })

      // Apply contact ID filter if we have tag, product, or subscription filters
      if (contactIds) {
        query = query.in('id', contactIds)
      }

      // Add server-side search if there's a search term
      if (searchTerm.trim()) {
        query = query.or(`email.ilike.%${searchTerm}%,first_name.ilike.%${searchTerm}%,last_name.ilike.%${searchTerm}%`)
      }

      // Apply pagination
      query = query.range(from, to)

      const { data, error, count } = await query

      if (error) throw error

      setTotalCount(count || 0)

      if (reset) {
        setContacts(data || [])
      } else {
        setContacts(prev => [...prev, ...(data || [])])
      }

      setHasMore(data && data.length === PAGE_SIZE)
      if (!reset) {
        setPage(prev => prev + 1)
      }
    } catch (err) {
      console.error('Error fetching contacts:', err)
      setError(err.message)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  function handleLoadMore() {
    if (!loadingMore && hasMore) {
      setPage(prev => prev + 1)
      fetchContacts(false)
    }
  }

  function exportToCSV() {
    // CSV headers
    const headers = ['First Name', 'Last Name', 'Email', 'Phone', 'Source System', 'Created At', 'Last Updated']

    // Convert contacts to CSV rows
    const rows = contacts.map(contact => [
      contact.first_name || '',
      contact.last_name || '',
      contact.email || '',
      contact.phone || '',
      contact.source_system || '',
      new Date(contact.created_at).toLocaleDateString(),
      new Date(contact.updated_at).toLocaleDateString()
    ])

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(field => `"${field}"`).join(','))
    ].join('\n')

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    link.setAttribute('href', url)
    link.setAttribute('download', `contacts_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (loading) {
    return <div className="loading">Loading contacts...</div>
  }

  if (error) {
    return (
      <div className="error">
        <h3>Error loading contacts</h3>
        <p>{error}</p>
        <button onClick={fetchContacts}>Retry</button>
      </div>
    )
  }

  return (
    <div className="contacts-container">
      <header className="contacts-header">
        <div className="contacts-header-left">
          <h1>Contacts</h1>
          <p className="contacts-count">
            Showing {contacts.length} of {totalCount.toLocaleString()} contacts
          </p>
        </div>
        <div className="contacts-header-right">
          <div className="view-toggle">
            <button
              className={`view-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
              title="Table View"
            >
              ☰ List
            </button>
            <button
              className={`view-btn ${viewMode === 'cards' ? 'active' : ''}`}
              onClick={() => setViewMode('cards')}
              title="Card View"
            >
              ⊞ Cards
            </button>
          </div>
          {contacts.length > 0 && (
            <button className="export-btn" onClick={exportToCSV}>
              Export to CSV
            </button>
          )}
        </div>
      </header>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search by name or email..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="filters-bar">
        <div className="filter-group">
          <label htmlFor="product-filter">Product:</label>
          <select
            id="product-filter"
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            className="filter-select"
            disabled={availableProducts.length === 0}
          >
            <option value="">All Products</option>
            {availableProducts.map(product => (
              <option key={product.id} value={product.id}>{product.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Tags:</label>
          <div className="multi-select-wrapper">
            <button
              className="multi-select-button"
              onClick={() => setShowTagDropdown(!showTagDropdown)}
              disabled={availableTags.length === 0}
            >
              {selectedTags.length === 0
                ? 'All Tags'
                : `${selectedTags.length} tag${selectedTags.length > 1 ? 's' : ''} selected`}
            </button>
            {showTagDropdown && availableTags.length > 0 && (
              <div className="multi-select-dropdown">
                <div className="multi-select-options">
                  {availableTags.map(tag => (
                    <label key={tag.id} className="multi-select-option">
                      <input
                        type="checkbox"
                        checked={selectedTags.includes(tag.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTags([...selectedTags, tag.id])
                          } else {
                            setSelectedTags(selectedTags.filter(id => id !== tag.id))
                          }
                        }}
                      />
                      <span>{tag.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="filter-group">
          <label htmlFor="subscription-filter">Subscription Status:</label>
          <select
            id="subscription-filter"
            value={selectedSubscription}
            onChange={(e) => setSelectedSubscription(e.target.value)}
            className="filter-select"
            disabled={availableSubscriptions.length === 0}
          >
            <option value="">All Statuses</option>
            {availableSubscriptions.map(sub => (
              <option key={sub} value={sub}>{sub}</option>
            ))}
          </select>
        </div>

        {(selectedTags.length > 0 || selectedSubscription || selectedProduct) && (
          <button
            className="clear-filters-btn"
            onClick={() => {
              setSelectedTags([])
              setSelectedSubscription('')
              setSelectedProduct('')
              setShowTagDropdown(false)
            }}
          >
            Clear Filters
          </button>
        )}
      </div>

      <div className="contacts-list">
        {contacts.length === 0 ? (
          <div className="no-results">
            {searchTerm ? 'No contacts found matching your search.' : 'No contacts yet.'}
          </div>
        ) : viewMode === 'table' ? (
          <table className="contacts-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Membership</th>
                <th>Source</th>
                <th>Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map((contact) => (
                <tr
                  key={contact.id}
                  className="contact-row"
                  onClick={() => setSelectedContact(contact)}
                >
                  <td className="contact-name-cell">
                    <div className="contact-avatar-small">
                      {(contact.first_name?.[0] || contact.email?.[0] || '?').toUpperCase()}
                    </div>
                    <span>
                      {contact.first_name || contact.last_name
                        ? `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
                        : 'No name'}
                    </span>
                  </td>
                  <td className="contact-email-cell">{contact.email}</td>
                  <td className="contact-membership-cell">
                    {contact.membership_group && (
                      <span className={`membership-badge ${contact.membership_group.toLowerCase().replace(' ', '-')}`}>
                        {contact.membership_level || contact.membership_group}
                      </span>
                    )}
                  </td>
                  <td className="contact-source-cell">
                    {contact.source_system && (
                      <span className="contact-source-badge">{contact.source_system}</span>
                    )}
                  </td>
                  <td className="contact-date-cell">
                    {new Date(contact.updated_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="contacts-cards">
            {contacts.map((contact) => (
              <div
                key={contact.id}
                className={`contact-card ${contact.membership_group ? 'has-membership' : ''} ${contact.membership_group?.toLowerCase().replace(' ', '-') || ''}`}
                onClick={() => setSelectedContact(contact)}
              >
                <div className="card-header">
                  <div className="contact-avatar">
                    {(contact.first_name?.[0] || contact.email?.[0] || '?').toUpperCase()}
                  </div>
                  <div className="card-header-text">
                    <h3 className="contact-card-name">
                      {contact.first_name || contact.last_name
                        ? `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
                        : 'No name'}
                    </h3>
                    <p className="contact-card-email">{contact.email}</p>
                  </div>
                </div>

                <div className="card-body">
                  {contact.membership_group && (
                    <div className="card-row membership-row">
                      <span className="card-label">Membership:</span>
                      <span className={`membership-badge ${contact.membership_group.toLowerCase().replace(' ', '-')}`}>
                        {contact.membership_level || contact.membership_group}
                      </span>
                    </div>
                  )}

                  {contact.paypal_business_name && (
                    <div className="card-row">
                      <span className="card-label">Business:</span>
                      <span>{contact.paypal_business_name}</span>
                    </div>
                  )}

                  {contact.shipping_city && contact.shipping_state && (
                    <div className="card-row">
                      <span className="card-label">Location:</span>
                      <span>{contact.shipping_city}, {contact.shipping_state}</span>
                    </div>
                  )}

                  {(contact.phone || contact.paypal_phone) && (
                    <div className="card-row">
                      <span className="card-label">Phone:</span>
                      <span>{contact.phone || contact.paypal_phone}</span>
                    </div>
                  )}

                  {contact.paypal_subscription_reference && (
                    <div className="card-row">
                      <span className="card-label">Subscription:</span>
                      <span className="badge-active">Active</span>
                    </div>
                  )}
                </div>

                <div className="card-footer">
                  <span className="contact-source-badge">{contact.source_system || 'Unknown'}</span>
                  <span className="card-date">Updated {new Date(contact.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {hasMore && contacts.length > 0 && (
        <div className="load-more-container">
          <button
            className="load-more-btn"
            onClick={handleLoadMore}
            disabled={loadingMore}
          >
            {loadingMore ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}

      {selectedContact && (
        <div className="modal-overlay" onClick={() => setSelectedContact(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedContact(null)}>×</button>
            <h2>Contact Details</h2>
            <div className="detail-grid">
              <div className="detail-item">
                <label>Name</label>
                <p>{selectedContact.first_name || selectedContact.last_name
                  ? `${selectedContact.first_name || ''} ${selectedContact.last_name || ''}`.trim()
                  : 'No name'}</p>
              </div>
              <div className="detail-item">
                <label>Email</label>
                <p>{selectedContact.email}</p>
              </div>

              {selectedContact.membership_group && (
                <>
                  <div className="detail-item">
                    <label>Membership Group</label>
                    <p><span className={`membership-badge ${selectedContact.membership_group.toLowerCase().replace(' ', '-')}`}>
                      {selectedContact.membership_group}
                    </span></p>
                  </div>
                  {selectedContact.membership_level && (
                    <div className="detail-item">
                      <label>Membership Level</label>
                      <p>{selectedContact.membership_level}</p>
                    </div>
                  )}
                  {selectedContact.membership_tier && (
                    <div className="detail-item">
                      <label>Membership Tier</label>
                      <p>{selectedContact.membership_tier}</p>
                    </div>
                  )}
                </>
              )}

              {(selectedContact.phone || selectedContact.paypal_phone) && (
                <div className="detail-item">
                  <label>Phone</label>
                  <p>{selectedContact.phone || selectedContact.paypal_phone}</p>
                </div>
              )}

              {selectedContact.paypal_business_name && (
                <div className="detail-item">
                  <label>Business Name</label>
                  <p>{selectedContact.paypal_business_name}</p>
                </div>
              )}

              {selectedContact.shipping_address_line_1 && (
                <>
                  <div className="detail-item full-width">
                    <label>Shipping Address</label>
                    <p>
                      {selectedContact.shipping_address_line_1}<br />
                      {selectedContact.shipping_address_line_2 && <>{selectedContact.shipping_address_line_2}<br /></>}
                      {selectedContact.shipping_city}, {selectedContact.shipping_state} {selectedContact.shipping_postal_code}<br />
                      {selectedContact.shipping_country}
                    </p>
                  </div>
                </>
              )}

              {selectedContact.paypal_subscription_reference && (
                <div className="detail-item">
                  <label>PayPal Subscription</label>
                  <p><span className="badge-active">Active</span></p>
                </div>
              )}

              <div className="detail-item">
                <label>Source System</label>
                <p>{selectedContact.source_system || 'Unknown'}</p>
              </div>
              {selectedContact.kajabi_id && (
                <div className="detail-item">
                  <label>Kajabi ID</label>
                  <p>{selectedContact.kajabi_id}</p>
                </div>
              )}
              {selectedContact.ticket_tailor_id && (
                <div className="detail-item">
                  <label>Ticket Tailor ID</label>
                  <p>{selectedContact.ticket_tailor_id}</p>
                </div>
              )}
              <div className="detail-item">
                <label>Created</label>
                <p>{new Date(selectedContact.created_at).toLocaleDateString()}</p>
              </div>
              <div className="detail-item">
                <label>Last Updated</label>
                <p>{new Date(selectedContact.updated_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
