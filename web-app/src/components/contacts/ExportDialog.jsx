import { useState } from 'react'
import { supabase } from '../../lib/supabase'
import Modal from '../ui/Modal'
import Button from '../ui/Button'
import Checkbox from '../ui/Checkbox'
import { useToast } from '../../hooks/useToast'
import Toast from '../ui/Toast'
import { downloadFile } from '../../lib/utils'
import Papa from 'papaparse'
import * as XLSX from 'xlsx'

const AVAILABLE_FIELDS = [
  { key: 'first_name', label: 'First Name', default: true },
  { key: 'last_name', label: 'Last Name', default: true },
  { key: 'primary_email', label: 'Email', default: true },
  { key: 'phone', label: 'Phone', default: true },
  { key: 'address_line_1', label: 'Address Line 1', default: false },
  { key: 'address_line_2', label: 'Address Line 2', default: false },
  { key: 'city', label: 'City', default: false },
  { key: 'state', label: 'State', default: false },
  { key: 'postal_code', label: 'Postal Code', default: false },
  { key: 'shipping_address_line_1', label: 'Shipping Address 1', default: false },
  { key: 'shipping_city', label: 'Shipping City', default: false },
  { key: 'shipping_state', label: 'Shipping State', default: false },
  { key: 'shipping_postal_code', label: 'Shipping Postal', default: false },
  { key: 'total_spent', label: 'Total Revenue', default: true },
  { key: 'transaction_count_actual', label: 'Transaction Count', default: true },
  { key: 'first_transaction_date', label: 'First Transaction', default: false },
  { key: 'last_transaction_date', label: 'Last Transaction', default: true },
  { key: 'has_active_subscription', label: 'Active Subscription', default: true },
  { key: 'membership_level', label: 'Membership Level', default: false },
  { key: 'source_system', label: 'Source System', default: false },
  { key: 'created_at', label: 'Created Date', default: false },
  { key: 'updated_at', label: 'Updated Date', default: false }
]

