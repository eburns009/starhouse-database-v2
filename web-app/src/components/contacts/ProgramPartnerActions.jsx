import { useState } from 'react'
import { supabase } from '../../lib/supabase'
import Button from '../ui/Button'

/**
 * Program Partner Actions Component
 * Simple add/remove actions with payment tracking
 */
export default function ProgramPartnerActions({ contact, onUpdate }) {
  const [showRemoveModal, setShowRemoveModal] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Form state
  const [reason, setReason] = useState('')
  const [customReason, setCustomReason] = useState('')
  const [notes, setNotes] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('check')
  const [paymentNotes, setPaymentNotes] = useState('')

  const isPartner = contact?.is_expected_program_partner

  const removeReasons = [
    { value: 'no_longer_qualifying', label: 'No longer meets qualification criteria' },
    { value: 'request_removal', label: 'Contact requested removal' },
    { value: 'payment_issues', label: 'Payment/billing issues' },
    { value: 'duplicate_entry', label: 'Duplicate entry' },
    { value: 'data_correction', label: 'Data correction' },
    { value: 'other', label: 'Other (specify below)' },
  ]

  const paymentMethods = [
    { value: 'check', label: '📝 Check', description: 'Payment by check' },
    { value: 'cash', label: '💵 Cash', description: 'Cash payment' },
    { value: 'wire_transfer', label: '🏦 Wire Transfer', description: 'Bank wire' },
    { value: 'credit_card', label: '💳 Credit Card', description: 'Manual card processing' },
    { value: 'paypal', label: 'PayPal', description: 'Manual PayPal' },
    { value: 'other', label: '📋 Other', description: 'Other method' },
  ]

  async function handleRemove() {
    try {
      setLoading(true)
      setError(null)

      if (!reason) {
        throw new Error('Please select a reason')
      }
      if (reason === 'other' && !customReason.trim()) {
        throw new Error('Please provide details')
      }

      const finalReason = reason === 'other' ? customReason : removeReasons.find(r => r.value === reason)?.label

      const { data, error: rpcError } = await supabase.rpc('remove_program_partner_status', {
        p_contact_id: contact.id,
        p_reason: finalReason,
        p_notes: notes,
        p_changed_by: 'user@starhouse.org'
      })

      if (rpcError) throw rpcError
      if (!data?.success) throw new Error(data?.error || 'Failed to remove')

      setShowRemoveModal(false)
      resetForm()
      if (onUpdate) onUpdate()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleAdd() {
    try {
      setLoading(true)
      setError(null)

      const { data, error: rpcError } = await supabase.rpc('add_program_partner_status', {
        p_contact_id: contact.id,
        p_reason: 'Added as Program Partner',
        p_notes: notes,
        p_changed_by: 'user@starhouse.org'
      })

      if (rpcError) throw rpcError
      if (!data?.success) throw new Error(data?.error || 'Failed to add')

      setShowAddModal(false)
      resetForm()
      if (onUpdate) onUpdate()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handlePayment() {
    try {
      setLoading(true)
      setError(null)

      if (!paymentMethod) {
        throw new Error('Please select a payment method')
      }
      if (paymentMethod === 'other' && !paymentNotes.trim()) {
        throw new Error('Please provide payment details')
      }

      const { data, error: rpcError } = await supabase.rpc('update_payment_method', {
        p_contact_id: contact.id,
        p_payment_method: paymentMethod,
        p_payment_notes: paymentNotes,
        p_changed_by: 'user@starhouse.org'
      })

      if (rpcError) throw rpcError
      if (!data?.success) throw new Error(data?.error || 'Failed to update')

      setShowPaymentModal(false)
      resetForm()
      if (onUpdate) onUpdate()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function resetForm() {
    setReason('')
    setCustomReason('')
    setNotes('')
    setPaymentMethod('check')
    setPaymentNotes('')
    setError(null)
  }

  function closeModal() {
    setShowRemoveModal(false)
    setShowAddModal(false)
    setShowPaymentModal(false)
    resetForm()
  }

  return (
    <>
      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {isPartner ? (
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPaymentModal(true)}
              className="text-blue-700 border-blue-300 hover:bg-blue-50"
            >
              💳 Record Payment
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowRemoveModal(true)}
              className="text-red-700 border-red-300 hover:bg-red-50"
            >
              ❌ Remove from Partners
            </Button>
          </>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddModal(true)}
            className="text-green-700 border-green-300 hover:bg-green-50"
          >
            ✅ Add as Program Partner
          </Button>
        )}
      </div>

      {/* Remove Modal */}
      {showRemoveModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={closeModal} />

            <div className="relative bg-white rounded-lg max-w-lg w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  ❌ Remove from Program Partners
                </h3>
                <button onClick={closeModal} className="text-gray-400 hover:text-gray-500">
                  <span className="text-2xl">×</span>
                </button>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select a reason...</option>
                    {removeReasons.map(r => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </div>

                {reason === 'other' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Please Specify <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={customReason}
                      onChange={(e) => setCustomReason(e.target.value)}
                      rows={3}
                      placeholder="Provide details..."
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Additional Notes (Optional)
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                    placeholder="Any additional context..."
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <Button onClick={closeModal} variant="outline" disabled={loading}>
                  Cancel
                </Button>
                <Button onClick={handleRemove} variant="danger" disabled={loading}>
                  {loading ? 'Removing...' : 'Remove from Partners'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={closeModal} />

            <div className="relative bg-white rounded-lg max-w-lg w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  ✅ Add as Program Partner
                </h3>
                <button onClick={closeModal} className="text-gray-400 hover:text-gray-500">
                  <span className="text-2xl">×</span>
                </button>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  Add <strong>{contact.first_name} {contact.last_name}</strong> to the Program Partners list.
                </p>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes (Optional)
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                    placeholder="Why are they being added? (e.g., Met qualifications, Signed up at event...)"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <Button onClick={closeModal} variant="outline" disabled={loading}>
                  Cancel
                </Button>
                <Button onClick={handleAdd} variant="primary" disabled={loading}>
                  {loading ? 'Adding...' : 'Add as Program Partner'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={closeModal} />

            <div className="relative bg-white rounded-lg max-w-lg w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  💳 Record Payment
                </h3>
                <button onClick={closeModal} className="text-gray-400 hover:text-gray-500">
                  <span className="text-2xl">×</span>
                </button>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Payment Method <span className="text-red-500">*</span>
                  </label>
                  <div className="space-y-2">
                    {paymentMethods.map(pm => (
                      <label key={pm.value} className="flex items-start p-2 border rounded-md cursor-pointer hover:bg-gray-50">
                        <input
                          type="radio"
                          name="paymentMethod"
                          value={pm.value}
                          checked={paymentMethod === pm.value}
                          onChange={(e) => setPaymentMethod(e.target.value)}
                          className="mt-1"
                        />
                        <div className="ml-3">
                          <div className="text-sm font-medium text-gray-900">{pm.label}</div>
                          <div className="text-xs text-gray-500">{pm.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Payment Details {paymentMethod === 'other' && <span className="text-red-500">*</span>}
                  </label>
                  <textarea
                    value={paymentNotes}
                    onChange={(e) => setPaymentNotes(e.target.value)}
                    rows={3}
                    placeholder={
                      paymentMethod === 'check' ? 'Check #, Amount, Date received...' :
                      paymentMethod === 'cash' ? 'Amount, Date, Receipt #...' :
                      'Amount, Date, Details...'
                    }
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <Button onClick={closeModal} variant="outline" disabled={loading}>
                  Cancel
                </Button>
                <Button onClick={handlePayment} variant="primary" disabled={loading}>
                  {loading ? 'Recording...' : 'Record Payment'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
