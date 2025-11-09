import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import './MembersList.css'

export default function MembersList() {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState('active') // 'active', 'canceled', 'expired', 'all'
  const [memberTypeFilter, setMemberTypeFilter] = useState('all') // 'all', 'individual', 'program-partner'
  const [billingPeriodFilter, setBillingPeriodFilter] = useState('all') // 'all', 'monthly', 'annual'
  const [legacyFilter, setLegacyFilter] = useState('all') // 'all', 'legacy', 'current'
  const [searchQuery, setSearchQuery] = useState('')

  // Stats
  const [stats, setStats] = useState({
    active: 0,
    canceled: 0,
    expired: 0,
    individual: 0,
    programPartners: 0,
    monthly: 0,
    annual: 0,
    legacy: 0
  })

  useEffect(() => {
    fetchMembers()
  }, [statusFilter, memberTypeFilter, billingPeriodFilter, legacyFilter, searchQuery])

  async function fetchMembers() {
    try {
      setLoading(true)
      setError(null)

      // Build query
      let query = supabase
        .from('subscriptions')
        .select(`
          id,
          status,
          amount,
          currency,
          billing_cycle,
          start_date,
          cancellation_date,
          next_billing_date,
          is_annual,
          contacts (
            id,
            first_name,
            last_name,
            email
          ),
          membership_products (
            id,
            product_name,
            membership_group,
            membership_level,
            membership_tier,
            is_legacy
          )
        `)
        .order('start_date', { ascending: false })

      // Apply status filter
      if (statusFilter !== 'all') {
        query = query.eq('status', statusFilter)
      }

      // Execute query
      const { data, error: fetchError } = await query

      if (fetchError) throw fetchError

      // Filter by member type (client-side since it's in the nested object)
      let filteredData = data || []
      if (memberTypeFilter === 'individual') {
        filteredData = filteredData.filter(m => m.membership_products?.membership_group === 'Individual')
      } else if (memberTypeFilter === 'program-partner') {
        filteredData = filteredData.filter(m => m.membership_products?.membership_group === 'Program Partner')
      }

      // Filter by billing period
      if (billingPeriodFilter === 'annual') {
        filteredData = filteredData.filter(m => m.is_annual === true)
      } else if (billingPeriodFilter === 'monthly') {
        filteredData = filteredData.filter(m => m.is_annual === false)
      }

      // Filter by legacy status
      if (legacyFilter === 'legacy') {
        filteredData = filteredData.filter(m => m.membership_products?.is_legacy === true)
      } else if (legacyFilter === 'current') {
        filteredData = filteredData.filter(m => m.membership_products?.is_legacy === false)
      }

      // Filter by search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        filteredData = filteredData.filter(m => {
          const name = `${m.contacts?.first_name} ${m.contacts?.last_name}`.toLowerCase()
          const email = m.contacts?.email?.toLowerCase() || ''
          const level = m.membership_products?.membership_level?.toLowerCase() || ''
          return name.includes(query) || email.includes(query) || level.includes(query)
        })
      }

      setMembers(filteredData)

      // Calculate stats (fetch all for stats)
      const { data: allData } = await supabase
        .from('subscriptions')
        .select('status, is_annual, membership_products(membership_group, is_legacy)')

      if (allData) {
        setStats({
          active: allData.filter(s => s.status === 'active').length,
          canceled: allData.filter(s => s.status === 'canceled').length,
          expired: allData.filter(s => s.status === 'expired').length,
          individual: allData.filter(s => s.membership_products?.membership_group === 'Individual').length,
          programPartners: allData.filter(s => s.membership_products?.membership_group === 'Program Partner').length,
          monthly: allData.filter(s => s.is_annual === false).length,
          annual: allData.filter(s => s.is_annual === true).length,
          legacy: allData.filter(s => s.membership_products?.is_legacy === true).length
        })
      }

    } catch (err) {
      console.error('Error fetching members:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function getStatusBadgeClass(status) {
    const classes = {
      active: 'status-active',
      canceled: 'status-canceled',
      expired: 'status-expired',
      paused: 'status-paused',
      trial: 'status-trial'
    }
    return classes[status] || 'status-unknown'
  }

  function getMemberTypeBadgeClass(group) {
    return group === 'Program Partner' ? 'type-partner' : 'type-individual'
  }

  function formatDate(dateString) {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString()
  }

  function formatAmount(amount, currency = 'USD') {
    if (!amount) return '-'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount)
  }

  if (loading) {
    return <div className="members-loading">Loading members...</div>
  }

  if (error) {
    return <div className="members-error">Error: {error}</div>
  }

  return (
    <div className="members-list-container">
      <div className="members-header">
        <h1>Members</h1>
        <div className="members-stats">
          <div className="stat-chip stat-active">
            <span className="stat-label">Active:</span>
            <span className="stat-value">{stats.active}</span>
          </div>
          <div className="stat-chip stat-info">
            <span className="stat-label">Monthly:</span>
            <span className="stat-value">{stats.monthly}</span>
          </div>
          <div className="stat-chip stat-info">
            <span className="stat-label">Annual:</span>
            <span className="stat-value">{stats.annual}</span>
          </div>
          <div className="stat-chip stat-legacy">
            <span className="stat-label">Legacy:</span>
            <span className="stat-value">{stats.legacy}</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="members-filters">
        <div className="filter-group">
          <label>Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="canceled">Canceled Members</option>
            <option value="expired">Expired</option>
            <option value="paused">Paused</option>
            <option value="trial">Trial</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Member Type:</label>
          <select
            value={memberTypeFilter}
            onChange={(e) => setMemberTypeFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Members</option>
            <option value="individual">Individual Members</option>
            <option value="program-partner">Program Partners</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Billing Period:</label>
          <select
            value={billingPeriodFilter}
            onChange={(e) => setBillingPeriodFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All</option>
            <option value="monthly">Monthly</option>
            <option value="annual">Annual</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Membership Type:</label>
          <select
            value={legacyFilter}
            onChange={(e) => setLegacyFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All</option>
            <option value="current">Current (Kajabi)</option>
            <option value="legacy">Legacy (PayPal)</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Search:</label>
          <input
            type="text"
            placeholder="Search by name, email, or level..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="filter-input"
          />
        </div>

        <button onClick={fetchMembers} className="btn-refresh">
          Refresh
        </button>
      </div>

      {/* Results count */}
      <div className="members-count">
        Showing {members.length} member{members.length !== 1 ? 's' : ''}
      </div>

      {/* Members Table */}
      <div className="members-table-container">
        <table className="members-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Type</th>
              <th>Level</th>
              <th>Status</th>
              <th>Amount</th>
              <th>Billing</th>
              <th>Start Date</th>
              <th>Next Billing</th>
              <th>Cancellation</th>
            </tr>
          </thead>
          <tbody>
            {members.length === 0 ? (
              <tr>
                <td colSpan="9" className="empty-state">
                  No members found with current filters
                </td>
              </tr>
            ) : (
              members.map(member => (
                <tr key={member.id}>
                  <td className="member-info">
                    <div className="member-name">
                      {member.contacts?.first_name} {member.contacts?.last_name}
                    </div>
                    <div className="member-email">{member.contacts?.email}</div>
                  </td>
                  <td>
                    <span className={`member-type-badge ${getMemberTypeBadgeClass(member.membership_products?.membership_group)}`}>
                      {member.membership_products?.membership_group === 'Program Partner'
                        ? 'Program Partner'
                        : 'Individual'}
                    </span>
                  </td>
                  <td>
                    <span className="member-level">
                      {member.membership_products?.membership_level || '-'}
                      {member.membership_products?.is_legacy && (
                        <span className="legacy-badge-inline"> (Legacy)</span>
                      )}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(member.status)}`}>
                      {member.status}
                    </span>
                  </td>
                  <td className="amount-cell">
                    {formatAmount(member.amount, member.currency)}
                    {member.is_annual && <span className="annual-badge">Annual</span>}
                  </td>
                  <td>{member.billing_cycle || '-'}</td>
                  <td>{formatDate(member.start_date)}</td>
                  <td>{formatDate(member.next_billing_date)}</td>
                  <td>{formatDate(member.cancellation_date)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
