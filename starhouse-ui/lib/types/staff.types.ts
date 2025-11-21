// Generated from PostgreSQL schema
// DO NOT EDIT MANUALLY - Run generate_typescript_types.py to regenerate

export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]

export type StaffRole = 'admin' | 'full_user' | 'read_only'

export interface StaffMember {
  id: string // UUID - primary key, links to auth.users
  email: string
  role: string
  added_at: string
  added_by: string | null
  notes: string | null
  active: boolean
  deactivated_at: string | null
  deactivated_by: string | null
  display_name: string | null
  // Auth metadata (synced from auth.users)
  last_sign_in_at: string | null
  email_confirmed_at: string | null
  updated_at: string
  // Legacy field - use last_sign_in_at instead
  last_login_at?: string | null
}

export interface Database {
  public: {
    Tables: {
      staff_members: {
        Row: StaffMember
        Insert: Omit<StaffMember, 'added_at'>
        Update: Partial<StaffMember>
      }
    }
    Functions: {
      is_admin: {
        Args: Record<string, never>
        Returns: boolean
      }
      can_edit: {
        Args: Record<string, never>
        Returns: boolean
      }
      get_user_role: {
        Args: Record<string, never>
        Returns: string
      }
      add_staff_member: {
        Args: {
          p_email: string
          p_role?: StaffRole
          p_display_name?: string
          p_notes?: string
        }
        Returns: Json
      }
      change_staff_role: {
        Args: {
          p_email: string
          p_new_role: StaffRole
        }
        Returns: Json
      }
      deactivate_staff_member: {
        Args: {
          p_email: string
        }
        Returns: Json
      }
    }
  }
}
