import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { ComplianceSummary } from './contacts/ProgramPartnerComplianceFilter'

/**
 * Program Partner Dashboard Component
 * Displays compliance statistics and lists of non-compliant partners
 */
export default function ProgramPartnerDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [nonCompliantPartners, setNonCompliantPartners] = useState([])
  const [revenueStats, setRevenueStats] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  async function fetchDashboardData() {
    try {
      setLoading(true)
      setError(null)

      // Fetch compliance statistics
      const { data: complianceData, error: complianceError } = await supabase
        .from('program_partner_compliance')
        .select('compliance_status, monthly_payment')

      if (complianceError) throw complianceError

      // Calculate stats
      const stats = {
        total: complianceData.length,
        compliant: complianceData.filter(d => d.compliance_status === 'compliant').length,
        needs_upgrade: complianceData.filter(d => d.compliance_status === 'needs_upgrade').length,
        no_membership: complianceData.filter(d => d.compliance_status === 'no_membership').length,
      }

      setStats(stats)

      // Fetch non-compliant partners
      const { data: nonCompliant, error: nonCompliantError } = await supabase
        .from('program_partner_compliance')
        .select('*')
        .neq('compliance_status', 'compliant')
        .order('compliance_status')
        .order('last_name')

      if (nonCompliantError) throw nonCompliantError
      setNonCompliantPartners(nonCompliant || [])

      // Calculate revenue statistics
      const currentRevenue = complianceData
        .filter(d => d.compliance_status === 'compliant' && d.monthly_payment)
        .reduce((sum, d) => sum + parseFloat(d.monthly_payment || 0), 0)

      const potentialRevenue = stats.total * 33 // Minimum tier is $33/month

      setRevenueStats({
        current: currentRevenue,
        potential: potentialRevenue,
        opportunity: potentialRevenue - currentRevenue,
      })

    } catch (err) {
      console.error('Error fetching dashboard data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <strong className="text-red-800">Error:</strong> {error}
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Program Partner Dashboard</h1>
        <button
          onClick={fetchDashboardData}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Compliance Summary Card */}
      <ComplianceSummary stats={stats} />

      {/* Revenue Statistics */}
      {revenueStats && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Revenue Impact</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                ${revenueStats.current.toFixed(0)}
              </div>
              <div className="text-xs text-gray-600 mt-1">Current Monthly Revenue</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                ${revenueStats.potential.toFixed(0)}
              </div>
              <div className="text-xs text-gray-600 mt-1">Potential Monthly Revenue</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                +${revenueStats.opportunity.toFixed(0)}
              </div>
              <div className="text-xs text-gray-600 mt-1">Monthly Opportunity</div>
            </div>
          </div>
          <div className="text-sm text-gray-500 mt-4 pt-4 border-t">
            Annual opportunity: ${(revenueStats.opportunity * 12).toFixed(0)}/year
          </div>
        </div>
      )}

      {/* Non-Compliant Partners List */}
      {nonCompliantPartners.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Non-Compliant Partners ({nonCompliantPartners.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action Needed
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {nonCompliantPartners.map((partner) => (
                  <tr key={partner.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {partner.first_name} {partner.last_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {partner.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {partner.current_membership}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          partner.compliance_status === 'needs_upgrade'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {partner.compliance_message}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => {
              // Export non-compliant partners
              const csv = [
                ['First Name', 'Last Name', 'Email', 'Current Membership', 'Status'],
                ...nonCompliantPartners.map(p => [
                  p.first_name,
                  p.last_name,
                  p.email,
                  p.current_membership,
                  p.compliance_message
                ])
              ].map(row => row.join(',')).join('\n')

              const blob = new Blob([csv], { type: 'text/csv' })
              const url = window.URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `non-compliant-partners-${new Date().toISOString().split('T')[0]}.csv`
              a.click()
            }}
            className="px-4 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 flex items-center justify-center"
          >
            📥 Export Non-Compliant List
          </button>
          <button
            onClick={() => {
              // Copy emails to clipboard
              const emails = nonCompliantPartners.map(p => p.email).join(', ')
              navigator.clipboard.writeText(emails)
              alert('Email addresses copied to clipboard!')
            }}
            className="px-4 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 flex items-center justify-center"
          >
            📋 Copy All Email Addresses
          </button>
        </div>
      </div>
    </div>
  )
}
