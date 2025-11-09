// ============================================================================
// SHARED TEST UTILITIES
// ============================================================================
// Purpose: Common mocks, fixtures, and helpers for webhook function testing
// ============================================================================

import { assertEquals, assertExists } from "https://deno.land/std@0.168.0/testing/asserts.ts"

// ============================================================================
// MOCK SUPABASE CLIENT
// ============================================================================

export interface MockQueryBuilder {
  from: (table: string) => any
  select: (columns?: string) => any
  insert: (data: any) => any
  update: (data: any) => any
  delete: () => any
  upsert: (data: any, options?: any) => any
  eq: (column: string, value: any) => any
  single: () => any
  maybeSingle: () => any
  gte: (column: string, value: any) => any
  ilike: (column: string, value: any) => any
}

export class MockSupabaseClient {
  private mockData: Map<string, any[]> = new Map()
  private callLog: any[] = []

  // Track all calls for assertions
  getCalls(): any[] {
    return this.callLog
  }

  // Set mock data for a table
  setMockData(table: string, data: any[]): void {
    this.mockData.set(table, data)
  }

  // Clear all mock data
  clearMockData(): void {
    this.mockData.clear()
    this.callLog = []
  }

  // Main from() method that starts query building
  from(table: string): any {
    this.callLog.push({ method: 'from', table })

    const builder: any = {
      _table: table,
      _operation: null,
      _data: null,
      _filters: [] as any[],
      _columns: '*',
      _singleResult: false,

      select: (columns = '*') => {
        builder._operation = 'select'
        builder._columns = columns
        this.callLog.push({ method: 'select', table, columns })
        return builder
      },

      insert: (data: any) => {
        builder._operation = 'insert'
        builder._data = data
        this.callLog.push({ method: 'insert', table, data })
        return builder
      },

      update: (data: any) => {
        builder._operation = 'update'
        builder._data = data
        this.callLog.push({ method: 'update', table, data })
        return builder
      },

      delete: () => {
        builder._operation = 'delete'
        this.callLog.push({ method: 'delete', table })
        return builder
      },

      upsert: (data: any, options?: any) => {
        builder._operation = 'upsert'
        builder._data = data
        builder._options = options
        this.callLog.push({ method: 'upsert', table, data, options })
        return builder
      },

      eq: (column: string, value: any) => {
        builder._filters.push({ type: 'eq', column, value })
        this.callLog.push({ method: 'eq', table, column, value })
        return builder
      },

      ilike: (column: string, value: any) => {
        builder._filters.push({ type: 'ilike', column, value })
        this.callLog.push({ method: 'ilike', table, column, value })
        return builder
      },

      gte: (column: string, value: any) => {
        builder._filters.push({ type: 'gte', column, value })
        this.callLog.push({ method: 'gte', table, column, value })
        return builder
      },

      single: () => {
        builder._singleResult = true
        this.callLog.push({ method: 'single', table })
        return builder
      },

      maybeSingle: () => {
        builder._singleResult = true
        builder._maybeNull = true
        this.callLog.push({ method: 'maybeSingle', table })
        return builder
      },

      // Execute the query and return mock data
      then: (resolve: any) => {
        const result = this._executeQuery(builder)
        return resolve(result)
      }
    }

    return builder
  }

