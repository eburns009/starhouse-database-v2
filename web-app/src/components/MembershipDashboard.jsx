import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import './MembershipDashboard.css'

export default function MembershipDashboard() {
  const [stats, setStats] = useState(null)
  const [programPartners, setProgramPartners] = useState([])
  const [membershipLevels, setMembershipLevels] = useState([])
  const [recentTransactions, setRecentTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // 'overview', 'partners', 'individuals'

  useEffect(() => {
    fetchMembershipData()
  }, [])

  async function fetchMembershipData() {
    try {
      setLoading(true)
      setError(null)

      // Fetch overall stats
      const { data: statsData, error: statsError } = await supabase
        .from('contacts')
        .select('membership_group, membership_level', { count: 'exact' })

      if (statsError) throw statsError

      // Calculate stats
      const totalMembers = statsData?.length || 0
      const programPartnersCount = statsData?.filter(c => c.membership_group === 'Program Partner').length || 0
      const individualsCount = statsData?.filter(c => c.membership_group === 'Individual').length || 0
      const noMembershipCount = statsData?.filter(c => !c.membership_group).length || 0

      setStats({
        total: totalMembers,
        programPartners: programPartnersCount,
        individuals: individualsCount,
        noMembership: noMembershipCount
      })

      // Fetch membership level breakdown
      const levelBreakdown = {}
      statsData?.forEach(c => {
        if (c.membership_level) {
          levelBreakdown[c.membership_level] = (levelBreakdown[c.membership_level] || 0) + 1
        }
      })
      setMembershipLevels(
        Object.entries(levelBreakdown)
          .map(([level, count]) => ({ level, count }))
          .sort((a, b) => b.count - a.count)
      )

      // Fetch Program Partners with transaction counts
      const { data: partnersData, error: partnersError } = await supabase
        .from('contacts')
        .select(`
          id,
          first_name,
          last_name,
          email,
          membership_level,
          membership_tier,
          paypal_subscription_reference,
          transactions (count)
        `)
        .eq('membership_group', 'Program Partner')
        .order('membership_level')
        .order('last_name')

      if (partnersError) throw partnersError
      setProgramPartners(partnersData || [])

      // Fetch recent transactions
      const { data: txData, error: txError } = await supabase
        .from('transactions')
        .select(`
          id,
          amount,
          transaction_date,
          transaction_type,
          status,
          contacts (first_name, last_name, email, membership_group, membership_level)
        `)
        .eq('status', 'completed')
        .order('transaction_date', { ascending: false })
        .limit(10)

      if (txError) throw txError
      setRecentTransactions(txData || [])

    } catch (err) {
      console.error('Error fetching membership data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="membership-loading">Loading membership data...</div>
  }

  if (error) {
    return <div className="membership-error">Error: {error}</div>
  }

  return (
    <div className="membership-dashboard">
      <h1>Membership Dashboard</h1>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Contacts</div>
          <div className="stat-value">{stats?.total || 0}</div>
        </div>
        <div className="stat-card highlight-partner">
          <div className="stat-label">Program Partners</div>
          <div className="stat-value">{stats?.programPartners || 0}</div>
        </div>
        <div className="stat-card highlight-individual">
          <div className="stat-label">Individual Members</div>
          <div className="stat-value">{stats?.individuals || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">No Membership</div>
          <div className="stat-value">{stats?.noMembership || 0}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="membership-tabs">
        <button
          className={activeTab === 'overview' ? 'tab-btn active' : 'tab-btn'}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'partners' ? 'tab-btn active' : 'tab-btn'}
          onClick={() => setActiveTab('partners')}
        >
          Program Partners ({stats?.programPartners || 0})
        </button>
        <button
          className={activeTab === 'transactions' ? 'tab-btn active' : 'tab-btn'}
          onClick={() => setActiveTab('transactions')}
        >
          Recent Transactions
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="overview-section">
          <div className="section-card">
            <h2>Membership Levels Breakdown</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Membership Level</th>
                  <th>Member Count</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {membershipLevels.map(({ level, count }) => (
                  <tr key={level}>
                    <td>{level}</td>
                    <td>{count}</td>
                    <td>{((count / stats.total) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Program Partners Tab */}
      {activeTab === 'partners' && (
        <div className="partners-section">
          <div className="section-card">
            <h2>Program Partners</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Level</th>
                  <th>Tier</th>
                  <th>Transactions</th>
                  <th>Has Subscription</th>
                </tr>
              </thead>
              <tbody>
                {programPartners.map(partner => (
                  <tr key={partner.id}>
                    <td>{partner.first_name} {partner.last_name}</td>
                    <td className="email-cell">{partner.email}</td>
                    <td>
                      <span className={`level-badge level-${partner.membership_level?.toLowerCase().replace(' ', '-')}`}>
                        {partner.membership_level}
                      </span>
                    </td>
                    <td>{partner.membership_tier}</td>
                    <td className="count-cell">{partner.transactions?.[0]?.count || 0}</td>
                    <td>
                      {partner.paypal_subscription_reference ? (
                        <span className="badge-yes">Yes</span>
                      ) : (
                        <span className="badge-no">No</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {programPartners.length === 0 && (
              <div className="empty-state">No Program Partners found</div>
            )}
          </div>
        </div>
      )}

      {/* Transactions Tab */}
      {activeTab === 'transactions' && (
        <div className="transactions-section">
          <div className="section-card">
            <h2>Recent Transactions (Last 10)</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Contact</th>
                  <th>Level</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentTransactions.map(tx => (
                  <tr key={tx.id}>
                    <td>{new Date(tx.transaction_date).toLocaleDateString()}</td>
                    <td>
                      {tx.contacts?.first_name} {tx.contacts?.last_name}
                      <br />
                      <span className="email-small">{tx.contacts?.email}</span>
                    </td>
                    <td>
                      {tx.contacts?.membership_group && (
                        <span className={`group-badge ${tx.contacts.membership_group?.toLowerCase().replace(' ', '-')}`}>
                          {tx.contacts.membership_level || tx.contacts.membership_group}
                        </span>
                      )}
                    </td>
                    <td>{tx.transaction_type}</td>
                    <td className="amount-cell">${tx.amount}</td>
                    <td>
                      <span className={`status-badge status-${tx.status}`}>
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