export default function ExportDialog({
  isOpen,
  onClose,
  selectedIds = [],
  currentFilters = {}
}) {
  const [selectedFields, setSelectedFields] = useState(
    AVAILABLE_FIELDS.filter(f => f.default).map(f => f.key)
  )
  const [exportFormat, setExportFormat] = useState('csv')
  const [exportScope, setExportScope] = useState(selectedIds.length > 0 ? 'selected' : 'all')
  const [isExporting, setIsExporting] = useState(false)

  const { success, error: showError, toasts, removeToast } = useToast()

  function toggleField(fieldKey) {
    setSelectedFields(prev => {
      if (prev.includes(fieldKey)) {
        return prev.filter(k => k !== fieldKey)
      } else {
        return [...prev, fieldKey]
      }
    })
  }

  function selectAllFields() {
    setSelectedFields(AVAILABLE_FIELDS.map(f => f.key))
  }

  function selectDefaultFields() {
    setSelectedFields(AVAILABLE_FIELDS.filter(f => f.default).map(f => f.key))
  }

  async function fetchContactsForExport() {
    let query = supabase.from('v_contact_list_optimized').select('*')

    // Apply scope
    if (exportScope === 'selected' && selectedIds.length > 0) {
      query = query.in('id', selectedIds)
    }

    // Apply filters
    if (currentFilters.search) {
      query = query.or(`first_name.ilike.%${currentFilters.search}%,last_name.ilike.%${currentFilters.search}%,primary_email.ilike.%${currentFilters.search}%`)
    }

    if (currentFilters.dateFrom) {
      query = query.gte('last_transaction_date', currentFilters.dateFrom)
    }

    if (currentFilters.dateTo) {
      query = query.lte('last_transaction_date', currentFilters.dateTo)
    }

    if (currentFilters.amountMin) {
      query = query.gte('total_spent', parseFloat(currentFilters.amountMin))
    }

    if (currentFilters.amountMax) {
      query = query.lte('total_spent', parseFloat(currentFilters.amountMax))
    }

    if (currentFilters.sourceSystem) {
      query = query.eq('source_system', currentFilters.sourceSystem)
    }

    if (currentFilters.hasActiveSubscription !== undefined && currentFilters.hasActiveSubscription !== '') {
      query = query.eq('has_active_subscription', currentFilters.hasActiveSubscription === 'true')
    }

    // Order by last transaction date
    query = query.order('last_transaction_date', { ascending: false, nullsFirst: false })

    const { data, error } = await query

    if (error) throw error
    return data || []
  }

  function filterContactData(contacts) {
    return contacts.map(contact => {
      const filtered = {}
      selectedFields.forEach(fieldKey => {
        const field = AVAILABLE_FIELDS.find(f => f.key === fieldKey)
        if (field) {
          filtered[field.label] = contact[fieldKey] ?? ''
        }
      })
      return filtered
    })
  }

  async function handleExport() {
    if (selectedFields.length === 0) {
      showError('Please select at least one field to export')
      return
    }

    try {
      setIsExporting(true)

      // Fetch contacts
      const contacts = await fetchContactsForExport()

      if (contacts.length === 0) {
        showError('No contacts to export')
        return
      }

      // Filter to selected fields
      const exportData = filterContactData(contacts)

      // Generate file based on format
      if (exportFormat === 'csv') {
        const csv = Papa.unparse(exportData)
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const filename = `contacts_export_${new Date().toISOString().split('T')[0]}.csv`
        downloadFile(blob, filename)
      } else {
        // Excel export
        const worksheet = XLSX.utils.json_to_sheet(exportData)
        const workbook = XLSX.utils.book_new()
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Contacts')

        // Generate buffer
        const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
        const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const filename = `contacts_export_${new Date().toISOString().split('T')[0]}.xlsx`
        downloadFile(blob, filename)
      }

      success(`Exported ${contacts.length} contact${contacts.length > 1 ? 's' : ''} to ${exportFormat.toUpperCase()}`)
      onClose()
    } catch (err) {
      console.error('Error exporting contacts:', err)
      showError('Failed to export contacts: ' + err.message)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title="Export Contacts">
        <div style={{ minWidth: '500px' }}>
          {/* Export Scope */}
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>
              Export Scope
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="exportScope"
                  value="selected"
                  checked={exportScope === 'selected'}
                  onChange={(e) => setExportScope(e.target.value)}
                  disabled={selectedIds.length === 0}
                  style={{ marginRight: '8px' }}
                />
                <span style={{ fontSize: '14px' }}>
                  Selected contacts only ({selectedIds.length} selected)
                </span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="exportScope"
                  value="all"
                  checked={exportScope === 'all'}
                  onChange={(e) => setExportScope(e.target.value)}
                  style={{ marginRight: '8px' }}
                />
                <span style={{ fontSize: '14px' }}>
                  All contacts (with current filters)
                </span>
              </label>
            </div>
          </div>

          {/* Export Format */}
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>
              Format
            </h3>
            <div style={{ display: 'flex', gap: '12px' }}>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="exportFormat"
                  value="csv"
                  checked={exportFormat === 'csv'}
                  onChange={(e) => setExportFormat(e.target.value)}
                  style={{ marginRight: '8px' }}
                />
                <span style={{ fontSize: '14px' }}>CSV</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="exportFormat"
                  value="xlsx"
                  checked={exportFormat === 'xlsx'}
                  onChange={(e) => setExportFormat(e.target.value)}
                  style={{ marginRight: '8px' }}
                />
                <span style={{ fontSize: '14px' }}>Excel (.xlsx)</span>
              </label>
            </div>
          </div>

          {/* Field Selection */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '12px'
            }}>
              <h3 style={{ fontSize: '14px', fontWeight: '600' }}>
                Fields to Export ({selectedFields.length}/{AVAILABLE_FIELDS.length})
              </h3>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={selectDefaultFields}
                  style={{
                    fontSize: '12px',
                    color: '#3b82f6',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  Default
                </button>
                <button
                  onClick={selectAllFields}
                  style={{
                    fontSize: '12px',
                    color: '#3b82f6',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  All
                </button>
              </div>
            </div>
            <div style={{
              maxHeight: '300px',
              overflowY: 'auto',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '12px'
            }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '8px'
              }}>
                {AVAILABLE_FIELDS.map(field => (
                  <label
                    key={field.key}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '6px 8px',
                      cursor: 'pointer',
                      borderRadius: '4px',
                      transition: 'background-color 0.15s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <input
                      type="checkbox"
                      checked={selectedFields.includes(field.key)}
                      onChange={() => toggleField(field.key)}
                      style={{ marginRight: '8px' }}
                    />
                    <span style={{ fontSize: '14px' }}>{field.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '8px',
            paddingTop: '16px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isExporting}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleExport}
              disabled={isExporting || selectedFields.length === 0}
            >
              {isExporting ? 'Exporting...' : `Export ${exportFormat.toUpperCase()}`}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Toast Notifications */}
      <Toast toasts={toasts} onClose={removeToast} />
    </>
  )
}