  // Execute the mock query based on filters
  private _executeQuery(builder: any): { data: any; error: null } | { data: null; error: any } {
    const table = builder._table
    const operation = builder._operation
    const data = builder._data
    const filters = builder._filters
    const singleResult = builder._singleResult

    // Get mock data for table
    let tableData = this.mockData.get(table) || []

    // Handle operations
    switch (operation) {
      case 'select':
        // Apply filters
        let filtered = tableData
        for (const filter of filters) {
          filtered = this._applyFilter(filtered, filter)
        }

        if (singleResult) {
          const record = filtered[0] || null
          if (!record && !builder._maybeNull) {
            return { data: null, error: { code: 'PGRST116', message: 'No rows found' } }
          }
          return { data: record, error: null }
        }

        return { data: filtered, error: null }

      case 'insert':
        const newRecord = { ...data, id: crypto.randomUUID() }
        tableData.push(newRecord)
        this.mockData.set(table, tableData)
        return { data: singleResult ? newRecord : [newRecord], error: null }

      case 'update':
        // Apply filters to find records to update
        let toUpdate = tableData
        for (const filter of filters) {
          toUpdate = this._applyFilter(toUpdate, filter)
        }

        // Update records
        toUpdate.forEach(record => {
          Object.assign(record, data)
        })

        return { data: singleResult ? toUpdate[0] : toUpdate, error: null }

      case 'upsert':
        // Simple upsert: just insert for now
        const upsertRecord = { ...data, id: crypto.randomUUID() }
        tableData.push(upsertRecord)
        this.mockData.set(table, tableData)
        return { data: singleResult ? upsertRecord : [upsertRecord], error: null }

      case 'delete':
        // Apply filters to find records to delete
        let toDelete = tableData
        for (const filter of filters) {
          toDelete = this._applyFilter(toDelete, filter)
        }

        // Remove records
        tableData = tableData.filter(record => !toDelete.includes(record))
        this.mockData.set(table, tableData)

        return { data: singleResult ? toDelete[0] : toDelete, error: null }

      default:
        return { data: null, error: { message: 'Unknown operation' } }
    }
  }

  // Apply a single filter to data
  private _applyFilter(data: any[], filter: any): any[] {
    switch (filter.type) {
      case 'eq':
        return data.filter(record => record[filter.column] === filter.value)

      case 'ilike':
        return data.filter(record => {
          const value = String(record[filter.column] || '').toLowerCase()
          const pattern = String(filter.value).toLowerCase()
          return value.includes(pattern)
        })

      case 'gte':
        return data.filter(record => record[filter.column] >= filter.value)

      default:
        return data
    }
  }
}

// ============================================================================
// MOCK HTTP REQUEST
// ============================================================================

export function createMockRequest(options: {
  method?: string
  body?: any
  headers?: Record<string, string>
  url?: string
}): Request {
  const {
    method = 'POST',
    body = {},
    headers = {},
    url = 'https://test.supabase.co/functions/v1/test'
  } = options

  const bodyString = typeof body === 'string' ? body : JSON.stringify(body)

  return new Request(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers
    },
    body: method !== 'GET' && method !== 'HEAD' ? bodyString : undefined
  })
}

// ============================================================================
// TEST FIXTURES - KAJABI
// ============================================================================

export const kajabiFixtures = {
  orderCreated: {
    event: 'order.created',
    data: {
      id: 'kajabi-txn-123',
      order_number: 'ORD-001',
      status: 'completed',
      member: {
        id: 'member-456',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe'
      },
      payment_transaction: {
        id: 'txn-789',
        amount_paid_decimal: '99.00',
        amount_paid: 9900,
        currency: 'USD',
        payment_method: 'credit_card',
        payment_processor: 'Stripe',
        sales_tax_decimal: '8.91',
        created_at: '2025-01-01T12:00:00Z'
      }
    }
  },

  paymentSucceeded: {
    event: 'payment.succeeded',
    data: {
      id: 'kajabi-payment-999',
      order_number: 'ORD-002',
      status: 'completed',
      member: {
        email: 'jane@example.com',
        first_name: 'Jane',
        last_name: 'Smith'
      },
      payment_transaction: {
        amount_paid_decimal: '49.99',
        currency: 'USD',
        payment_method: 'paypal'
      }
    }
  },

  tagAdded: {
    event: 'tag.added',
    data: {
      email: 'test@example.com',
      first_name: 'John',
      last_name: 'Doe',
      contact_id: 'contact-123',
      tag_name: 'VIP Customer'
    }
  },

  noEmail: {
    event: 'order.created',
    data: {
      id: 'test-txn-no-email',
      order_number: 'TEST-001',
      payment_transaction: {
        amount_paid_decimal: '1.00',
        currency: 'USD'
      }
    }
  }
}

// ============================================================================
// TEST FIXTURES - PAYPAL
// ============================================================================

