import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { contactSchema } from '../../lib/validation'
import { supabase } from '../../lib/supabase'
import Modal from '../ui/Modal'
import Input from '../ui/Input'
import Button from '../ui/Button'
import Checkbox from '../ui/Checkbox'
import { useState } from 'react'

export default function ContactForm({ isOpen, onClose, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [serverError, setServerError] = useState(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      address_line_1: '',
      address_line_2: '',
      city: '',
      state: '',
      postal_code: '',
      country: 'US',
      email_subscribed: true,
      notes: ''
    }
  })

  const onSubmit = async (data) => {
    try {
      setIsSubmitting(true)
      setServerError(null)

      // Clean up empty strings
      const cleanData = Object.fromEntries(
        Object.entries(data).map(([key, value]) => [
          key,
          value === '' ? null : value
        ])
      )

      const { data: newContact, error } = await supabase
        .from('contacts')
        .insert([cleanData])
        .select()
        .single()

      if (error) throw error

      reset()
      onSuccess?.(newContact)
      onClose()
    } catch (error) {
      console.error('Error creating contact:', error)
      setServerError(error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Contact"
      size="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {serverError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {serverError}
          </div>
        )}

        {/* Basic Information */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First Name"
              {...register('first_name')}
              error={errors.first_name?.message}
              required
            />
            <Input
              label="Last Name"
              {...register('last_name')}
              error={errors.last_name?.message}
              required
            />
            <Input
              label="Email"
              type="email"
              {...register('email')}
              error={errors.email?.message}
              required
            />
            <Input
              label="Phone"
              {...register('phone')}
              error={errors.phone?.message}
              placeholder="+1 (555) 123-4567"
            />
          </div>
        </div>

        {/* Billing Address */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Billing Address</h3>
          <div className="space-y-4">
            <Input
              label="Address Line 1"
              {...register('address_line_1')}
              error={errors.address_line_1?.message}
            />
            <Input
              label="Address Line 2"
              {...register('address_line_2')}
              error={errors.address_line_2?.message}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="City"
                {...register('city')}
                error={errors.city?.message}
              />
              <Input
                label="State/Province"
                {...register('state')}
                error={errors.state?.message}
              />
              <Input
                label="Postal Code"
                {...register('postal_code')}
                error={errors.postal_code?.message}
              />
              <Input
                label="Country"
                {...register('country')}
                error={errors.country?.message}
              />
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Additional Information</h3>
          <div className="space-y-4">
            <Checkbox
              label="Subscribe to email list"
              {...register('email_subscribed')}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                {...register('notes')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create Contact'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
