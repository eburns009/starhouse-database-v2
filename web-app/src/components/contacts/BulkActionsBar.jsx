import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import Button from '../ui/Button'
import Select from '../ui/Select'
import Modal from '../ui/Modal'
import ConfirmDialog from '../ui/ConfirmDialog'
import { useToast } from '../../hooks/useToast'
import Toast from '../ui/Toast'

export default function BulkActionsBar({ selectedIds = [], onClearSelection, onActionComplete }) {
  const [showAddTagModal, setShowAddTagModal] = useState(false)
  const [showRemoveTagModal, setShowRemoveTagModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [availableTags, setAvailableTags] = useState([])
  const [selectedTagId, setSelectedTagId] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  const { success, error: showError, toasts, removeToast } = useToast()

  useEffect(() => {
    if (showAddTagModal || showRemoveTagModal) {
      fetchTags()
    }
  }, [showAddTagModal, showRemoveTagModal])

  async function fetchTags() {
    try {
      const { data, error } = await supabase
        .from('tags')
        .select('id, name')
        .order('name')

      if (error) throw error
      setAvailableTags(data || [])
    } catch (err) {
      console.error('Error fetching tags:', err)
      showError('Failed to load tags')
    }
  }

  async function handleAddTag() {
    if (!selectedTagId) {
      showError('Please select a tag')
      return
    }

    try {
      setIsProcessing(true)

      // Create junction table entries for all selected contacts
      const insertData = selectedIds.map(contactId => ({
        contact_id: contactId,
        tag_id: selectedTagId
      }))

      const { error } = await supabase
        .from('contact_tags')
        .upsert(insertData, {
          onConflict: 'contact_id,tag_id',
          ignoreDuplicates: true
        })

      if (error) throw error

      const tagName = availableTags.find(t => t.id === selectedTagId)?.name || 'tag'
      success(`Added ${tagName} to ${selectedIds.length} contact${selectedIds.length > 1 ? 's' : ''}`)

      setShowAddTagModal(false)
      setSelectedTagId('')
      onActionComplete?.()
    } catch (err) {
      console.error('Error adding tags:', err)
      showError('Failed to add tags: ' + err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  async function handleRemoveTag() {
    if (!selectedTagId) {
      showError('Please select a tag')
      return
    }

    try {
      setIsProcessing(true)

      const { error } = await supabase
        .from('contact_tags')
        .delete()
        .in('contact_id', selectedIds)
        .eq('tag_id', selectedTagId)

      if (error) throw error

      const tagName = availableTags.find(t => t.id === selectedTagId)?.name || 'tag'
      success(`Removed ${tagName} from ${selectedIds.length} contact${selectedIds.length > 1 ? 's' : ''}`)

      setShowRemoveTagModal(false)
      setSelectedTagId('')
      onActionComplete?.()
    } catch (err) {
      console.error('Error removing tags:', err)
      showError('Failed to remove tags: ' + err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  async function handleBulkDelete() {
    try {
      setIsProcessing(true)

      const { error } = await supabase
        .from('contacts')
        .delete()
        .in('id', selectedIds)

      if (error) throw error

      success(`Deleted ${selectedIds.length} contact${selectedIds.length > 1 ? 's' : ''}`)

      setShowDeleteConfirm(false)
      onClearSelection?.()
      onActionComplete?.()
    } catch (err) {
      console.error('Error deleting contacts:', err)
      showError('Failed to delete contacts: ' + err.message)
    } finally {
      setIsProcessing(false)
    }
  }

  function handleExport() {
    // Trigger export - will be handled by parent component
    onActionComplete?.('export')
  }

  if (selectedIds.length === 0) return null

  return (
    <>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '12px 16px',
        backgroundColor: '#3b82f6',
        color: 'white',
        borderRadius: '8px',
        marginBottom: '16px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontWeight: '600', fontSize: '14px' }}>
            {selectedIds.length} contact{selectedIds.length > 1 ? 's' : ''} selected
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearSelection}
            style={{ color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}
          >
            Clear Selection
          </Button>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            variant="success"
            size="sm"
            onClick={() => setShowAddTagModal(true)}
          >
            Add Tag
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowRemoveTagModal(true)}
            style={{ backgroundColor: 'white', color: '#3b82f6' }}
          >
            Remove Tag
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            style={{ backgroundColor: 'white', color: '#3b82f6' }}
          >
            Export
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => setShowDeleteConfirm(true)}
          >
            Delete
          </Button>
        </div>
      </div>

      {/* Add Tag Modal */}
      <Modal
        isOpen={showAddTagModal}
        onClose={() => setShowAddTagModal(false)}
        title="Add Tag to Selected Contacts"
      >
        <div style={{ minWidth: '400px' }}>
          <p style={{ marginBottom: '16px', color: '#6b7280' }}>
            Add a tag to {selectedIds.length} selected contact{selectedIds.length > 1 ? 's' : ''}
          </p>

          <Select
            label="Select Tag"
            value={selectedTagId}
            onChange={(e) => setSelectedTagId(e.target.value)}
            options={[
              { value: '', label: 'Choose a tag...' },
              ...availableTags.map(tag => ({ value: tag.id, label: tag.name }))
            ]}
          />

          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '8px',
            marginTop: '20px',
            paddingTop: '16px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <Button
              variant="outline"
              onClick={() => setShowAddTagModal(false)}
              disabled={isProcessing}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleAddTag}
              disabled={!selectedTagId || isProcessing}
            >
              {isProcessing ? 'Adding...' : 'Add Tag'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Remove Tag Modal */}
      <Modal
        isOpen={showRemoveTagModal}
        onClose={() => setShowRemoveTagModal(false)}
        title="Remove Tag from Selected Contacts"
      >
        <div style={{ minWidth: '400px' }}>
          <p style={{ marginBottom: '16px', color: '#6b7280' }}>
            Remove a tag from {selectedIds.length} selected contact{selectedIds.length > 1 ? 's' : ''}
          </p>

          <Select
            label="Select Tag"
            value={selectedTagId}
            onChange={(e) => setSelectedTagId(e.target.value)}
            options={[
              { value: '', label: 'Choose a tag...' },
              ...availableTags.map(tag => ({ value: tag.id, label: tag.name }))
            ]}
          />

          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '8px',
            marginTop: '20px',
            paddingTop: '16px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <Button
              variant="outline"
              onClick={() => setShowRemoveTagModal(false)}
              disabled={isProcessing}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleRemoveTag}
              disabled={!selectedTagId || isProcessing}
            >
              {isProcessing ? 'Removing...' : 'Remove Tag'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleBulkDelete}
        title="Delete Selected Contacts?"
        message={`Are you sure you want to delete ${selectedIds.length} contact${selectedIds.length > 1 ? 's' : ''}? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isProcessing}
      />

      {/* Toast Notifications */}
      <Toast toasts={toasts} onClose={removeToast} />
    </>
  )
}