export const paypalFixtures = {
  paymentCompleted: {
    event_type: 'PAYMENT.SALE.COMPLETED',
    resource: {
      id: 'PAYID12345',
      amount: {
        total: '99.99',
        currency: 'USD'
      },
      payer: {
        email_address: 'buyer@example.com',
        name: {
          given_name: 'Bob',
          surname: 'Builder'
        }
      },
      create_time: '2025-01-01T12:00:00Z'
    }
  },

  subscriptionCreated: {
    event_type: 'BILLING.SUBSCRIPTION.CREATED',
    resource: {
      id: 'I-SUBSCRIPTION123',
      status: 'ACTIVE',
      subscriber: {
        email_address: 'subscriber@example.com',
        name: {
          given_name: 'Alice',
          surname: 'Wonder'
        }
      },
      billing_info: {
        last_payment: {
          amount: {
            value: '29.99',
            currency_code: 'USD'
          }
        },
        next_billing_time: '2025-02-01T12:00:00Z'
      },
      create_time: '2025-01-01T12:00:00Z'
    }
  }
}

// ============================================================================
// TEST FIXTURES - TICKET TAILOR
// ============================================================================

export const ticketTailorFixtures = {
  orderCompleted: {
    type: 'order.completed',
    data: {
      id: 'tt-order-12345',
      reference: 'TT-REF-001',
      total: 15000, // In cents (150.00)
      currency: 'USD',
      status: 'completed',
      created_at: '2025-01-01T12:00:00Z',
      customer: {
        email: 'attendee@example.com',
        first_name: 'Sarah',
        last_name: 'Connor'
      },
      tickets: [
        {
          id: 'ticket-1',
          ticket_type_id: 'vip-ticket',
          price: 15000,
          status: 'valid'
        }
      ]
    }
  },

  orderRefunded: {
    type: 'order.refunded',
    data: {
      id: 'tt-order-12345',
      reference: 'TT-REF-001',
      total: 15000,
      currency: 'USD',
      status: 'refunded',
      refunded_at: '2025-01-02T12:00:00Z',
      customer: {
        email: 'attendee@example.com',
        first_name: 'Sarah',
        last_name: 'Connor'
      }
    }
  },

  orderCancelled: {
    type: 'order.cancelled',
    data: {
      id: 'tt-order-67890',
      reference: 'TT-REF-002',
      total: 5000,
      currency: 'USD',
      status: 'cancelled',
      cancelled_at: '2025-01-03T12:00:00Z',
      customer: {
        email: 'cancelled@example.com',
        first_name: 'John',
        last_name: 'Smith'
      }
    }
  },

  noEmail: {
    type: 'order.completed',
    data: {
      id: 'tt-test-no-email',
      reference: 'TT-TEST-001',
      total: 100,
      currency: 'USD',
      status: 'completed',
      created_at: '2025-01-01T12:00:00Z'
      // No customer information
    }
  }
}

// ============================================================================
// ASSERTION HELPERS
// ============================================================================

export function assertContactCreated(mockClient: MockSupabaseClient, email: string): void {
  const calls = mockClient.getCalls()
  const contactInserts = calls.filter(call =>
    call.method === 'upsert' &&
    call.table === 'contacts' &&
    call.data.email === email
  )

  assertEquals(
    contactInserts.length >= 1,
    true,
    `Expected contact with email ${email} to be created`
  )
}

export function assertTransactionCreated(mockClient: MockSupabaseClient, amount: number): void {
  const calls = mockClient.getCalls()
  const transactionInserts = calls.filter(call =>
    call.method === 'upsert' &&
    call.table === 'transactions' &&
    call.data.amount === amount
  )

  assertEquals(
    transactionInserts.length >= 1,
    true,
    `Expected transaction with amount ${amount} to be created`
  )
}

export function assertTagAdded(mockClient: MockSupabaseClient, tagName: string): void {
  const calls = mockClient.getCalls()
  const tagInserts = calls.filter(call =>
    (call.method === 'insert' || call.method === 'upsert') &&
    call.table === 'contact_tags'
  )

  assertEquals(
    tagInserts.length >= 1,
    true,
    `Expected tag relationship to be created`
  )
}
