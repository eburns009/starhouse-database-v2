import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import Button from '../ui/Button'
import Modal from '../ui/Modal'
import ConfirmDialog from '../ui/ConfirmDialog'
import { useToast } from '../../hooks/useToast'
import Toast from '../ui/Toast'
import { formatCurrency, formatDate } from '../../lib/utils'

export default function DuplicateDetection({ isOpen, onClose, onResolved }) {
  const [duplicateGroups, setDuplicateGroups] = useState([])
  const [selectedGroup, setSelectedGroup] = useState(null)
  const [contactDetails, setContactDetails] = useState([])
  const [selectedMaster, setSelectedMaster] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showMergeConfirm, setShowMergeConfirm] = useState(false)
  const [isMerging, setIsMerging] = useState(false)

  const { success, error: showError, toasts, removeToast } = useToast()

  useEffect(() => {
    if (isOpen) {
      fetchDuplicates()
    }
  }, [isOpen])

  async function fetchDuplicates() {
    try {
      setLoading(true)

      const { data, error } = await supabase
        .from('v_potential_duplicate_contacts')
        .select('*')
        .order('contact_count', { ascending: false })

      if (error) throw error

      setDuplicateGroups(data || [])
    } catch (err) {
      console.error('Error fetching duplicates:', err)
      showError('Failed to load duplicate contacts')
    } finally {
      setLoading(false)
    }
  }

  async function loadGroupDetails(group) {
    try {
      setLoading(true)
      setSelectedGroup(group)

      const { data, error } = await supabase
        .from('v_contact_detail_enriched')
        .select('*')
        .in('id', group.contact_ids)

      if (error) throw error

      setContactDetails(data || [])
      // Auto-select the contact with highest revenue as master
      if (data && data.length > 0) {
        const master = data.reduce((max, contact) =>
          (contact.total_spent || 0) > (max.total_spent || 0) ? contact : max
        )
        setSelectedMaster(master.id)
      }
    } catch (err) {
      console.error('Error loading contact details:', err)
      showError('Failed to load contact details')
    } finally {
      setLoading(false)
    }
  }

  function closeGroupView() {
    setSelectedGroup(null)
    setContactDetails([])
    setSelectedMaster(null)
  }

  async function handleMerge() {
    if (!selectedMaster) {
      showError('Please select a master contact to keep')
      return
    }

    try {
      setIsMerging(true)

      const duplicatesToDelete = contactDetails
        .filter(c => c.id !== selectedMaster)
        .map(c => c.id)

      // Delete duplicate contacts
      const { error: deleteError } = await supabase
        .from('contacts')
        .delete()
        .in('id', duplicatesToDelete)

      if (deleteError) throw deleteError

      success(`Merged ${duplicatesToDelete.length} duplicate contact${duplicatesToDelete.length > 1 ? 's' : ''} into one`)

      // Refresh the list
      await fetchDuplicates()
      closeGroupView()
      setShowMergeConfirm(false)
      onResolved?.()
    } catch (err) {
      console.error('Error merging contacts:', err)
      showError('Failed to merge contacts: ' + err.message)
    } finally {
      setIsMerging(false)
    }
  }

  async function handleMarkNotDuplicate() {
    try {
      setLoading(true)

      // Add a suffix to all emails except the first one to break the duplicate
      const updates = contactDetails.slice(1).map((contact, index) => ({
        id: contact.id,
        primary_email: `${contact.primary_email.split('@')[0]}+${index + 1}@${contact.primary_email.split('@')[1]}`
      }))

      for (const update of updates) {
        const { error } = await supabase
          .from('contacts')
          .update({ primary_email: update.primary_email })
          .eq('id', update.id)

        if (error) throw error
      }

      success('Contacts marked as not duplicates')
      await fetchDuplicates()
      closeGroupView()
      onResolved?.()
    } catch (err) {
      console.error('Error marking as not duplicate:', err)
      showError('Failed to mark as not duplicate: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="Duplicate Contact Detection"
        size="large"
      >
        <div style={{ minWidth: '700px' }}>
          {loading && !selectedGroup ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
              <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
              <p>Loading duplicate contacts...</p>
            </div>
          ) : selectedGroup ? (
            // Detail view - show group comparison
            <div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px',
                paddingBottom: '12px',
                borderBottom: '2px solid #e5e7eb'
              }}>
                <div>
                  <Button variant="ghost" size="sm" onClick={closeGroupView}>
                    ← Back to List
                  </Button>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginTop: '8px' }}>
                    {selectedGroup.email}
                  </h3>
                  <p style={{ fontSize: '14px', color: '#6b7280' }}>
                    {selectedGroup.contact_count} contacts with same email
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleMarkNotDuplicate}
                    disabled={loading}
                  >
                    Not Duplicates
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setShowMergeConfirm(true)}
                    disabled={!selectedMaster}
                  >
                    Merge Selected
                  </Button>
                </div>
              </div>

              {/* Contact comparison cards */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '16px',
                maxHeight: '500px',
                overflowY: 'auto'
              }}>
                {contactDetails.map(contact => (
                  <div
                    key={contact.id}
                    onClick={() => setSelectedMaster(contact.id)}
                    style={{
                      border: selectedMaster === contact.id ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                      borderRadius: '8px',
                      padding: '16px',
                      cursor: 'pointer',
                      backgroundColor: selectedMaster === contact.id ? '#eff6ff' : 'white',
                      transition: 'all 0.2s'
                    }}
                  >
                    {selectedMaster === contact.id && (
                      <div style={{
                        display: 'inline-block',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        fontSize: '11px',
                        fontWeight: '600',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        marginBottom: '8px'
                      }}>
                        MASTER
                      </div>
                    )}

                    <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
                      {contact.first_name} {contact.last_name}
                    </h4>

                    <div style={{ fontSize: '13px', color: '#4b5563' }}>
                      <div style={{ marginBottom: '6px' }}>
                        <strong>Email:</strong> {contact.primary_email}
                      </div>
                      {contact.phone && (
                        <div style={{ marginBottom: '6px' }}>
                          <strong>Phone:</strong> {contact.phone}
                        </div>
                      )}
                      <div style={{ marginBottom: '6px' }}>
                        <strong>Revenue:</strong> {formatCurrency(contact.total_spent)}
                      </div>
                      <div style={{ marginBottom: '6px' }}>
                        <strong>Transactions:</strong> {contact.transaction_count_actual || 0}
                      </div>
                      <div style={{ marginBottom: '6px' }}>
                        <strong>Last Transaction:</strong> {formatDate(contact.last_transaction_date)}
                      </div>
                      {contact.address_line_1 && (
                        <div style={{ marginBottom: '6px' }}>
                          <strong>Address:</strong> {contact.city}, {contact.state}
                        </div>
                      )}
                      <div style={{ marginBottom: '6px' }}>
                        <strong>Source:</strong> {contact.source_system || 'Unknown'}
                      </div>
                      <div style={{ marginBottom: '6px' }}>
                        <strong>Created:</strong> {formatDate(contact.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{
                marginTop: '16px',
                padding: '12px',
                backgroundColor: '#fef3c7',
                border: '1px solid #fbbf24',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#78350f'
              }}>
                <strong>Note:</strong> Click on a contact card to select it as the master record.
                When you merge, the master record will be kept and all others will be deleted.
              </div>
            </div>
          ) : duplicateGroups.length === 0 ? (
            // No duplicates found
            <div style={{
              textAlign: 'center',
              padding: '60px 20px',
              color: '#6b7280'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>✓</div>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                No Duplicates Found
              </h3>
              <p style={{ fontSize: '14px' }}>
                All contacts have unique email addresses.
              </p>
            </div>
          ) : (
            // List view - show all duplicate groups
            <div>
              <p style={{ marginBottom: '16px', color: '#6b7280', fontSize: '14px' }}>
                Found {duplicateGroups.length} group{duplicateGroups.length > 1 ? 's' : ''} of potential duplicate contacts
              </p>

              <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                {duplicateGroups.map((group, index) => (
                  <div
                    key={index}
                    onClick={() => loadGroupDetails(group)}
                    style={{
                      padding: '16px',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      marginBottom: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#3b82f6'
                      e.currentTarget.style.backgroundColor = '#f8fafc'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#e5e7eb'
                      e.currentTarget.style.backgroundColor = 'white'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                        {group.email}
                      </div>
                      <div style={{ fontSize: '14px', color: '#6b7280' }}>
                        {group.contact_count} duplicate contact{group.contact_count > 1 ? 's' : ''}
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Review →
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Close button at bottom when viewing list */}
          {!selectedGroup && duplicateGroups.length > 0 && (
            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              marginTop: '20px',
              paddingTop: '16px',
              borderTop: '1px solid #e5e7eb'
            }}>
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            </div>
          )}
        </div>
      </Modal>

      {/* Merge Confirmation */}
      <ConfirmDialog
        isOpen={showMergeConfirm}
        onClose={() => setShowMergeConfirm(false)}
        onConfirm={handleMerge}
        title="Merge Duplicate Contacts?"
        message={`This will delete ${contactDetails.length - 1} duplicate contact${contactDetails.length - 1 > 1 ? 's' : ''} and keep only the selected master record. This action cannot be undone.`}
        confirmText="Merge Contacts"
        cancelText="Cancel"
        variant="danger"
        isLoading={isMerging}
      />

      {/* Toast Notifications */}
      <Toast toasts={toasts} onClose={removeToast} />
    </>
  )
}
