export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.5"
  }
  public: {
    Tables: {
      audit_log: {
        Row: {
          action: string
          created_at: string
          id: string
          ip_address: unknown
          metadata: Json | null
          new_values: Json | null
          old_values: Json | null
          record_id: string
          table_name: string
          user_agent: string | null
          user_email: string | null
          user_id: string | null
        }
        Insert: {
          action: string
          created_at?: string
          id?: string
          ip_address?: unknown
          metadata?: Json | null
          new_values?: Json | null
          old_values?: Json | null
          record_id: string
          table_name: string
          user_agent?: string | null
          user_email?: string | null
          user_id?: string | null
        }
        Update: {
          action?: string
          created_at?: string
          id?: string
          ip_address?: unknown
          metadata?: Json | null
          new_values?: Json | null
          old_values?: Json | null
          record_id?: string
          table_name?: string
          user_agent?: string | null
          user_email?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
      backup_legacy_program_partner_corrections: {
        Row: {
          backup_timestamp: string | null
          contact_email: string | null
          contact_id: string | null
          correct_group: string | null
          correct_level: string | null
          corrected: boolean | null
          corrected_at: string | null
          created_at: string | null
          current_group: string | null
          id: string | null
          notes: string | null
        }
        Insert: {
          backup_timestamp?: string | null
          contact_email?: string | null
          contact_id?: string | null
          correct_group?: string | null
          correct_level?: string | null
          corrected?: boolean | null
          corrected_at?: string | null
          created_at?: string | null
          current_group?: string | null
          id?: string | null
          notes?: string | null
        }
        Update: {
          backup_timestamp?: string | null
          contact_email?: string | null
          contact_id?: string | null
          correct_group?: string | null
          correct_level?: string | null
          corrected?: boolean | null
          corrected_at?: string | null
          created_at?: string | null
          current_group?: string | null
          id?: string | null
          notes?: string | null
        }
        Relationships: []
      }
      backup_phone_duplicate_merge_20251109: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          country: string | null
          created_at: string | null
          email: string | null
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          id: string | null
          is_legacy_member: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          mailchimp_id: string | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          quickbooks_id: string | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string | null
          state: string | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          updated_at: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          country?: string | null
          created_at?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          id?: string | null
          is_legacy_member?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          mailchimp_id?: string | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          quickbooks_id?: string | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          updated_at?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          country?: string | null
          created_at?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          id?: string | null
          is_legacy_member?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          mailchimp_id?: string | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          quickbooks_id?: string | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          updated_at?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: []
      }
      backup_program_partner_audit_log: {
        Row: {
          action: string | null
          backup_timestamp: string | null
          changed_at: string | null
          changed_by: string | null
          contact_id: string | null
          id: string | null
          ip_address: unknown
          metadata: Json | null
          new_value: Json | null
          notes: string | null
          previous_value: Json | null
          reason: string | null
          user_agent: string | null
        }
        Insert: {
          action?: string | null
          backup_timestamp?: string | null
          changed_at?: string | null
          changed_by?: string | null
          contact_id?: string | null
          id?: string | null
          ip_address?: unknown
          metadata?: Json | null
          new_value?: Json | null
          notes?: string | null
          previous_value?: Json | null
          reason?: string | null
          user_agent?: string | null
        }
        Update: {
          action?: string | null
          backup_timestamp?: string | null
          changed_at?: string | null
          changed_by?: string | null
          contact_id?: string | null
          id?: string | null
          ip_address?: unknown
          metadata?: Json | null
          new_value?: Json | null
          notes?: string | null
          previous_value?: Json | null
          reason?: string | null
          user_agent?: string | null
        }
        Relationships: []
      }
      backup_program_partner_contacts: {
        Row: {
          backup_timestamp: string | null
          email: string | null
          first_name: string | null
          id: string | null
          is_expected_program_partner: boolean | null
          last_name: string | null
          last_payment_date: string | null
          partner_status_notes: string | null
          payment_method: string | null
          payment_method_notes: string | null
        }
        Insert: {
          backup_timestamp?: string | null
          email?: string | null
          first_name?: string | null
          id?: string | null
          is_expected_program_partner?: boolean | null
          last_name?: string | null
          last_payment_date?: string | null
          partner_status_notes?: string | null
          payment_method?: string | null
          payment_method_notes?: string | null
        }
        Update: {
          backup_timestamp?: string | null
          email?: string | null
          first_name?: string | null
          id?: string | null
          is_expected_program_partner?: boolean | null
          last_name?: string | null
          last_payment_date?: string | null
          partner_status_notes?: string | null
          payment_method?: string | null
          payment_method_notes?: string | null
        }
        Relationships: []
      }
      backup_subscriptions_paypal_cleanup_20251109: {
        Row: {
          backup_timestamp: string | null
          contact_id: string | null
          created_at: string | null
          id: string | null
          kajabi_subscription_id: string | null
          payment_processor: string | null
          paypal_subscription_reference: string | null
          start_date: string | null
          status: Database["public"]["Enums"]["subscription_status"] | null
        }
        Insert: {
          backup_timestamp?: string | null
          contact_id?: string | null
          created_at?: string | null
          id?: string | null
          kajabi_subscription_id?: string | null
          payment_processor?: string | null
          paypal_subscription_reference?: string | null
          start_date?: string | null
          status?: Database["public"]["Enums"]["subscription_status"] | null
        }
        Update: {
          backup_timestamp?: string | null
          contact_id?: string | null
          created_at?: string | null
          id?: string | null
          kajabi_subscription_id?: string | null
          payment_processor?: string | null
          paypal_subscription_reference?: string | null
          start_date?: string | null
          status?: Database["public"]["Enums"]["subscription_status"] | null
        }
        Relationships: []
      }
      contact_emails: {
        Row: {
          bounce_reason: string | null
          contact_id: string
          created_at: string
          created_by: string | null
          deliverable: boolean | null
          email: string
          email_type: string | null
          id: string
          is_outreach: boolean
          is_primary: boolean
          last_bounce_at: string | null
          source: string
          updated_at: string
          updated_by: string | null
          verified: boolean
          verified_at: string | null
        }
        Insert: {
          bounce_reason?: string | null
          contact_id: string
          created_at?: string
          created_by?: string | null
          deliverable?: boolean | null
          email: string
          email_type?: string | null
          id?: string
          is_outreach?: boolean
          is_primary?: boolean
          last_bounce_at?: string | null
          source: string
          updated_at?: string
          updated_by?: string | null
          verified?: boolean
          verified_at?: string | null
        }
        Update: {
          bounce_reason?: string | null
          contact_id?: string
          created_at?: string
          created_by?: string | null
          deliverable?: boolean | null
          email?: string
          email_type?: string | null
          id?: string
          is_outreach?: boolean
          is_primary?: boolean
          last_bounce_at?: string | null
          source?: string
          updated_at?: string
          updated_by?: string | null
          verified?: boolean
          verified_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_emails_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      contact_emails_backup_20251110: {
        Row: {
          bounce_reason: string | null
          contact_id: string | null
          created_at: string | null
          created_by: string | null
          deliverable: boolean | null
          email: string | null
          email_type: string | null
          id: string | null
          is_outreach: boolean | null
          is_primary: boolean | null
          last_bounce_at: string | null
          source: string | null
          updated_at: string | null
          updated_by: string | null
          verified: boolean | null
          verified_at: string | null
        }
        Insert: {
          bounce_reason?: string | null
          contact_id?: string | null
          created_at?: string | null
          created_by?: string | null
          deliverable?: boolean | null
          email?: string | null
          email_type?: string | null
          id?: string | null
          is_outreach?: boolean | null
          is_primary?: boolean | null
          last_bounce_at?: string | null
          source?: string | null
          updated_at?: string | null
          updated_by?: string | null
          verified?: boolean | null
          verified_at?: string | null
        }
        Update: {
          bounce_reason?: string | null
          contact_id?: string | null
          created_at?: string | null
          created_by?: string | null
          deliverable?: boolean | null
          email?: string | null
          email_type?: string | null
          id?: string | null
          is_outreach?: boolean | null
          is_primary?: boolean | null
          last_bounce_at?: string | null
          source?: string | null
          updated_at?: string | null
          updated_by?: string | null
          verified?: boolean | null
          verified_at?: string | null
        }
        Relationships: []
      }
      contact_names: {
        Row: {
          contact_id: string
          created_at: string
          id: string
          is_primary: boolean
          name_text: string
          name_type: string
          source: string
          updated_at: string
          verified: boolean
        }
        Insert: {
          contact_id: string
          created_at?: string
          id?: string
          is_primary?: boolean
          name_text: string
          name_type?: string
          source: string
          updated_at?: string
          verified?: boolean
        }
        Update: {
          contact_id?: string
          created_at?: string
          id?: string
          is_primary?: boolean
          name_text?: string
          name_type?: string
          source?: string
          updated_at?: string
          verified?: boolean
        }
        Relationships: [
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_names_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      contact_notes: {
        Row: {
          author_name: string
          author_user_id: string | null
          contact_id: string
          content: string
          created_at: string
          created_by: string | null
          id: string
          is_pinned: boolean
          is_private: boolean
          note_type: string
          subject: string | null
          tags: string[] | null
          updated_at: string
          updated_by: string | null
        }
        Insert: {
          author_name: string
          author_user_id?: string | null
          contact_id: string
          content: string
          created_at?: string
          created_by?: string | null
          id?: string
          is_pinned?: boolean
          is_private?: boolean
          note_type?: string
          subject?: string | null
          tags?: string[] | null
          updated_at?: string
          updated_by?: string | null
        }
        Update: {
          author_name?: string
          author_user_id?: string | null
          contact_id?: string
          content?: string
          created_at?: string
          created_by?: string | null
          id?: string
          is_pinned?: boolean
          is_private?: boolean
          note_type?: string
          subject?: string | null
          tags?: string[] | null
          updated_at?: string
          updated_by?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_notes_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      contact_products: {
        Row: {
          access_expires_at: string | null
          access_granted_at: string | null
          contact_id: string
          created_at: string
          id: string
          product_id: string
        }
        Insert: {
          access_expires_at?: string | null
          access_granted_at?: string | null
          contact_id: string
          created_at?: string
          id?: string
          product_id: string
        }
        Update: {
          access_expires_at?: string | null
          access_granted_at?: string | null
          contact_id?: string
          created_at?: string
          id?: string
          product_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_products_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_products_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "v_active_products"
            referencedColumns: ["id"]
          },
        ]
      }
      contact_roles: {
        Row: {
          contact_id: string
          created_at: string
          created_by: string | null
          ended_at: string | null
          id: string
          metadata: Json | null
          notes: string | null
          role: string
          source: string | null
          started_at: string
          status: string
          updated_at: string
          updated_by: string | null
        }
        Insert: {
          contact_id: string
          created_at?: string
          created_by?: string | null
          ended_at?: string | null
          id?: string
          metadata?: Json | null
          notes?: string | null
          role: string
          source?: string | null
          started_at?: string
          status?: string
          updated_at?: string
          updated_by?: string | null
        }
        Update: {
          contact_id?: string
          created_at?: string
          created_by?: string | null
          ended_at?: string | null
          id?: string
          metadata?: Json | null
          notes?: string | null
          role?: string
          source?: string | null
          started_at?: string
          status?: string
          updated_at?: string
          updated_by?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      contact_tags: {
        Row: {
          contact_id: string
          created_at: string
          id: string
          tag_id: string
        }
        Insert: {
          contact_id: string
          created_at?: string
          id?: string
          tag_id: string
        }
        Update: {
          contact_id?: string
          created_at?: string
          id?: string
          tag_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_tags_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_tags_tag_id_fkey"
            columns: ["tag_id"]
            isOneToOne: false
            referencedRelation: "tags"
            referencedColumns: ["id"]
          },
        ]
      }
      contacts: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          address_quality_score: number | null
          address_validated: boolean | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          consent_date: string | null
          consent_method: string | null
          consent_source: string | null
          country: string | null
          created_at: string
          created_by: string | null
          deleted_at: string | null
          deleted_by: string | null
          email: string
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          household_id: string | null
          id: string
          import_locked: boolean | null
          import_locked_at: string | null
          import_locked_reason: string | null
          is_alias_of: string | null
          is_legacy_member: boolean | null
          is_primary_household_contact: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          legal_basis: string | null
          lock_level: string | null
          mailchimp_id: string | null
          mailing_list_ready: boolean | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          merge_history: Json | null
          ncoa_move_date: string | null
          ncoa_new_address: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          potential_duplicate_flagged_at: string | null
          potential_duplicate_group: string | null
          potential_duplicate_reason: string | null
          preferred_mailing_address: string | null
          quickbooks_id: string | null
          secondary_emails: Json | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string
          state: string | null
          subscription_protected: boolean | null
          subscription_protected_reason: string | null
          tags: string[] | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          unsubscribe_date: string | null
          updated_at: string
          updated_by: string | null
          usps_dpv_confirmation: string | null
          usps_rdi: string | null
          usps_validation_date: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email: string
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contacts_is_alias_of_fkey"
            columns: ["is_alias_of"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      contacts_additions_backup: {
        Row: {
          added_at: string | null
          backup_id: number
          contact_data: Json
          contact_email: string
          notes: string | null
          source_system: string
        }
        Insert: {
          added_at?: string | null
          backup_id?: number
          contact_data: Json
          contact_email: string
          notes?: string | null
          source_system: string
        }
        Update: {
          added_at?: string | null
          backup_id?: number
          contact_data?: Json
          contact_email?: string
          notes?: string | null
          source_system?: string
        }
        Relationships: []
      }
      contacts_backup_20251115_203330_ncoa: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          address_quality_score: number | null
          address_validated: boolean | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          consent_date: string | null
          consent_method: string | null
          consent_source: string | null
          country: string | null
          created_at: string | null
          created_by: string | null
          deleted_at: string | null
          deleted_by: string | null
          email: string | null
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          household_id: string | null
          id: string | null
          import_locked: boolean | null
          import_locked_at: string | null
          import_locked_reason: string | null
          is_alias_of: string | null
          is_legacy_member: boolean | null
          is_primary_household_contact: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          legal_basis: string | null
          lock_level: string | null
          mailchimp_id: string | null
          mailing_list_ready: boolean | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          merge_history: Json | null
          ncoa_move_date: string | null
          ncoa_new_address: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          potential_duplicate_flagged_at: string | null
          potential_duplicate_group: string | null
          potential_duplicate_reason: string | null
          preferred_mailing_address: string | null
          quickbooks_id: string | null
          secondary_emails: Json | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string | null
          state: string | null
          subscription_protected: boolean | null
          subscription_protected_reason: string | null
          tags: string[] | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          unsubscribe_date: string | null
          updated_at: string | null
          updated_by: string | null
          usps_dpv_confirmation: string | null
          usps_rdi: string | null
          usps_validation_date: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: []
      }
      contacts_backup_20251115_203615_ncoa: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          address_quality_score: number | null
          address_validated: boolean | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          consent_date: string | null
          consent_method: string | null
          consent_source: string | null
          country: string | null
          created_at: string | null
          created_by: string | null
          deleted_at: string | null
          deleted_by: string | null
          email: string | null
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          household_id: string | null
          id: string | null
          import_locked: boolean | null
          import_locked_at: string | null
          import_locked_reason: string | null
          is_alias_of: string | null
          is_legacy_member: boolean | null
          is_primary_household_contact: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          legal_basis: string | null
          lock_level: string | null
          mailchimp_id: string | null
          mailing_list_ready: boolean | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          merge_history: Json | null
          ncoa_move_date: string | null
          ncoa_new_address: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          potential_duplicate_flagged_at: string | null
          potential_duplicate_group: string | null
          potential_duplicate_reason: string | null
          preferred_mailing_address: string | null
          quickbooks_id: string | null
          secondary_emails: Json | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string | null
          state: string | null
          subscription_protected: boolean | null
          subscription_protected_reason: string | null
          tags: string[] | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          unsubscribe_date: string | null
          updated_at: string | null
          updated_by: string | null
          usps_dpv_confirmation: string | null
          usps_rdi: string | null
          usps_validation_date: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: []
      }
      contacts_backup_20251115_210133_exceptions: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          address_quality_score: number | null
          address_validated: boolean | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          consent_date: string | null
          consent_method: string | null
          consent_source: string | null
          country: string | null
          created_at: string | null
          created_by: string | null
          deleted_at: string | null
          deleted_by: string | null
          email: string | null
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          household_id: string | null
          id: string | null
          import_locked: boolean | null
          import_locked_at: string | null
          import_locked_reason: string | null
          is_alias_of: string | null
          is_legacy_member: boolean | null
          is_primary_household_contact: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          legal_basis: string | null
          lock_level: string | null
          mailchimp_id: string | null
          mailing_list_ready: boolean | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          merge_history: Json | null
          ncoa_move_date: string | null
          ncoa_new_address: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          potential_duplicate_flagged_at: string | null
          potential_duplicate_group: string | null
          potential_duplicate_reason: string | null
          preferred_mailing_address: string | null
          quickbooks_id: string | null
          secondary_emails: Json | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string | null
          state: string | null
          subscription_protected: boolean | null
          subscription_protected_reason: string | null
          tags: string[] | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          unsubscribe_date: string | null
          updated_at: string | null
          updated_by: string | null
          usps_dpv_confirmation: string | null
          usps_rdi: string | null
          usps_validation_date: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: []
      }
      contacts_backup_20251115_215640_ncoa: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          address_quality_score: number | null
          address_validated: boolean | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          consent_date: string | null
          consent_method: string | null
          consent_source: string | null
          country: string | null
          created_at: string | null
          created_by: string | null
          deleted_at: string | null
          deleted_by: string | null
          email: string | null
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          household_id: string | null
          id: string | null
          import_locked: boolean | null
          import_locked_at: string | null
          import_locked_reason: string | null
          is_alias_of: string | null
          is_legacy_member: boolean | null
          is_primary_household_contact: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          legal_basis: string | null
          lock_level: string | null
          mailchimp_id: string | null
          mailing_list_ready: boolean | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          merge_history: Json | null
          ncoa_move_date: string | null
          ncoa_new_address: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          potential_duplicate_flagged_at: string | null
          potential_duplicate_group: string | null
          potential_duplicate_reason: string | null
          preferred_mailing_address: string | null
          quickbooks_id: string | null
          secondary_emails: Json | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string | null
          state: string | null
          subscription_protected: boolean | null
          subscription_protected_reason: string | null
          tags: string[] | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          unsubscribe_date: string | null
          updated_at: string | null
          updated_by: string | null
          usps_dpv_confirmation: string | null
          usps_rdi: string | null
          usps_validation_date: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          address_quality_score?: number | null
          address_validated?: boolean | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          household_id?: string | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_alias_of?: string | null
          is_legacy_member?: boolean | null
          is_primary_household_contact?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          mailing_list_ready?: boolean | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          merge_history?: Json | null
          ncoa_move_date?: string | null
          ncoa_new_address?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          secondary_emails?: Json | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          usps_dpv_confirmation?: string | null
          usps_rdi?: string | null
          usps_validation_date?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: []
      }
      contacts_backup_20251115_enrichment: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          consent_date: string | null
          consent_method: string | null
          consent_source: string | null
          country: string | null
          created_at: string | null
          created_by: string | null
          deleted_at: string | null
          deleted_by: string | null
          email: string | null
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          id: string | null
          import_locked: boolean | null
          import_locked_at: string | null
          import_locked_reason: string | null
          is_legacy_member: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          legal_basis: string | null
          lock_level: string | null
          mailchimp_id: string | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          potential_duplicate_flagged_at: string | null
          potential_duplicate_group: string | null
          potential_duplicate_reason: string | null
          preferred_mailing_address: string | null
          quickbooks_id: string | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string | null
          state: string | null
          subscription_protected: boolean | null
          subscription_protected_reason: string | null
          tags: string[] | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          unsubscribe_date: string | null
          updated_at: string | null
          updated_by: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_legacy_member?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          consent_date?: string | null
          consent_method?: string | null
          consent_source?: string | null
          country?: string | null
          created_at?: string | null
          created_by?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          id?: string | null
          import_locked?: boolean | null
          import_locked_at?: string | null
          import_locked_reason?: string | null
          is_legacy_member?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          legal_basis?: string | null
          lock_level?: string | null
          mailchimp_id?: string | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          potential_duplicate_flagged_at?: string | null
          potential_duplicate_group?: string | null
          potential_duplicate_reason?: string | null
          preferred_mailing_address?: string | null
          quickbooks_id?: string | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          subscription_protected?: boolean | null
          subscription_protected_reason?: string | null
          tags?: string[] | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          unsubscribe_date?: string | null
          updated_at?: string | null
          updated_by?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: []
      }
      contacts_cleanup_backup: {
        Row: {
          backup_id: number
          cleaned_at: string | null
          cleanup_type: string
          contact_id: string
          new_data: Json | null
          notes: string | null
          old_data: Json
        }
        Insert: {
          backup_id?: number
          cleaned_at?: string | null
          cleanup_type: string
          contact_id: string
          new_data?: Json | null
          notes?: string | null
          old_data: Json
        }
        Update: {
          backup_id?: number
          cleaned_at?: string | null
          cleanup_type?: string
          contact_id?: string
          new_data?: Json | null
          notes?: string | null
          old_data?: Json
        }
        Relationships: []
      }
      contacts_duplicate_cleanup_backup: {
        Row: {
          backup_id: number
          existing_contact_id: string
          existing_email: string
          match_type: string
          merged_at: string | null
          notes: string | null
          paypal_contact_data: Json
          paypal_contact_id: string
          paypal_email: string
        }
        Insert: {
          backup_id?: number
          existing_contact_id: string
          existing_email: string
          match_type: string
          merged_at?: string | null
          notes?: string | null
          paypal_contact_data: Json
          paypal_contact_id: string
          paypal_email: string
        }
        Update: {
          backup_id?: number
          existing_contact_id?: string
          existing_email?: string
          match_type?: string
          merged_at?: string | null
          notes?: string | null
          paypal_contact_data?: Json
          paypal_contact_id?: string
          paypal_email?: string
        }
        Relationships: []
      }
      contacts_enrichment_backup: {
        Row: {
          backup_id: number
          contact_id: string
          enriched_at: string | null
          enrichment_type: string
          field_name: string
          new_value: string | null
          notes: string | null
          old_value: string | null
        }
        Insert: {
          backup_id?: number
          contact_id: string
          enriched_at?: string | null
          enrichment_type: string
          field_name: string
          new_value?: string | null
          notes?: string | null
          old_value?: string | null
        }
        Update: {
          backup_id?: number
          contact_id?: string
          enriched_at?: string | null
          enrichment_type?: string
          field_name?: string
          new_value?: string | null
          notes?: string | null
          old_value?: string | null
        }
        Relationships: []
      }
      contacts_merge_backup: {
        Row: {
          backup_id: number
          duplicate_contact_data: Json | null
          duplicate_contact_id: string | null
          merged_at: string | null
          merged_tags: string[] | null
          merged_transactions_count: number | null
          notes: string | null
          primary_contact_id: string | null
        }
        Insert: {
          backup_id?: number
          duplicate_contact_data?: Json | null
          duplicate_contact_id?: string | null
          merged_at?: string | null
          merged_tags?: string[] | null
          merged_transactions_count?: number | null
          notes?: string | null
          primary_contact_id?: string | null
        }
        Update: {
          backup_id?: number
          duplicate_contact_data?: Json | null
          duplicate_contact_id?: string | null
          merged_at?: string | null
          merged_tags?: string[] | null
          merged_transactions_count?: number | null
          notes?: string | null
          primary_contact_id?: string | null
        }
        Relationships: []
      }
      dlq_events: {
        Row: {
          created_at: string | null
          error_code: string | null
          error_message: string
          error_stack: string | null
          event_type: string
          id: string
          last_retry_at: string | null
          max_retries: number | null
          next_retry_at: string | null
          payload: Json
          resolved_at: string | null
          resolved_by: string | null
          retry_count: number | null
          source: string
          webhook_event_id: string | null
        }
        Insert: {
          created_at?: string | null
          error_code?: string | null
          error_message: string
          error_stack?: string | null
          event_type: string
          id?: string
          last_retry_at?: string | null
          max_retries?: number | null
          next_retry_at?: string | null
          payload: Json
          resolved_at?: string | null
          resolved_by?: string | null
          retry_count?: number | null
          source: string
          webhook_event_id?: string | null
        }
        Update: {
          created_at?: string | null
          error_code?: string | null
          error_message?: string
          error_stack?: string | null
          event_type?: string
          id?: string
          last_retry_at?: string | null
          max_retries?: number | null
          next_retry_at?: string | null
          payload?: Json
          resolved_at?: string | null
          resolved_by?: string | null
          retry_count?: number | null
          source?: string
          webhook_event_id?: string | null
        }
        Relationships: []
      }
      external_identities: {
        Row: {
          contact_id: string
          created_at: string
          created_by: string | null
          external_id: string
          id: string
          last_synced_at: string | null
          metadata: Json | null
          sync_status: string | null
          system: string
          updated_at: string
          updated_by: string | null
          verified: boolean
          verified_at: string | null
        }
        Insert: {
          contact_id: string
          created_at?: string
          created_by?: string | null
          external_id: string
          id?: string
          last_synced_at?: string | null
          metadata?: Json | null
          sync_status?: string | null
          system: string
          updated_at?: string
          updated_by?: string | null
          verified?: boolean
          verified_at?: string | null
        }
        Update: {
          contact_id?: string
          created_at?: string
          created_by?: string | null
          external_id?: string
          id?: string
          last_synced_at?: string | null
          metadata?: Json | null
          sync_status?: string | null
          system?: string
          updated_at?: string
          updated_by?: string | null
          verified?: boolean
          verified_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "external_identities_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      health_check_log: {
        Row: {
          active_alerts: string[] | null
          checked_at: string
          failed_webhooks_24h: number | null
          id: string
          invalid_signatures_24h: number | null
          name_duplicates: number | null
          orphaned_subscriptions: number | null
          orphaned_transactions: number | null
          overall_status: string
          total_contacts: number | null
          webhooks_last_24h: number | null
        }
        Insert: {
          active_alerts?: string[] | null
          checked_at?: string
          failed_webhooks_24h?: number | null
          id?: string
          invalid_signatures_24h?: number | null
          name_duplicates?: number | null
          orphaned_subscriptions?: number | null
          orphaned_transactions?: number | null
          overall_status: string
          total_contacts?: number | null
          webhooks_last_24h?: number | null
        }
        Update: {
          active_alerts?: string[] | null
          checked_at?: string
          failed_webhooks_24h?: number | null
          id?: string
          invalid_signatures_24h?: number | null
          name_duplicates?: number | null
          orphaned_subscriptions?: number | null
          orphaned_transactions?: number | null
          overall_status?: string
          total_contacts?: number | null
          webhooks_last_24h?: number | null
        }
        Relationships: []
      }
      import_audit_log: {
        Row: {
          conflict_reason: string | null
          contact_id: string | null
          created_at: string | null
          created_by: string | null
          fields_updated: string[] | null
          had_conflict: boolean | null
          id: string
          import_batch_id: string
          import_source: string
          new_values: Json | null
          old_values: Json | null
          operation: string
        }
        Insert: {
          conflict_reason?: string | null
          contact_id?: string | null
          created_at?: string | null
          created_by?: string | null
          fields_updated?: string[] | null
          had_conflict?: boolean | null
          id?: string
          import_batch_id: string
          import_source: string
          new_values?: Json | null
          old_values?: Json | null
          operation: string
        }
        Update: {
          conflict_reason?: string | null
          contact_id?: string | null
          created_at?: string | null
          created_by?: string | null
          fields_updated?: string[] | null
          had_conflict?: boolean | null
          id?: string
          import_batch_id?: string
          import_source?: string
          new_values?: Json | null
          old_values?: Json | null
          operation?: string
        }
        Relationships: [
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_audit_log_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      import_conflicts: {
        Row: {
          conflict_type: string
          contact_id: string | null
          created_at: string | null
          db_value: string | null
          field_name: string
          id: string
          import_batch_id: string
          import_source: string
          import_value: string | null
          resolution: string | null
          resolved: boolean | null
          resolved_at: string | null
          resolved_by: string | null
        }
        Insert: {
          conflict_type: string
          contact_id?: string | null
          created_at?: string | null
          db_value?: string | null
          field_name: string
          id?: string
          import_batch_id: string
          import_source: string
          import_value?: string | null
          resolution?: string | null
          resolved?: boolean | null
          resolved_at?: string | null
          resolved_by?: string | null
        }
        Update: {
          conflict_type?: string
          contact_id?: string | null
          created_at?: string | null
          db_value?: string | null
          field_name?: string
          id?: string
          import_batch_id?: string
          import_source?: string
          import_value?: string | null
          resolution?: string | null
          resolved?: boolean | null
          resolved_at?: string | null
          resolved_by?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "import_conflicts_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      import_lock_rules: {
        Row: {
          allows_address_update: boolean
          allows_enriched_data_update: boolean
          allows_name_update: boolean
          allows_source_system_update: boolean
          allows_subscription_update: boolean
          description: string
          lock_level: string
        }
        Insert: {
          allows_address_update: boolean
          allows_enriched_data_update: boolean
          allows_name_update: boolean
          allows_source_system_update: boolean
          allows_subscription_update: boolean
          description: string
          lock_level: string
        }
        Update: {
          allows_address_update?: boolean
          allows_enriched_data_update?: boolean
          allows_name_update?: boolean
          allows_source_system_update?: boolean
          allows_subscription_update?: boolean
          description?: string
          lock_level?: string
        }
        Relationships: []
      }
      jobs: {
        Row: {
          completed_at: string | null
          created_at: string
          error_details: Json | null
          error_message: string | null
          failed_items: number | null
          id: string
          payload: Json
          processed_items: number | null
          result: Json | null
          started_at: string | null
          status: Database["public"]["Enums"]["job_status"]
          total_items: number | null
          type: Database["public"]["Enums"]["job_type"]
          updated_at: string
          user_email: string | null
          user_id: string | null
        }
        Insert: {
          completed_at?: string | null
          created_at?: string
          error_details?: Json | null
          error_message?: string | null
          failed_items?: number | null
          id?: string
          payload: Json
          processed_items?: number | null
          result?: Json | null
          started_at?: string | null
          status?: Database["public"]["Enums"]["job_status"]
          total_items?: number | null
          type: Database["public"]["Enums"]["job_type"]
          updated_at?: string
          user_email?: string | null
          user_id?: string | null
        }
        Update: {
          completed_at?: string | null
          created_at?: string
          error_details?: Json | null
          error_message?: string | null
          failed_items?: number | null
          id?: string
          payload?: Json
          processed_items?: number | null
          result?: Json | null
          started_at?: string | null
          status?: Database["public"]["Enums"]["job_status"]
          total_items?: number | null
          type?: Database["public"]["Enums"]["job_type"]
          updated_at?: string
          user_email?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
      membership_products: {
        Row: {
          annual_price: number | null
          created_at: string
          description: string | null
          features: Json | null
          id: string
          is_active: boolean | null
          is_legacy: boolean | null
          membership_group: string
          membership_level: string
          membership_tier: string
          monthly_price: number | null
          paypal_item_titles: string[]
          product_name: string
          product_slug: string
          sort_order: number | null
          updated_at: string
        }
        Insert: {
          annual_price?: number | null
          created_at?: string
          description?: string | null
          features?: Json | null
          id?: string
          is_active?: boolean | null
          is_legacy?: boolean | null
          membership_group: string
          membership_level: string
          membership_tier: string
          monthly_price?: number | null
          paypal_item_titles: string[]
          product_name: string
          product_slug: string
          sort_order?: number | null
          updated_at?: string
        }
        Update: {
          annual_price?: number | null
          created_at?: string
          description?: string | null
          features?: Json | null
          id?: string
          is_active?: boolean | null
          is_legacy?: boolean | null
          membership_group?: string
          membership_level?: string
          membership_tier?: string
          monthly_price?: number | null
          paypal_item_titles?: string[]
          product_name?: string
          product_slug?: string
          sort_order?: number | null
          updated_at?: string
        }
        Relationships: []
      }
      products: {
        Row: {
          active: boolean | null
          archived_at: string | null
          created_at: string
          deleted_at: string | null
          description: string | null
          id: string
          kajabi_offer_id: string | null
          name: string
          name_norm: string | null
          product_type: string | null
          updated_at: string
        }
        Insert: {
          active?: boolean | null
          archived_at?: string | null
          created_at?: string
          deleted_at?: string | null
          description?: string | null
          id?: string
          kajabi_offer_id?: string | null
          name: string
          name_norm?: string | null
          product_type?: string | null
          updated_at?: string
        }
        Update: {
          active?: boolean | null
          archived_at?: string | null
          created_at?: string
          deleted_at?: string | null
          description?: string | null
          id?: string
          kajabi_offer_id?: string | null
          name?: string
          name_norm?: string | null
          product_type?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      saved_views: {
        Row: {
          columns: Json | null
          created_at: string
          entity: string
          filters: Json
          id: string
          is_default: boolean | null
          name: string
          share_scope: string | null
          sort: Json | null
          updated_at: string
          user_id: string
        }
        Insert: {
          columns?: Json | null
          created_at?: string
          entity: string
          filters?: Json
          id?: string
          is_default?: boolean | null
          name: string
          share_scope?: string | null
          sort?: Json | null
          updated_at?: string
          user_id: string
        }
        Update: {
          columns?: Json | null
          created_at?: string
          entity?: string
          filters?: Json
          id?: string
          is_default?: boolean | null
          name?: string
          share_scope?: string | null
          sort?: Json | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      staff_members: {
        Row: {
          active: boolean
          added_at: string
          added_by: string | null
          deactivated_at: string | null
          deactivated_by: string | null
          email: string
          notes: string | null
          role: string
        }
        Insert: {
          active?: boolean
          added_at?: string
          added_by?: string | null
          deactivated_at?: string | null
          deactivated_by?: string | null
          email: string
          notes?: string | null
          role?: string
        }
        Update: {
          active?: boolean
          added_at?: string
          added_by?: string | null
          deactivated_at?: string | null
          deactivated_by?: string | null
          email?: string
          notes?: string | null
          role?: string
        }
        Relationships: []
      }
      subscription_restoration_audit: {
        Row: {
          contact_id: string | null
          duplicate_source_system: string | null
          duplicate_was_subscribed: boolean
          email: string
          id: string
          merge_backup_id: number | null
          merged_at: string | null
          new_subscribed: boolean
          old_source_system: string | null
          old_subscribed: boolean
          restoration_reason: string
          restored_at: string | null
          restored_by: string | null
          verified: boolean | null
          verified_at: string | null
          verified_by: string | null
        }
        Insert: {
          contact_id?: string | null
          duplicate_source_system?: string | null
          duplicate_was_subscribed: boolean
          email: string
          id?: string
          merge_backup_id?: number | null
          merged_at?: string | null
          new_subscribed: boolean
          old_source_system?: string | null
          old_subscribed: boolean
          restoration_reason: string
          restored_at?: string | null
          restored_by?: string | null
          verified?: boolean | null
          verified_at?: string | null
          verified_by?: string | null
        }
        Update: {
          contact_id?: string | null
          duplicate_source_system?: string | null
          duplicate_was_subscribed?: boolean
          email?: string
          id?: string
          merge_backup_id?: number | null
          merged_at?: string | null
          new_subscribed?: boolean
          old_source_system?: string | null
          old_subscribed?: boolean
          restoration_reason?: string
          restored_at?: string | null
          restored_by?: string | null
          verified?: boolean | null
          verified_at?: string | null
          verified_by?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscription_restoration_audit_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      subscriptions: {
        Row: {
          amount: number | null
          billing_cycle: string | null
          cancellation_date: string | null
          contact_id: string
          coupon_code: string | null
          created_at: string
          currency: string | null
          deleted_at: string | null
          id: string
          is_annual: boolean | null
          kajabi_subscription_id: string | null
          membership_product_id: string | null
          next_billing_date: string | null
          payment_processor: string | null
          paypal_subscription_reference: string | null
          product_id: string | null
          start_date: string | null
          status: Database["public"]["Enums"]["subscription_status"]
          trial_end_date: string | null
          updated_at: string
        }
        Insert: {
          amount?: number | null
          billing_cycle?: string | null
          cancellation_date?: string | null
          contact_id: string
          coupon_code?: string | null
          created_at?: string
          currency?: string | null
          deleted_at?: string | null
          id?: string
          is_annual?: boolean | null
          kajabi_subscription_id?: string | null
          membership_product_id?: string | null
          next_billing_date?: string | null
          payment_processor?: string | null
          paypal_subscription_reference?: string | null
          product_id?: string | null
          start_date?: string | null
          status?: Database["public"]["Enums"]["subscription_status"]
          trial_end_date?: string | null
          updated_at?: string
        }
        Update: {
          amount?: number | null
          billing_cycle?: string | null
          cancellation_date?: string | null
          contact_id?: string
          coupon_code?: string | null
          created_at?: string
          currency?: string | null
          deleted_at?: string | null
          id?: string
          is_annual?: boolean | null
          kajabi_subscription_id?: string | null
          membership_product_id?: string | null
          next_billing_date?: string | null
          payment_processor?: string | null
          paypal_subscription_reference?: string | null
          product_id?: string | null
          start_date?: string | null
          status?: Database["public"]["Enums"]["subscription_status"]
          trial_end_date?: string | null
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscriptions_membership_product_id_fkey"
            columns: ["membership_product_id"]
            isOneToOne: false
            referencedRelation: "membership_products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "v_active_products"
            referencedColumns: ["id"]
          },
        ]
      }
      subscriptions_dedup_backup: {
        Row: {
          backed_up_at: string | null
          backup_id: number
          contact_email: string | null
          contact_name: string | null
          reason: string
          subscription_data: Json
          subscription_id: string
        }
        Insert: {
          backed_up_at?: string | null
          backup_id?: number
          contact_email?: string | null
          contact_name?: string | null
          reason: string
          subscription_data: Json
          subscription_id: string
        }
        Update: {
          backed_up_at?: string | null
          backup_id?: number
          contact_email?: string | null
          contact_name?: string | null
          reason?: string
          subscription_data?: Json
          subscription_id?: string
        }
        Relationships: []
      }
      tags: {
        Row: {
          category: string | null
          created_at: string
          deleted_at: string | null
          description: string | null
          id: string
          name: string
          name_norm: string | null
          updated_at: string
        }
        Insert: {
          category?: string | null
          created_at?: string
          deleted_at?: string | null
          description?: string | null
          id?: string
          name: string
          name_norm?: string | null
          updated_at?: string
        }
        Update: {
          category?: string | null
          created_at?: string
          deleted_at?: string | null
          description?: string | null
          id?: string
          name?: string
          name_norm?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      transactions: {
        Row: {
          amount: number
          contact_id: string
          coupon_code: string | null
          created_at: string
          currency: string | null
          deleted_at: string | null
          external_order_id: string | null
          external_transaction_id: string | null
          id: string
          kajabi_transaction_id: string | null
          order_number: string | null
          payment_method: string | null
          payment_processor: string | null
          product_id: string | null
          quantity: number | null
          raw_source: Json | null
          source_system: string
          status: Database["public"]["Enums"]["payment_status"]
          subscription_id: string | null
          tax_amount: number | null
          transaction_date: string
          transaction_type: Database["public"]["Enums"]["transaction_type"]
          updated_at: string
        }
        Insert: {
          amount: number
          contact_id: string
          coupon_code?: string | null
          created_at?: string
          currency?: string | null
          deleted_at?: string | null
          external_order_id?: string | null
          external_transaction_id?: string | null
          id?: string
          kajabi_transaction_id?: string | null
          order_number?: string | null
          payment_method?: string | null
          payment_processor?: string | null
          product_id?: string | null
          quantity?: number | null
          raw_source?: Json | null
          source_system?: string
          status?: Database["public"]["Enums"]["payment_status"]
          subscription_id?: string | null
          tax_amount?: number | null
          transaction_date?: string
          transaction_type?: Database["public"]["Enums"]["transaction_type"]
          updated_at?: string
        }
        Update: {
          amount?: number
          contact_id?: string
          coupon_code?: string | null
          created_at?: string
          currency?: string | null
          deleted_at?: string | null
          external_order_id?: string | null
          external_transaction_id?: string | null
          id?: string
          kajabi_transaction_id?: string | null
          order_number?: string | null
          payment_method?: string | null
          payment_processor?: string | null
          product_id?: string | null
          quantity?: number | null
          raw_source?: Json | null
          source_system?: string
          status?: Database["public"]["Enums"]["payment_status"]
          subscription_id?: string | null
          tax_amount?: number | null
          transaction_date?: string
          transaction_type?: Database["public"]["Enums"]["transaction_type"]
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "transactions_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "v_active_products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_subscription_id_fkey"
            columns: ["subscription_id"]
            isOneToOne: false
            referencedRelation: "subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_subscription_id_fkey"
            columns: ["subscription_id"]
            isOneToOne: false
            referencedRelation: "v_active_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_subscription_id_fkey"
            columns: ["subscription_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["subscription_id"]
          },
        ]
      }
      webhook_events: {
        Row: {
          contact_id: string | null
          created_at: string
          error_code: string | null
          error_message: string | null
          event_type: string
          id: string
          ip_address: string | null
          payload_hash: string
          payload_size: number | null
          processed_at: string
          processing_duration_ms: number | null
          provider_event_id: string | null
          received_at: string
          request_id: string
          signature_header: string | null
          signature_valid: boolean
          source: string
          status: string
          subscription_id: string | null
          transaction_id: string | null
          updated_at: string
          user_agent: string | null
          webhook_id: string
          webhook_timestamp: string | null
        }
        Insert: {
          contact_id?: string | null
          created_at?: string
          error_code?: string | null
          error_message?: string | null
          event_type: string
          id?: string
          ip_address?: string | null
          payload_hash: string
          payload_size?: number | null
          processed_at?: string
          processing_duration_ms?: number | null
          provider_event_id?: string | null
          received_at?: string
          request_id?: string
          signature_header?: string | null
          signature_valid?: boolean
          source: string
          status?: string
          subscription_id?: string | null
          transaction_id?: string | null
          updated_at?: string
          user_agent?: string | null
          webhook_id: string
          webhook_timestamp?: string | null
        }
        Update: {
          contact_id?: string | null
          created_at?: string
          error_code?: string | null
          error_message?: string | null
          event_type?: string
          id?: string
          ip_address?: string | null
          payload_hash?: string
          payload_size?: number | null
          processed_at?: string
          processing_duration_ms?: number | null
          provider_event_id?: string | null
          received_at?: string
          request_id?: string
          signature_header?: string | null
          signature_valid?: boolean
          source?: string
          status?: string
          subscription_id?: string | null
          transaction_id?: string | null
          updated_at?: string
          user_agent?: string | null
          webhook_id?: string
          webhook_timestamp?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "webhook_events_subscription_id_fkey"
            columns: ["subscription_id"]
            isOneToOne: false
            referencedRelation: "subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_subscription_id_fkey"
            columns: ["subscription_id"]
            isOneToOne: false
            referencedRelation: "v_active_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_subscription_id_fkey"
            columns: ["subscription_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["subscription_id"]
          },
          {
            foreignKeyName: "webhook_events_transaction_id_fkey"
            columns: ["transaction_id"]
            isOneToOne: false
            referencedRelation: "transactions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_transaction_id_fkey"
            columns: ["transaction_id"]
            isOneToOne: false
            referencedRelation: "v_potential_duplicate_transactions"
            referencedColumns: ["transaction_1_id"]
          },
          {
            foreignKeyName: "webhook_events_transaction_id_fkey"
            columns: ["transaction_id"]
            isOneToOne: false
            referencedRelation: "v_potential_duplicate_transactions"
            referencedColumns: ["transaction_2_id"]
          },
          {
            foreignKeyName: "webhook_events_transaction_id_fkey"
            columns: ["transaction_id"]
            isOneToOne: false
            referencedRelation: "v_transactions_missing_provenance"
            referencedColumns: ["id"]
          },
        ]
      }
      webhook_nonces: {
        Row: {
          created_at: string
          id: string
          nonce: string
          source: string
        }
        Insert: {
          created_at?: string
          id?: string
          nonce: string
          source: string
        }
        Update: {
          created_at?: string
          id?: string
          nonce?: string
          source?: string
        }
        Relationships: []
      }
      webhook_rate_limits: {
        Row: {
          bucket_key: string
          capacity: number
          last_refill: string
          refill_rate: number
          source: string
          tokens: number
        }
        Insert: {
          bucket_key: string
          capacity: number
          last_refill: string
          refill_rate: number
          source: string
          tokens: number
        }
        Update: {
          bucket_key?: string
          capacity?: number
          last_refill?: string
          refill_rate?: number
          source?: string
          tokens?: number
        }
        Relationships: []
      }
    }
    Views: {
      address_verification_stats: {
        Row: {
          address_type: string | null
          source: string | null
          total_addresses: number | null
          verified_count: number | null
          verified_pct: number | null
        }
        Relationships: []
      }
      dlq_ready_for_retry: {
        Row: {
          created_at: string | null
          error_code: string | null
          event_type: string | null
          id: string | null
          max_retries: number | null
          next_retry_at: string | null
          retry_count: number | null
          source: string | null
        }
        Relationships: []
      }
      dlq_summary: {
        Row: {
          error_code: string | null
          exhausted_count: number | null
          latest_error_at: string | null
          oldest_error_at: string | null
          retryable_count: number | null
          source: string | null
          total_events: number | null
          unresolved_count: number | null
        }
        Relationships: []
      }
      email_sync_health: {
        Row: {
          count: string | null
          metric: string | null
        }
        Relationships: []
      }
      error_code_distribution: {
        Row: {
          affected_sources: number | null
          avg_retries_needed: number | null
          error_code: string | null
          first_seen: string | null
          last_seen: string | null
          occurrences: number | null
        }
        Relationships: []
      }
      mailing_list_export: {
        Row: {
          address_line_1: string | null
          address_line_2: string | null
          address_source: string | null
          billing_complete: boolean | null
          billing_score: number | null
          city: string | null
          confidence: string | null
          country: string | null
          email: string | null
          first_name: string | null
          is_manual_override: boolean | null
          last_name: string | null
          last_transaction_date: string | null
          postal_code: string | null
          shipping_complete: boolean | null
          shipping_score: number | null
          state: string | null
        }
        Relationships: []
      }
      mailing_list_priority: {
        Row: {
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_city: string | null
          billing_complete: boolean | null
          billing_country: string | null
          billing_line1: string | null
          billing_line2: string | null
          billing_score: number | null
          billing_state: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          billing_zip: string | null
          confidence: string | null
          email: string | null
          first_name: string | null
          id: string | null
          is_manual_override: boolean | null
          last_name: string | null
          last_transaction_date: string | null
          preferred_mailing_address: string | null
          recommended_address: string | null
          shipping_address_source: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_complete: boolean | null
          shipping_country: string | null
          shipping_line1: string | null
          shipping_line2: string | null
          shipping_score: number | null
          shipping_state: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          shipping_zip: string | null
        }
        Relationships: []
      }
      mailing_list_quality_issues: {
        Row: {
          billing_usps_dpv_match_code: string | null
          billing_usps_vacant: boolean | null
          email: string | null
          first_name: string | null
          id: string | null
          issue_type: string | null
          last_name: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_vacant: boolean | null
        }
        Insert: {
          billing_usps_dpv_match_code?: string | null
          billing_usps_vacant?: boolean | null
          email?: string | null
          first_name?: string | null
          id?: string | null
          issue_type?: never
          last_name?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_vacant?: boolean | null
        }
        Update: {
          billing_usps_dpv_match_code?: string | null
          billing_usps_vacant?: boolean | null
          email?: string | null
          first_name?: string | null
          id?: string | null
          issue_type?: never
          last_name?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_vacant?: boolean | null
        }
        Relationships: []
      }
      name_sync_health: {
        Row: {
          count: string | null
          metric: string | null
        }
        Relationships: []
      }
      phone_verification_stats: {
        Row: {
          countries: number | null
          source: string | null
          total_phones: number | null
          verified_count: number | null
          verified_pct: number | null
        }
        Relationships: []
      }
      recent_webhook_failures: {
        Row: {
          contact_email: string | null
          contact_id: string | null
          contact_name: string | null
          error_code: string | null
          error_message: string | null
          event_type: string | null
          id: string | null
          received_at: string | null
          source: string | null
        }
        Relationships: [
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "webhook_events_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      v_active_contacts: {
        Row: {
          additional_email: string | null
          additional_email_source: string | null
          additional_name: string | null
          additional_name_source: string | null
          additional_phone: string | null
          additional_phone_source: string | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          billing_usps_active: boolean | null
          billing_usps_county: string | null
          billing_usps_delivery_line_1: string | null
          billing_usps_delivery_line_2: string | null
          billing_usps_dpv_match_code: string | null
          billing_usps_footnotes: string | null
          billing_usps_last_line: string | null
          billing_usps_latitude: number | null
          billing_usps_longitude: number | null
          billing_usps_precision: string | null
          billing_usps_rdi: string | null
          billing_usps_vacant: boolean | null
          billing_usps_validated_at: string | null
          city: string | null
          country: string | null
          created_at: string | null
          deleted_at: string | null
          email: string | null
          email_subscribed: boolean | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          id: string | null
          is_legacy_member: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_name: string | null
          last_transaction_date: string | null
          mailchimp_id: string | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          notes: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          quickbooks_id: string | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          shipping_usps_active: boolean | null
          shipping_usps_county: string | null
          shipping_usps_delivery_line_1: string | null
          shipping_usps_delivery_line_2: string | null
          shipping_usps_dpv_match_code: string | null
          shipping_usps_footnotes: string | null
          shipping_usps_last_line: string | null
          shipping_usps_latitude: number | null
          shipping_usps_longitude: number | null
          shipping_usps_precision: string | null
          shipping_usps_rdi: string | null
          shipping_usps_vacant: boolean | null
          shipping_usps_validated_at: string | null
          source_system: string | null
          state: string | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          updated_at: string | null
          zipcode: string | null
          zoho_email: string | null
          zoho_id: string | null
          zoho_phone: string | null
          zoho_phone_source: string | null
        }
        Insert: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          country?: string | null
          created_at?: string | null
          deleted_at?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          id?: string | null
          is_legacy_member?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          mailchimp_id?: string | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          quickbooks_id?: string | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          updated_at?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Update: {
          additional_email?: string | null
          additional_email_source?: string | null
          additional_name?: string | null
          additional_name_source?: string | null
          additional_phone?: string | null
          additional_phone_source?: string | null
          address?: string | null
          address_2?: string | null
          address_line_1?: string | null
          address_line_2?: string | null
          billing_address_source?: string | null
          billing_address_updated_at?: string | null
          billing_address_verified?: boolean | null
          billing_usps_active?: boolean | null
          billing_usps_county?: string | null
          billing_usps_delivery_line_1?: string | null
          billing_usps_delivery_line_2?: string | null
          billing_usps_dpv_match_code?: string | null
          billing_usps_footnotes?: string | null
          billing_usps_last_line?: string | null
          billing_usps_latitude?: number | null
          billing_usps_longitude?: number | null
          billing_usps_precision?: string | null
          billing_usps_rdi?: string | null
          billing_usps_vacant?: boolean | null
          billing_usps_validated_at?: string | null
          city?: string | null
          country?: string | null
          created_at?: string | null
          deleted_at?: string | null
          email?: string | null
          email_subscribed?: boolean | null
          favorite_payment_method?: string | null
          first_name?: string | null
          first_transaction_date?: string | null
          has_active_subscription?: boolean | null
          id?: string | null
          is_legacy_member?: boolean | null
          kajabi_id?: string | null
          kajabi_member_id?: string | null
          last_name?: string | null
          last_transaction_date?: string | null
          mailchimp_id?: string | null
          membership_group?: string | null
          membership_level?: string | null
          membership_tier?: string | null
          notes?: string | null
          paypal_business_name?: string | null
          paypal_email?: string | null
          paypal_first_name?: string | null
          paypal_last_name?: string | null
          paypal_payer_id?: string | null
          paypal_phone?: string | null
          paypal_subscription_reference?: string | null
          phone?: string | null
          phone_country_code?: string | null
          phone_source?: string | null
          phone_verified?: boolean | null
          postal_code?: string | null
          quickbooks_id?: string | null
          shipping_address_line_1?: string | null
          shipping_address_line_2?: string | null
          shipping_address_source?: string | null
          shipping_address_status?: string | null
          shipping_address_updated_at?: string | null
          shipping_address_verified?: boolean | null
          shipping_city?: string | null
          shipping_country?: string | null
          shipping_postal_code?: string | null
          shipping_state?: string | null
          shipping_usps_active?: boolean | null
          shipping_usps_county?: string | null
          shipping_usps_delivery_line_1?: string | null
          shipping_usps_delivery_line_2?: string | null
          shipping_usps_dpv_match_code?: string | null
          shipping_usps_footnotes?: string | null
          shipping_usps_last_line?: string | null
          shipping_usps_latitude?: number | null
          shipping_usps_longitude?: number | null
          shipping_usps_precision?: string | null
          shipping_usps_rdi?: string | null
          shipping_usps_vacant?: boolean | null
          shipping_usps_validated_at?: string | null
          source_system?: string | null
          state?: string | null
          ticket_tailor_id?: string | null
          total_coupons_used?: number | null
          total_spent?: number | null
          transaction_count?: number | null
          updated_at?: string | null
          zipcode?: string | null
          zoho_email?: string | null
          zoho_id?: string | null
          zoho_phone?: string | null
          zoho_phone_source?: string | null
        }
        Relationships: []
      }
      v_active_members: {
        Row: {
          billing_cycle: string | null
          contact_id: string | null
          email: string | null
          first_name: string | null
          last_name: string | null
          last_payment_date: string | null
          lifetime_value: number | null
          member_since: string | null
          membership_fee: number | null
          membership_status: string | null
          next_billing_date: string | null
        }
        Relationships: []
      }
      v_active_products: {
        Row: {
          active: boolean | null
          archived_at: string | null
          created_at: string | null
          deleted_at: string | null
          description: string | null
          id: string | null
          kajabi_offer_id: string | null
          name: string | null
          name_norm: string | null
          product_type: string | null
          updated_at: string | null
        }
        Insert: {
          active?: boolean | null
          archived_at?: string | null
          created_at?: string | null
          deleted_at?: string | null
          description?: string | null
          id?: string | null
          kajabi_offer_id?: string | null
          name?: string | null
          name_norm?: string | null
          product_type?: string | null
          updated_at?: string | null
        }
        Update: {
          active?: boolean | null
          archived_at?: string | null
          created_at?: string | null
          deleted_at?: string | null
          description?: string | null
          id?: string | null
          kajabi_offer_id?: string | null
          name?: string | null
          name_norm?: string | null
          product_type?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      v_active_subscriptions: {
        Row: {
          amount: number | null
          billing_cycle: string | null
          cancellation_date: string | null
          contact_id: string | null
          coupon_code: string | null
          created_at: string | null
          currency: string | null
          email: string | null
          first_name: string | null
          id: string | null
          kajabi_subscription_id: string | null
          last_name: string | null
          next_billing_date: string | null
          payment_processor: string | null
          product_id: string | null
          product_name: string | null
          start_date: string | null
          status: Database["public"]["Enums"]["subscription_status"] | null
          trial_end_date: string | null
          updated_at: string | null
        }
        Relationships: [
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "subscriptions_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "subscriptions_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "v_active_products"
            referencedColumns: ["id"]
          },
        ]
      }
      v_contact_detail_enriched: {
        Row: {
          active_role_count: number | null
          active_roles: string[] | null
          address: string | null
          address_2: string | null
          address_line_1: string | null
          address_line_2: string | null
          all_emails: Json | null
          billing_address_source: string | null
          billing_address_updated_at: string | null
          billing_address_verified: boolean | null
          city: string | null
          country: string | null
          created_at: string | null
          email: string | null
          email_subscribed: boolean | null
          external_identities: Json | null
          favorite_payment_method: string | null
          first_name: string | null
          first_transaction_date: string | null
          has_active_subscription: boolean | null
          id: string | null
          is_attendee: boolean | null
          is_donor: boolean | null
          is_legacy_member: boolean | null
          is_member: boolean | null
          is_subscriber: boolean | null
          is_volunteer: boolean | null
          kajabi_id: string | null
          kajabi_member_id: string | null
          last_activity_at: string | null
          last_name: string | null
          last_transaction_date: string | null
          mailchimp_id: string | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          note_count: number | null
          notes: string | null
          outreach_deliverable: boolean | null
          outreach_email: string | null
          outreach_source: string | null
          paypal_business_name: string | null
          paypal_email: string | null
          paypal_first_name: string | null
          paypal_last_name: string | null
          paypal_payer_id: string | null
          paypal_phone: string | null
          paypal_subscription_reference: string | null
          phone: string | null
          phone_country_code: string | null
          phone_source: string | null
          phone_verified: boolean | null
          postal_code: string | null
          primary_email: string | null
          quickbooks_id: string | null
          shipping_address_line_1: string | null
          shipping_address_line_2: string | null
          shipping_address_source: string | null
          shipping_address_status: string | null
          shipping_address_updated_at: string | null
          shipping_address_verified: boolean | null
          shipping_city: string | null
          shipping_country: string | null
          shipping_postal_code: string | null
          shipping_state: string | null
          source_system: string | null
          state: string | null
          subscription_count: number | null
          tag_count: number | null
          ticket_tailor_id: string | null
          total_coupons_used: number | null
          total_spent: number | null
          transaction_count: number | null
          transaction_count_actual: number | null
          updated_at: string | null
          webhook_event_count: number | null
          zipcode: string | null
          zoho_id: string | null
        }
        Relationships: []
      }
      v_contact_list_optimized: {
        Row: {
          active_roles: string[] | null
          created_at: string | null
          email: string | null
          email_subscribed: boolean | null
          first_name: string | null
          full_name: string | null
          has_active_subscription: boolean | null
          id: string | null
          is_donor: boolean | null
          is_member: boolean | null
          is_volunteer: boolean | null
          last_name: string | null
          last_transaction_date: string | null
          membership_level: string | null
          membership_tier: string | null
          outreach_source: string | null
          total_spent: number | null
          transaction_count: number | null
          updated_at: string | null
        }
        Relationships: []
      }
      v_contact_list_with_subscriptions: {
        Row: {
          active_roles: string[] | null
          created_at: string | null
          email: string | null
          email_subscribed: boolean | null
          first_name: string | null
          full_name: string | null
          has_active_subscription: boolean | null
          id: string | null
          is_annual: boolean | null
          is_donor: boolean | null
          is_legacy: boolean | null
          is_member: boolean | null
          is_volunteer: boolean | null
          last_name: string | null
          last_transaction_date: string | null
          member_since: string | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          outreach_source: string | null
          subscription_amount: number | null
          subscription_currency: string | null
          subscription_status:
            | Database["public"]["Enums"]["subscription_status"]
            | null
          total_spent: number | null
          transaction_count: number | null
          updated_at: string | null
        }
        Relationships: []
      }
      v_contact_outreach_email: {
        Row: {
          contact_id: string | null
          is_deliverable: boolean | null
          outreach_email: string | null
          outreach_email_bounced: boolean | null
          outreach_source: string | null
          total_email_count: number | null
        }
        Insert: {
          contact_id?: string | null
          is_deliverable?: never
          outreach_email?: never
          outreach_email_bounced?: never
          outreach_source?: never
          total_email_count?: never
        }
        Update: {
          contact_id?: string | null
          is_deliverable?: never
          outreach_email?: never
          outreach_email_bounced?: never
          outreach_source?: never
          total_email_count?: never
        }
        Relationships: []
      }
      v_contact_roles_quick: {
        Row: {
          active_role_count: number | null
          active_roles: string[] | null
          contact_id: string | null
          is_attendee: boolean | null
          is_board: boolean | null
          is_donor: boolean | null
          is_member: boolean | null
          is_partner: boolean | null
          is_staff: boolean | null
          is_subscriber: boolean | null
          is_volunteer: boolean | null
          latest_role_started_at: string | null
          latest_role_updated_at: string | null
        }
        Relationships: [
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "contact_roles_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      v_contact_summary: {
        Row: {
          email: string | null
          first_name: string | null
          id: string | null
          last_name: string | null
          last_transaction_date: string | null
          product_count: number | null
          subscription_count: number | null
          tag_count: number | null
          total_revenue: number | null
          transaction_count: number | null
        }
        Relationships: []
      }
      v_database_health: {
        Row: {
          active_alerts: string[] | null
          avg_webhook_processing_ms: number | null
          checked_at: string | null
          contacts_added_today: number | null
          contacts_updated_today: number | null
          failed_webhooks_24h: number | null
          invalid_signatures_24h: number | null
          name_duplicates: number | null
          orphaned_subscriptions: number | null
          orphaned_transactions: number | null
          overall_status: string | null
          revenue_last_30_days: number | null
          total_contacts: number | null
          total_transactions: number | null
          transactions_last_7_days: number | null
          webhooks_last_24h: number | null
        }
        Relationships: []
      }
      v_failed_webhooks: {
        Row: {
          error_code: string | null
          error_message: string | null
          event_type: string | null
          ip_address: string | null
          processing_duration_ms: number | null
          provider_event_id: string | null
          received_at: string | null
          request_id: string | null
          signature_valid: boolean | null
          source: string | null
          webhook_id: string | null
        }
        Relationships: []
      }
      v_membership_metrics: {
        Row: {
          active_members: number | null
          avg_membership_fee: number | null
          cancelled_last_30_days: number | null
          cancelled_members: number | null
          expired_members: number | null
          grace_period_members: number | null
          last_updated: string | null
          monthly_members: number | null
          monthly_recurring_revenue: number | null
          new_members_last_30_days: number | null
          non_members: number | null
          overdue_members: number | null
          paused_members: number | null
          renewing_next_7_days: number | null
          total_lifetime_value: number | null
          yearly_members: number | null
        }
        Relationships: []
      }
      v_membership_status: {
        Row: {
          billing_cycle: string | null
          cancellation_date: string | null
          contact_created_at: string | null
          contact_id: string | null
          days_until_billing: unknown
          email: string | null
          first_name: string | null
          kajabi_subscription_id: string | null
          last_name: string | null
          last_payment_date: string | null
          lifetime_value: number | null
          member_since: string | null
          membership_fee: number | null
          membership_status: string | null
          next_billing_date: string | null
          payment_processor: string | null
          start_date: string | null
          subscription_created_at: string | null
          subscription_id: string | null
          subscription_status:
            | Database["public"]["Enums"]["subscription_status"]
            | null
          subscription_updated_at: string | null
        }
        Relationships: []
      }
      v_membership_summary_by_group: {
        Row: {
          active_subscriptions: number | null
          avg_subscription_amount: number | null
          legacy_count: number | null
          member_count: number | null
          membership_group: string | null
          membership_level: string | null
          membership_tier: string | null
          total_monthly_revenue: number | null
        }
        Relationships: []
      }
      v_performance_metrics: {
        Row: {
          active_connections: number | null
          cache_hit_ratio_percent: number | null
          contact_count: number | null
          contacts_size: string | null
          subscription_count: number | null
          subscriptions_size: string | null
          total_database_size: string | null
          transaction_count: number | null
          transactions_size: string | null
          unused_indexes: number | null
          webhook_event_count: number | null
          webhook_events_size: string | null
        }
        Relationships: []
      }
      v_potential_duplicate_contacts: {
        Row: {
          contact_count: number | null
          contact_ids: string[] | null
          email: string | null
        }
        Relationships: []
      }
      v_potential_duplicate_transactions: {
        Row: {
          amount: number | null
          currency: string | null
          date_1: string | null
          date_2: string | null
          duplicate_likelihood: string | null
          email: string | null
          external_id_1: string | null
          external_id_2: string | null
          first_name: string | null
          last_name: string | null
          order_id_1: string | null
          order_id_2: string | null
          seconds_apart: number | null
          source_1: string | null
          source_2: string | null
          transaction_1_id: string | null
          transaction_2_id: string | null
        }
        Relationships: []
      }
      v_rate_limit_status: {
        Row: {
          bucket_key: string | null
          capacity: number | null
          last_refill: string | null
          refill_rate: number | null
          requests_per_minute: number | null
          source: string | null
          status: string | null
          time_since_last_request: unknown
          token_percentage: number | null
          tokens: number | null
        }
        Insert: {
          bucket_key?: string | null
          capacity?: number | null
          last_refill?: string | null
          refill_rate?: number | null
          requests_per_minute?: never
          source?: string | null
          status?: never
          time_since_last_request?: never
          token_percentage?: never
          tokens?: number | null
        }
        Update: {
          bucket_key?: string | null
          capacity?: number | null
          last_refill?: string | null
          refill_rate?: number | null
          requests_per_minute?: never
          source?: string | null
          status?: never
          time_since_last_request?: never
          token_percentage?: never
          tokens?: number | null
        }
        Relationships: []
      }
      v_recent_health_alerts: {
        Row: {
          active_alerts: string[] | null
          checked_at: string | null
          failed_webhooks_24h: number | null
          invalid_signatures_24h: number | null
          name_duplicates: number | null
          orphaned_subscriptions: number | null
          orphaned_transactions: number | null
          overall_status: string | null
          total_contacts: number | null
        }
        Relationships: []
      }
      v_revenue_by_source: {
        Row: {
          avg_transaction: number | null
          first_transaction: string | null
          gross_revenue: number | null
          last_transaction: string | null
          net_revenue: number | null
          refunds: number | null
          source_system: string | null
          transaction_count: number | null
          unique_customers: number | null
        }
        Relationships: []
      }
      v_system_health: {
        Row: {
          active_subscriptions: number | null
          completed_transactions: number | null
          paying_customers: number | null
          total_contacts: number | null
          total_revenue: number | null
        }
        Relationships: []
      }
      v_transactions_missing_provenance: {
        Row: {
          amount: number | null
          contact_id: string | null
          created_at: string | null
          external_order_id: string | null
          external_transaction_id: string | null
          id: string | null
          issue: string | null
          source_system: string | null
          transaction_date: string | null
        }
        Insert: {
          amount?: number | null
          contact_id?: string | null
          created_at?: string | null
          external_order_id?: string | null
          external_transaction_id?: string | null
          id?: string | null
          issue?: never
          source_system?: string | null
          transaction_date?: string | null
        }
        Update: {
          amount?: number | null
          contact_id?: string | null
          created_at?: string | null
          external_order_id?: string | null
          external_transaction_id?: string | null
          id?: string | null
          issue?: never
          source_system?: string | null
          transaction_date?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_priority"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "mailing_list_quality_issues"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_contacts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_active_members"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_detail_enriched"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_optimized"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_list_with_subscriptions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_outreach_email"
            referencedColumns: ["contact_id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_contact_summary"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "transactions_contact_id_fkey"
            columns: ["contact_id"]
            isOneToOne: false
            referencedRelation: "v_membership_status"
            referencedColumns: ["contact_id"]
          },
        ]
      }
      v_webhook_security_alerts: {
        Row: {
          alert_type: string | null
          error_message: string | null
          event_type: string | null
          ip_address: string | null
          provider_event_id: string | null
          received_at: string | null
          request_id: string | null
          signature_valid: boolean | null
          source: string | null
          webhook_id: string | null
          webhook_timestamp: string | null
        }
        Relationships: []
      }
      webhook_health_24h: {
        Row: {
          avg_duration_ms: number | null
          failed_count: number | null
          last_event_at: string | null
          max_duration_ms: number | null
          source: string | null
          success_count: number | null
          success_pct: number | null
          time_since_last_event: unknown
          total_events: number | null
        }
        Relationships: []
      }
    }
    Functions: {
      add_contact_tag: {
        Args: { p_contact_id: string; p_new_tag: string }
        Returns: Json
      }
      add_staff_member: {
        Args: { p_email: string; p_notes?: string; p_role?: string }
        Returns: Json
      }
      bulk_add_contact_tags: {
        Args: { p_contact_id: string; p_new_tags: string[] }
        Returns: Json
      }
      calculate_address_score: {
        Args: { address_type: string; contact_id: string }
        Returns: number
      }
      checkout_rate_limit: {
        Args: {
          p_bucket_key: string
          p_default_capacity?: number
          p_default_refill_rate?: number
          p_source: string
        }
        Returns: boolean
      }
      cleanup_old_nonces: { Args: never; Returns: number }
      cleanup_old_webhook_events: { Args: never; Returns: number }
      cleanup_stale_rate_limits: { Args: never; Returns: number }
      daily_health_check: {
        Args: never
        Returns: {
          metric: string
          recommendation: string
          status: string
          threshold: string
          value: string
        }[]
      }
      deactivate_staff_member: { Args: { p_email: string }; Returns: Json }
      find_contact_by_any_email: {
        Args: { search_email: string }
        Returns: string
      }
      find_duplicates_batch: {
        Args: { emails: string[] }
        Returns: {
          found_contact_id: string
          match_field: string
          search_email: string
        }[]
      }
      find_probable_duplicate_transaction: {
        Args: {
          p_amount: number
          p_contact_id: string
          p_source_system: string
          p_transaction_date: string
          p_window_minutes?: number
        }
        Returns: string
      }
      get_active_member_emails: {
        Args: never
        Returns: {
          email: string
          first_name: string
          last_name: string
        }[]
      }
      get_contact_activity: {
        Args: { p_contact_id: string; p_limit?: number; p_offset?: number }
        Returns: {
          activity_date: string
          activity_id: string
          activity_name: string
          activity_status: string
          activity_type: string
          amount: number
          details: string
          metadata: Json
          source_table: string
        }[]
      }
      get_membership_product_from_title: {
        Args: { item_title: string }
        Returns: {
          annual_price: number
          is_legacy: boolean
          membership_group: string
          membership_level: string
          membership_tier: string
          monthly_price: number
          product_id: string
          product_name: string
        }[]
      }
      get_membership_status: { Args: { p_contact_id: string }; Returns: string }
      get_rate_limit_info: {
        Args: { p_bucket_key: string; p_source: string }
        Returns: {
          bucket_key: string
          capacity: number
          current_tokens: number
          estimated_requests_per_minute: number
          last_refill: string
          refill_rate: number
          seconds_until_next_token: number
          source: string
        }[]
      }
      get_webhook_stats: {
        Args: { p_hours?: number }
        Returns: {
          avg_duration_ms: number
          duplicates: number
          failed: number
          invalid_signatures: number
          p50_duration_ms: number
          p95_duration_ms: number
          p99_duration_ms: number
          replays_blocked: number
          source: string
          successful: number
          total_webhooks: number
        }[]
      }
      is_address_complete: {
        Args: { address_type: string; contact_id: string }
        Returns: boolean
      }
      is_annual_payment: {
        Args: { amount: number; item_title: string }
        Returns: boolean
      }
      is_current_member: { Args: { p_contact_id: string }; Returns: boolean }
      is_duplicate_payload: {
        Args: { p_payload_hash: string; p_source: string }
        Returns: boolean
      }
      is_nonce_used: {
        Args: { p_nonce: string; p_source: string }
        Returns: boolean
      }
      is_replay_attack: {
        Args: { p_webhook_timestamp: string }
        Returns: boolean
      }
      is_verified_staff: { Args: never; Returns: boolean }
      is_webhook_processed: { Args: { p_webhook_id: string }; Returns: boolean }
      log_health_check: { Args: never; Returns: string }
      process_webhook_atomically: {
        Args: {
          p_event_type: string
          p_nonce: string
          p_payload_hash: string
          p_provider_event_id: string
          p_request_id: string
          p_signature_valid: boolean
          p_source: string
        }
        Returns: {
          is_duplicate: boolean
          message: string
          webhook_event_id: string
        }[]
      }
      promote_to_admin: { Args: { p_email: string }; Returns: Json }
      record_nonce: {
        Args: { p_nonce: string; p_source: string }
        Returns: boolean
      }
      remove_contact_tag: {
        Args: { p_contact_id: string; p_tag_to_remove: string }
        Returns: Json
      }
      replay_dlq_event: {
        Args: { dlq_event_id: string; replayed_by?: string }
        Returns: Json
      }
      replay_dlq_events_bulk: {
        Args: { dlq_event_ids: string[]; replayed_by?: string }
        Returns: Json
      }
      resolve_dlq_event: {
        Args: { dlq_event_id: string; resolved_by_user: string }
        Returns: boolean
      }
      search_contacts: {
        Args: { p_limit?: number; p_offset?: number; p_query: string }
        Returns: {
          contact_id: string
          email: string
          full_name: string
          is_donor: boolean
          is_member: boolean
          match_score: number
          match_type: string
          phone: string
          total_spent: number
        }[]
      }
      set_primary_email: {
        Args: { p_contact_id: string; p_new_primary_email: string }
        Returns: {
          message: string
          new_primary_email: string
          old_primary_email: string
          success: boolean
        }[]
      }
      set_primary_name: {
        Args: { p_contact_id: string; p_new_primary_name: string }
        Returns: {
          message: string
          new_primary_name: string
          old_primary_name: string
          success: boolean
        }[]
      }
      show_limit: { Args: never; Returns: number }
      show_trgm: { Args: { "": string }; Returns: string[] }
      standardize_country_code: {
        Args: { input_country: string }
        Returns: string
      }
      test_rate_limiting: {
        Args: never
        Returns: {
          details: string
          result: string
          test_name: string
        }[]
      }
    }
    Enums: {
      job_status: "pending" | "running" | "completed" | "failed" | "cancelled"
      job_type:
        | "bulk_import"
        | "bulk_export"
        | "bulk_merge"
        | "bulk_tag"
        | "bulk_delete"
        | "report_generation"
        | "data_cleanup"
      payment_status:
        | "pending"
        | "completed"
        | "failed"
        | "refunded"
        | "disputed"
      subscription_status:
        | "active"
        | "paused"
        | "canceled"
        | "expired"
        | "trial"
      transaction_type: "purchase" | "subscription" | "refund" | "adjustment"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      job_status: ["pending", "running", "completed", "failed", "cancelled"],
      job_type: [
        "bulk_import",
        "bulk_export",
        "bulk_merge",
        "bulk_tag",
        "bulk_delete",
        "report_generation",
        "data_cleanup",
      ],
      payment_status: [
        "pending",
        "completed",
        "failed",
        "refunded",
        "disputed",
      ],
      subscription_status: ["active", "paused", "canceled", "expired", "trial"],
      transaction_type: ["purchase", "subscription", "refund", "adjustment"],
    },
  },
} as const
