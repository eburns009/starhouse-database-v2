/**
 * Database Types
 *
 * TODO: Generate from Supabase with: npm run db:types
 * This will auto-generate types from your database schema
 *
 * For now, core types are defined manually
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type SourceSystem =
  | 'kajabi'
  | 'zoho'
  | 'ticket_tailor'
  | 'quickbooks'
  | 'mailchimp'
  | 'manual'

export type SubscriptionStatus =
  | 'active'
  | 'paused'
  | 'canceled'
  | 'expired'
  | 'trial'

export type PaymentStatus =
  | 'pending'
  | 'completed'
  | 'failed'
  | 'refunded'
  | 'disputed'

export type TransactionType =
  | 'purchase'
  | 'subscription'
  | 'refund'
  | 'adjustment'

export type JobStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

export type JobType =
  | 'bulk_import'
  | 'bulk_export'
  | 'bulk_merge'
  | 'bulk_tag'
  | 'bulk_delete'
  | 'report_generation'
  | 'data_cleanup'

export interface Database {
  public: {
    Tables: {
      contacts: {
        Row: {
          id: string
          email: string
          first_name: string | null
          last_name: string | null
          phone: string | null
          paypal_phone: string | null
          phone_country_code: string | null
          address_line_1: string | null
          address_line_2: string | null
          address: string | null
          address_2: string | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_status: string | null
          city: string | null
          state: string | null
          postal_code: string | null
          country: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_business_name: string | null
          additional_name: string | null
          additional_name_source: string | null
          email_subscribed: boolean
          source_system: SourceSystem
          kajabi_id: string | null
          kajabi_member_id: string | null
          ticket_tailor_id: string | null
          zoho_id: string | null
          quickbooks_id: string | null
          mailchimp_id: string | null
          notes: string | null
          potential_duplicate_group: string | null
          potential_duplicate_reason: string | null
          potential_duplicate_flagged_at: string | null
          deleted_at: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          first_name?: string | null
          last_name?: string | null
          phone?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          city?: string | null
          state?: string | null
          postal_code?: string | null
          country?: string | null
          email_subscribed?: boolean
          source_system?: SourceSystem
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          ticket_tailor_id?: string | null
          zoho_id?: string | null
          quickbooks_id?: string | null
          mailchimp_id?: string | null
          notes?: string | null
          deleted_at?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          first_name?: string | null
          last_name?: string | null
          phone?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          city?: string | null
          state?: string | null
          postal_code?: string | null
          country?: string | null
          email_subscribed?: boolean
          source_system?: SourceSystem
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          ticket_tailor_id?: string | null
          zoho_id?: string | null
          quickbooks_id?: string | null
          mailchimp_id?: string | null
          notes?: string | null
          deleted_at?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      tags: {
        Row: {
          id: string
          name: string
          description: string | null
          category: string | null
          deleted_at: string | null
          created_at: string
          updated_at: string
        }
      }
      products: {
        Row: {
          id: string
          name: string
          description: string | null
          product_type: string | null
          kajabi_offer_id: string | null
          active: boolean
          archived_at: string | null
          deleted_at: string | null
          created_at: string
          updated_at: string
        }
      }
      subscriptions: {
        Row: {
          id: string
          contact_id: string
          product_id: string | null
          kajabi_subscription_id: string | null
          status: SubscriptionStatus
          amount: number | null
          currency: string
          billing_cycle: string | null
          start_date: string | null
          trial_end_date: string | null
          cancellation_date: string | null
          next_billing_date: string | null
          payment_processor: string | null
          coupon_code: string | null
          deleted_at: string | null
          created_at: string
          updated_at: string
        }
      }
      transactions: {
        Row: {
          id: string
          contact_id: string
          product_id: string | null
          subscription_id: string | null
          kajabi_transaction_id: string | null
          order_number: string | null
          transaction_type: TransactionType
          status: PaymentStatus
          amount: number
          currency: string
          tax_amount: number | null
          quantity: number
          payment_method: string | null
          payment_processor: string | null
          coupon_code: string | null
          transaction_date: string
          deleted_at: string | null
          created_at: string
          updated_at: string
        }
      }
      audit_log: {
        Row: {
          id: string
          user_id: string | null
          user_email: string | null
          action: string
          table_name: string
          record_id: string
          old_values: Json | null
          new_values: Json | null
          ip_address: string | null
          user_agent: string | null
          metadata: Json | null
          created_at: string
        }
      }
      jobs: {
        Row: {
          id: string
          type: JobType
          status: JobStatus
          user_id: string | null
          user_email: string | null
          payload: Json
          started_at: string | null
          completed_at: string | null
          total_items: number | null
          processed_items: number
          failed_items: number
          result: Json | null
          error_message: string | null
          error_details: Json | null
          created_at: string
          updated_at: string
        }
      }
      saved_views: {
        Row: {
          id: string
          user_id: string
          name: string
          entity: string
          is_default: boolean
          filters: Json
          sort: Json | null
          columns: Json | null
          share_scope: string
          created_at: string
          updated_at: string
        }
      }
    }
    Views: {
      v_contact_summary: {
        Row: {
          id: string
          email: string
          first_name: string | null
          last_name: string | null
          tag_count: number
          product_count: number
          subscription_count: number
          transaction_count: number
          total_revenue: number | null
          last_transaction_date: string | null
        }
      }
    }
  }
}
