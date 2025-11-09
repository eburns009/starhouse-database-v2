import { useState } from 'react'
import { supabase } from '../../lib/supabase'
import Button from '../ui/Button'
import ConfirmDialog from '../ui/ConfirmDialog'

/**
 * Program Partner Management Component
 * FAANG-level implementation with audit trails and payment tracking
 */
export default function ProgramPartnerManagement({ contact, onUpdate }) {
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Modal state
  const [action, setAction] = useState('remove') // 'remove' or 'update_payment'
  const [reason, setReason] = useState('')
  const [customReason, setCustomReason] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('check')
  const [paymentNotes, setPaymentNotes] = useState('')

  const isPartner = contact?.is_expected_program_partner

  const reasonOptions = [
    { value: 'no_longer_qualifying', label: 'No longer meets qualification criteria' },
    { value: 'request_removal', label: 'Contact requested removal' },
    { value: 'payment_issues', label: 'Payment/billing issues' },
    { value: 'duplicate_entry', label: 'Duplicate entry' },
    { value: 'data_correction', label: 'Data correction' },
    { value: 'other', label: 'Other (specify below)' },
  ]

  const paymentMethodOptions = [
    { value: 'check', label: '📝 Check', description: 'Payment by physical check' },
    { value: 'cash', label: '💵 Cash', description: 'Cash payment in person' },
    { value: 'wire_transfer', label: '🏦 Wire Transfer', description: 'Bank wire transfer' },
    { value: 'credit_card', label: '💳 Credit Card', description: 'Manual credit card processing' },
    { value: 'paypal', label: 'PayPal (manual)', description: 'Manual PayPal payment' },
    { value: 'other', label: '📋 Other', description: 'Other payment method' },
  ]

  function openModal() {
    setShowModal(true)
    setError(null)
    // Reset form
    setAction('remove')
    setReason('')
    setCustomReason('')
    setPaymentMethod('check')
    setPaymentNotes('')
  }

  function closeModal() {
    setShowModal(false)
    setError(null)
  }

  async function handleSubmit() {
    try {
      setLoading(true)
      setError(null)

      if (action === 'remove') {
        await handleRemoveStatus()
      } else {
        await handleUpdatePayment()
      }

      closeModal()
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Error managing Program Partner status:', err)
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  async function handleRemoveStatus() {
    // Validate
    if (!reason) {
      throw new Error('Please select a reason for removal')
    }
    if (reason === 'other' && !customReason.trim()) {
      throw new Error('Please provide details for "Other" reason')
    }

    const finalReason = reason === 'other' ? customReason : reasonOptions.find(o => o.value === reason)?.label
    const notes = reason === 'other' ? customReason : paymentNotes

    // Call the database function
    const { data, error } = await supabase.rpc('remove_program_partner_status', {
      p_contact_id: contact.id,
      p_reason: finalReason,
      p_notes: notes,
      p_changed_by: 'user@starhouse.org' // TODO: Get actual user email from auth
    })

    if (error) throw error
    if (!data?.success) throw new Error(data?.error || 'Failed to remove status')
  }

  async function handleUpdatePayment() {
    // Validate
    if (!paymentMethod) {
      throw new Error('Please select a payment method')
    }
    if (paymentMethod === 'other' && !paymentNotes.trim()) {
      throw new Error('Please provide details for "Other" payment method')
    }

    // Call the database function
    const { data, error } = await supabase.rpc('update_payment_method', {
      p_contact_id: contact.id,
      p_payment_method: paymentMethod,
      p_payment_notes: paymentNotes,
      p_changed_by: 'user@starhouse.org' // TODO: Get actual user email from auth
    })

    if (error) throw error
    if (!data?.success) throw new Error(data?.error || 'Failed to update payment method')
  }

  if (!isPartner) {
    return null // Don't show button if not a partner
  }

  return (
    <>
      {/* Manage Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={openModal}
        className="text-gray-700 border-gray-300 hover:bg-gray-50"
      >
        ⚙️ Manage Partner Status
      </Button>

      {/* Management Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={closeModal}
            />

            {/* Modal panel */}
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              {/* Header */}
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                    ⚙️
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Manage Program Partner Status
                    </h3>
                    <p className="mt-2 text-sm text-gray-500">
                      {contact.first_name} {contact.last_name}
                    </p>
                  </div>
                  <button
                    onClick={closeModal}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <span className="text-2xl">×</span>
                  </button>
                </div>

                {/* Error Display */}
                {error && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}

                {/* Action Selection */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    What would you like to do?
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-start p-3 border rounded-md cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="action"
                        value="remove"
                        checked={action === 'remove'}
                        onChange={(e) => setAction(e.target.value)}
                        className="mt-1"
                      />
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">
                          ❌ Remove Program Partner Status
                        </div>
                        <div className="text-sm text-gray-500">
                          Permanently remove this contact from Program Partners list
                        </div>
                      </div>
                    </label>
                    <label className="flex items-start p-3 border rounded-md cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="action"
                        value="update_payment"
                        checked={action === 'update_payment'}
                        onChange={(e) => setAction(e.target.value)}
                        className="mt-1"
                      />
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">
                          💳 Update Payment Method
                        </div>
                        <div className="text-sm text-gray-500">
                          Record payment via check, cash, or other method
                        </div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Remove Status Form */}
                {action === 'remove' && (
                  <div className="mt-4 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Reason for Removal <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Select a reason...</option>
                        {reasonOptions.map(opt => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
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
                          placeholder="Provide details about why this status is being removed..."
                          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    )}

                    {reason && reason !== 'other' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Additional Notes (Optional)
                        </label>
                        <textarea
                          value={paymentNotes}
                          onChange={(e) => setPaymentNotes(e.target.value)}
                          rows={2}
                          placeholder="Any additional context or notes..."
                          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Update Payment Form */}
                {action === 'update_payment' && (
                  <div className="mt-4 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Payment Method <span className="text-red-500">*</span>
                      </label>
                      <div className="space-y-2">
                        {paymentMethodOptions.map(opt => (
                          <label
                            key={opt.value}
                            className="flex items-start p-2 border rounded-md cursor-pointer hover:bg-gray-50"
                          >
                            <input
                              type="radio"
                              name="paymentMethod"
                              value={opt.value}
                              checked={paymentMethod === opt.value}
                              onChange={(e) => setPaymentMethod(e.target.value)}
                              className="mt-1"
                            />
                            <div className="ml-3">
                              <div className="text-sm font-medium text-gray-900">
                                {opt.label}
                              </div>
                              <div className="text-xs text-gray-500">
                                {opt.description}
                              </div>
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
                          paymentMethod === 'check' ? 'Check number, date received, amount...' :
                          paymentMethod === 'cash' ? 'Amount, date received, receipt number...' :
                          paymentMethod === 'wire_transfer' ? 'Transaction ID, date received...' :
                          'Payment details, amount, date...'
                        }
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        Include check numbers, amounts, dates, or any relevant details
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <Button
                  onClick={handleSubmit}
                  disabled={loading}
                  variant="primary"
                  className="w-full sm:w-auto sm:ml-3"
                >
                  {loading ? 'Processing...' : action === 'remove' ? 'Remove Status' : 'Update Payment'}
                </Button>
                <Button
                  onClick={closeModal}
                  disabled={loading}
                  variant="outline"
                  className="mt-3 sm:mt-0 w-full sm:w-auto"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
