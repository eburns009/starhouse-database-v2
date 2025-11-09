import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { contactEditSchema } from '../../lib/validation'
import { supabase } from '../../lib/supabase'
import Input from '../ui/Input'
import Button from '../ui/Button'
import Checkbox from '../ui/Checkbox'
import { useState, useEffect } from 'react'

export default function ContactEditForm({ contact, onSuccess, onCancel }) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [serverError, setServerError] = useState(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm({
    resolver: zodResolver(contactEditSchema),
    defaultValues: contact
  })

  useEffect(() => {
    if (contact) {
      reset(contact)
    }
  }, [contact, reset])

  const onSubmit = async (data) => {
    try {
      setIsSubmitting(true)
      setServerError(null)

      const cleanData = Object.fromEntries(
        Object.entries(data).map(([key, value]) => [
          key,
          value === '' ? null : value
        ])
      )

      const { data: updatedContact, error } = await supabase
        .from('contacts')
        .update(cleanData)
        .eq('id', contact.id)
        .select()
        .single()

      if (error) throw error

      onSuccess?.(updatedContact)
    } catch (error) {
      console.error('Error updating contact:', error)
      setServerError(error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {serverError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {serverError}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="First Name"
          {...register('first_name')}
          error={errors.first_name?.message}
        />
        <Input
          label="Last Name"
          {...register('last_name')}
          error={errors.last_name?.message}
        />
        <Input
          label="Email"
          type="email"
          {...register('email')}
          error={errors.email?.message}
        />
        <Input
          label="Phone"
          {...register('phone')}
          error={errors.phone?.message}
        />
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-3">Billing Address</h3>
        <div className="space-y-3">
          <Input label="Address Line 1" {...register('address_line_1')} />
          <Input label="Address Line 2" {...register('address_line_2')} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="City" {...register('city')} />
            <Input label="State" {...register('state')} />
            <Input label="Postal Code" {...register('postal_code')} />
            <Input label="Country" {...register('country')} />
          </div>
        </div>
      </div>

      <Checkbox label="Subscribe to email list" {...register('email_subscribed')} />

      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  )
}
