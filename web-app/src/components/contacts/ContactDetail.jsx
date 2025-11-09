import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { useToast } from '../../hooks/useToast'
import { useKeyboard } from '../../hooks/useKeyboard'
import ActivityTimeline from './ActivityTimeline'
import EmailManager from './EmailManager'
import NotesPanel from './NotesPanel'
import ContactEditForm from './ContactEditForm'
import TagsManager from './TagsManager'
import ProgramPartnerActions from './ProgramPartnerActions'
import { ComplianceBadge } from './ProgramPartnerComplianceFilter'
import Button from '../ui/Button'
import ConfirmDialog from '../ui/ConfirmDialog'
import Toast from '../ui/Toast'
import './ContactDetail.css'

export default function ContactDetail({ contactId, onClose, onDeleted }) {
  const [contact, setContact] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [isEditing, setIsEditing] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const { success, error: showError, toasts, removeToast } = useToast()

  // Keyboard shortcuts
  useKeyboard('e', () => !isEditing && setIsEditing(true), { ctrl: true })
  useKeyboard('d', () => !isEditing && setShowDeleteConfirm(true), { ctrl: true })
  useKeyboard('Escape', () => {
    if (isEditing) {
      setIsEditing(false)
    } else {
      onClose()
    }
  })

  useEffect(() => {
    if (contactId) {
      fetchContactDetail()
    }
  }, [contactId])

  async function fetchContactDetail() {
    try {
      setLoading(true)
      setError(null)

      // Fetch from detail view for rich contact info
      const { data: detailData, error: detailError } = await supabase
        .from('v_contact_detail_enriched')
        .select('*')
        .eq('id', contactId)
        .single()

      if (detailError) throw detailError

      // Also fetch compliance fields from list view
      const { data: complianceData, error: complianceError } = await supabase
        .from('v_contact_list_with_subscriptions')
        .select('is_expected_program_partner, partner_compliance_status, partner_compliance_message, payment_method, payment_method_notes')
        .eq('id', contactId)
        .single()

      if (complianceError) console.warn('Failed to fetch compliance data:', complianceError)

      // Merge the data
      setContact({
        ...detailData,
        is_expected_program_partner: complianceData?.is_expected_program_partner,
        partner_compliance_status: complianceData?.partner_compliance_status,
        partner_compliance_message: complianceData?.partner_compliance_message,
        payment_method: complianceData?.payment_method,
        payment_method_notes: complianceData?.payment_method_notes
      })
    } catch (err) {
      console.error('Error fetching contact detail:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    try {
      setIsDeleting(true)

      const { error: deleteError } = await supabase
        .from('contacts')
        .delete()
        .eq('id', contactId)

      if (deleteError) throw deleteError

      success('Contact deleted successfully')

      // Close modal and notify parent
      setTimeout(() => {
        onClose()
        onDeleted?.()
      }, 500)
    } catch (err) {
      console.error('Error deleting contact:', err)
      showError('Failed to delete contact: ' + err.message)
    } finally {
      setIsDeleting(false)
      setShowDeleteConfirm(false)
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
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getRoleBadges = () => {
    if (!contact?.active_roles) return []
    return contact.active_roles.map(role => ({
      label: role.charAt(0).toUpperCase() + role.slice(1),
      role
    }))
  }

  const parseEmails = () => {
    if (!contact?.all_emails) return []
    try {
      return Array.isArray(contact.all_emails) ? contact.all_emails : []
    } catch {
      return []
    }
  }

  if (loading) {
    return (
      <div className="contact-detail-modal">
        <div className="contact-detail-container">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading contact...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="contact-detail-modal">
        <div className="contact-detail-container">
          <div className="error-container">
            <h2>Error</h2>
            <p>{error}</p>
            <button onClick={onClose} className="btn-primary">Close</button>
          </div>
        </div>
      </div>
    )
  }

  if (!contact) {
    return null
  }

  return (
    <div className="contact-detail-modal" onClick={onClose}>
      <div className="contact-detail-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="contact-header">
          <div className="header-left">
            <h1>
              {contact.first_name} {contact.last_name}
              {contact.has_active_subscription && (
                <span className="subscription-indicator">✓</span>
              )}
            </h1>
            <p className="primary-email">{contact.primary_email}</p>
            <div className="role-badges">
              {getRoleBadges().map((badge, idx) => (
                <span key={idx} className={`role-badge role-${badge.role}`}>
                  {badge.label}
                </span>
              ))}
              {/* Program Partner Compliance Badge */}
              {contact.is_expected_program_partner && (
                <ComplianceBadge
                  status={contact.partner_compliance_status}
                  message={contact.partner_compliance_message}
                />
              )}
            </div>
          </div>
          <div className="header-right">
            {isEditing ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(false)}
                  style={{ marginRight: '8px' }}
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                {/* Program Partner Actions */}
                <ProgramPartnerActions
                  contact={contact}
                  onUpdate={fetchContactDetail}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(true)}
                  style={{ marginLeft: '8px', marginRight: '8px' }}
                >
                  ✏️ Edit
                </Button>
              </>
            )}
            <button onClick={onClose} className="btn-close">✕</button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="quick-stats">
          <div className="stat-card">
            <div className="stat-label">Total Revenue</div>
            <div className="stat-value">{formatCurrency(contact.total_spent)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Transactions</div>
            <div className="stat-value">{contact.transaction_count_actual || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tags</div>
            <div className="stat-value">{contact.tag_count || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Notes</div>
            <div className="stat-value">{contact.note_count || 0}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs-container">
          <div className="tabs-header">
            <button
              className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`tab-button ${activeTab === 'activity' ? 'active' : ''}`}
              onClick={() => setActiveTab('activity')}
            >
              Activity
            </button>
            <button
              className={`tab-button ${activeTab === 'emails' ? 'active' : ''}`}
              onClick={() => setActiveTab('emails')}
            >
              Emails ({parseEmails().length})
            </button>
            <button
              className={`tab-button ${activeTab === 'notes' ? 'active' : ''}`}
              onClick={() => setActiveTab('notes')}
            >
              Notes ({contact.note_count || 0})
            </button>
          </div>

          <div className="tabs-content">
            {/* OVERVIEW TAB */}
            {activeTab === 'overview' && (
              <div className="tab-panel">
                {isEditing ? (
                  /* Edit Mode */
                  <ContactEditForm
                    contact={contact}
                    onSuccess={(updatedContact) => {
                      setContact(updatedContact)
                      setIsEditing(false)
                      success('Contact updated successfully!')
                      fetchContactDetail()
                    }}
                    onCancel={() => setIsEditing(false)}
                  />
                ) : (
                  <>
                    {/* Contact Information */}
                    <div className="info-section">
                  <h3>Contact Information</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>Full Name</label>
                      <div>{contact.first_name} {contact.last_name}</div>
                    </div>
                    <div className="info-item">
                      <label>Primary Email</label>
                      <div>{contact.primary_email || '—'}</div>
                    </div>
                    <div className="info-item">
                      <label>Outreach Email</label>
                      <div>
                        {contact.outreach_email}
                        <span className="email-source">({contact.outreach_source})</span>
                      </div>
                    </div>
                    <div className="info-item">
                      <label>Phone</label>
                      <div>{contact.phone || '—'}</div>
                    </div>
                  </div>
                </div>

                {/* Addresses */}
                {(contact.address_line_1 || contact.shipping_address_line_1) && (
                  <div className="info-section">
                    <h3>Addresses</h3>
                    <div className="address-grid">
                      {contact.address_line_1 && (
                        <div className="address-card">
                          <div className="address-label">
                            Billing Address
                            {contact.billing_address_verified && (
                              <span className="verified-badge">✓ Verified</span>
                            )}
                          </div>
                          <div className="address-content">
                            {contact.address_line_1}<br />
                            {contact.address_line_2 && <>{contact.address_line_2}<br /></>}
                            {contact.city}, {contact.state} {contact.postal_code}
                          </div>
                        </div>
                      )}
                      {contact.shipping_address_line_1 && (
                        <div className="address-card">
                          <div className="address-label">
                            Shipping Address
                            {contact.shipping_address_verified && (
                              <span className="verified-badge">✓ Verified</span>
                            )}
                          </div>
                          <div className="address-content">
                            {contact.shipping_address_line_1}<br />
                            {contact.shipping_address_line_2 && <>{contact.shipping_address_line_2}<br /></>}
                            {contact.shipping_city}, {contact.shipping_state} {contact.shipping_postal_code}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Membership */}
                {(contact.membership_level || contact.membership_tier) && (
                  <div className="info-section">
                    <h3>Membership</h3>
                    <div className="info-grid">
                      {contact.membership_level && (
                        <div className="info-item">
                          <label>Level</label>
                          <div>{contact.membership_level}</div>
                        </div>
                      )}
                      {contact.membership_tier && (
                        <div className="info-item">
                          <label>Tier</label>
                          <div>{contact.membership_tier}</div>
                        </div>
                      )}
                      <div className="info-item">
                        <label>Status</label>
                        <div>
                          {contact.has_active_subscription ? (
                            <span className="status-active">Active</span>
                          ) : (
                            <span className="status-inactive">Inactive</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Revenue Stats */}
                <div className="info-section">
                  <h3>Revenue Statistics</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>Total Spent</label>
                      <div className="stat-large">{formatCurrency(contact.total_spent)}</div>
                    </div>
                    <div className="info-item">
                      <label>Transaction Count</label>
                      <div className="stat-large">{contact.transaction_count_actual || 0}</div>
                    </div>
                    <div className="info-item">
                      <label>First Transaction</label>
                      <div>{formatDate(contact.first_transaction_date)}</div>
                    </div>
                    <div className="info-item">
                      <label>Last Transaction</label>
                      <div>{formatDate(contact.last_transaction_date)}</div>
                    </div>
                  </div>
                </div>

                {/* System Info */}
                <div className="info-section">
                  <h3>System Information</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>Created</label>
                      <div>{formatDate(contact.created_at)}</div>
                    </div>
                    <div className="info-item">
                      <label>Last Updated</label>
                      <div>{formatDate(contact.updated_at)}</div>
                    </div>
                    <div className="info-item">
                      <label>Last Activity</label>
                      <div>{formatDate(contact.last_activity_at)}</div>
                    </div>
                    <div className="info-item">
                      <label>Source System</label>
                      <div>{contact.source_system || 'Unknown'}</div>
                    </div>
                  </div>
                </div>

                {/* Tags Section */}
                <div className="info-section">
                  <h3>Tags</h3>
                  <TagsManager
                    contactId={contactId}
                    onUpdate={() => {
                      fetchContactDetail()
                      success('Tags updated successfully!')
                    }}
                  />
                </div>

                {/* Danger Zone */}
                <div className="info-section" style={{ borderTop: '2px solid #fee2e2', marginTop: '32px', paddingTop: '24px' }}>
                  <h3 style={{ color: '#dc2626' }}>Danger Zone</h3>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px', backgroundColor: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
                    <div>
                      <div style={{ fontWeight: 600, color: '#991b1b' }}>Delete this contact</div>
                      <div style={{ fontSize: '14px', color: '#7f1d1d', marginTop: '4px' }}>
                        Once you delete a contact, there is no going back. Please be certain.
                      </div>
                    </div>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => setShowDeleteConfirm(true)}
                    >
                      🗑️ Delete Contact
                    </Button>
                  </div>
                </div>
                  </>
                )}
              </div>
            )}

            {/* ACTIVITY TAB */}
            {activeTab === 'activity' && (
              <div className="tab-panel">
                <ActivityTimeline contactId={contactId} />
              </div>
            )}

            {/* EMAILS TAB */}
            {activeTab === 'emails' && (
              <div className="tab-panel">
                <EmailManager
                  contactId={contactId}
                  emails={parseEmails()}
                  onUpdate={fetchContactDetail}
                />
              </div>
            )}

            {/* NOTES TAB */}
            {activeTab === 'notes' && (
              <div className="tab-panel">
                <NotesPanel
                  contactId={contactId}
                  onUpdate={fetchContactDetail}
                />
              </div>
            )}
          </div>
        </div>

        {/* Confirm Delete Dialog */}
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          onClose={() => setShowDeleteConfirm(false)}
          onConfirm={handleDelete}
          title="Delete Contact?"
          message={`Are you sure you want to delete ${contact.first_name} ${contact.last_name}? This action cannot be undone.`}
          confirmText="Delete"
          cancelText="Cancel"
          variant="danger"
          isLoading={isDeleting}
        />

        {/* Toast Notifications */}
        <Toast toasts={toasts} onClose={removeToast} />
      </div>
    </div>
  )
}
