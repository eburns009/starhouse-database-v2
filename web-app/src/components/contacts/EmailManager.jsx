import { useState } from 'react'
import { supabase } from '../../lib/supabase'
import { EMAIL_TYPES } from '../../types/contacts'
import './EmailManager.css'

export default function EmailManager({ contactId, emails, onUpdate }) {
  const [isAdding, setIsAdding] = useState(false)
  const [newEmail, setNewEmail] = useState({
    email: '',
    email_type: 'personal',
    is_primary: false,
    is_outreach: false,
    verified: false
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  async function handleAddEmail(e) {
    e.preventDefault()
    try {
      setSaving(true)
      setError(null)

      const { data, error: insertError } = await supabase
        .from('contact_emails')
        .insert({
          contact_id: contactId,
          email: newEmail.email,
          email_type: newEmail.email_type,
          is_primary: newEmail.is_primary,
          is_outreach: newEmail.is_outreach,
          source: 'manual',
          verified: newEmail.verified
        })
        .select()

      if (insertError) throw insertError

      setNewEmail({
        email: '',
        email_type: 'personal',
        is_primary: false,
        is_outreach: false,
        verified: false
      })
      setIsAdding(false)

      // Refresh parent
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Error adding email:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleSetPrimary(emailId) {
    try {
      // This would require updating the old primary first
      // For now, just show a message
      alert('To change primary email, please use the Update button and check the "Primary" box')
    } catch (err) {
      console.error('Error setting primary:', err)
      setError(err.message)
    }
  }

  async function handleDeleteEmail(emailId, isPrimary) {
    if (isPrimary) {
      alert('Cannot delete primary email. Please set another email as primary first.')
      return
    }

    if (!confirm('Are you sure you want to delete this email?')) {
      return
    }

    try {
      const { error: deleteError } = await supabase
        .from('contact_emails')
        .delete()
        .eq('id', emailId)
        .eq('contact_id', contactId)

      if (deleteError) throw deleteError

      // Refresh parent
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Error deleting email:', err)
      setError(err.message)
    }
  }

  return (
    <div className="email-manager">
      <div className="manager-header">
        <h3>Email Addresses</h3>
        {!isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="btn-add"
          >
            + Add Email
          </button>
        )}
      </div>

      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Add Email Form */}
      {isAdding && (
        <form onSubmit={handleAddEmail} className="add-email-form">
          <div className="form-group">
            <label>Email Address *</label>
            <input
              type="email"
              value={newEmail.email}
              onChange={(e) => setNewEmail({ ...newEmail, email: e.target.value })}
              required
              placeholder="user@example.com"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Type</label>
            <select
              value={newEmail.email_type}
              onChange={(e) => setNewEmail({ ...newEmail, email_type: e.target.value })}
              className="form-input"
            >
              <option value="personal">Personal</option>
              <option value="work">Work</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="form-checkboxes">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={newEmail.is_primary}
                onChange={(e) => setNewEmail({ ...newEmail, is_primary: e.target.checked })}
              />
              <span>Set as primary email</span>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={newEmail.is_outreach}
                onChange={(e) => setNewEmail({ ...newEmail, is_outreach: e.target.checked })}
              />
              <span>Use for outreach</span>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={newEmail.verified}
                onChange={(e) => setNewEmail({ ...newEmail, verified: e.target.checked })}
              />
              <span>Verified</span>
            </label>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              disabled={saving}
              className="btn-save"
            >
              {saving ? 'Saving...' : 'Add Email'}
            </button>
            <button
              type="button"
              onClick={() => {
                setIsAdding(false)
                setError(null)
              }}
              className="btn-cancel"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Email List */}
      <div className="email-list">
        {(!emails || emails.length === 0) ? (
          <div className="empty-state">
            <p>No emails found</p>
          </div>
        ) : (
          emails.map((email, idx) => (
            <div key={idx} className="email-card">
              <div className="email-info">
                <div className="email-address">
                  {email.email}
                  {email.is_primary && (
                    <span className="badge badge-primary">Primary</span>
                  )}
                  {email.is_outreach && (
                    <span className="badge badge-outreach">Outreach</span>
                  )}
                </div>
                <div className="email-meta">
                  <span className="meta-item">
                    <strong>Type:</strong> {email.email_type || email.type || 'personal'}
                  </span>
                  <span className="meta-item">
                    <strong>Source:</strong> {email.source || 'unknown'}
                  </span>
                  {email.verified ? (
                    <span className="meta-item status-verified">✓ Verified</span>
                  ) : (
                    <span className="meta-item status-unverified">Not verified</span>
                  )}
                  {email.deliverable !== null && (
                    <span className={`meta-item ${email.deliverable ? 'status-deliverable' : 'status-bounced'}`}>
                      {email.deliverable ? '✓ Deliverable' : '✗ Bounced'}
                    </span>
                  )}
                </div>
              </div>
              <div className="email-actions">
                {!email.is_primary && (
                  <>
                    <button
                      onClick={() => handleSetPrimary(email.id)}
                      className="btn-action"
                      title="Set as primary"
                    >
                      Set Primary
                    </button>
                    <button
                      onClick={() => handleDeleteEmail(email.id, email.is_primary)}
                      className="btn-action btn-danger"
                      title="Delete email"
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
