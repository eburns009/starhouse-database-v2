import { useState } from 'react'

/**
 * Program Partner Compliance Filter Component
 * Displays filter options for Program Partner compliance status
 */
export default function ProgramPartnerComplianceFilter({ value, onChange }) {
  const complianceOptions = [
    { value: 'all', label: 'All Contacts', count: null },
    { value: 'expected', label: 'Expected Partners', count: null },
    { value: 'compliant', label: '✅ Compliant', count: null },
    { value: 'needs_upgrade', label: '⚠️ Needs Upgrade', count: null },
    { value: 'no_membership', label: '❌ No Membership', count: null },
  ]

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Program Partner Status
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      >
        {complianceOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

/**
 * Program Partner Compliance Badge Component
 * Displays a colored badge indicating compliance status
 */
export function ComplianceBadge({ status, message }) {
  if (!status) return null

  const badgeStyles = {
    compliant: 'bg-green-100 text-green-800',
    needs_upgrade: 'bg-yellow-100 text-yellow-800',
    no_membership: 'bg-red-100 text-red-800',
    trial: 'bg-blue-100 text-blue-800',
  }

  const badgeIcons = {
    compliant: '✅',
    needs_upgrade: '⚠️',
    no_membership: '❌',
    trial: '⏳',
  }

  const style = badgeStyles[status] || 'bg-gray-100 text-gray-800'
  const icon = badgeIcons[status] || ''

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style}`}
      title={message}
    >
      <span className="mr-1">{icon}</span>
      {status === 'compliant' && 'Compliant'}
      {status === 'needs_upgrade' && 'Needs Upgrade'}
      {status === 'no_membership' && 'No Membership'}
      {status === 'trial' && 'Trial'}
    </span>
  )
}

/**
 * Program Partner Compliance Summary Component
 * Displays summary statistics for Program Partner compliance
 */
export function ComplianceSummary({ stats }) {
  if (!stats) return null

  const total = stats.total || 0
  const compliant = stats.compliant || 0
  const needsUpgrade = stats.needs_upgrade || 0
  const noMembership = stats.no_membership || 0

  const complianceRate = total > 0 ? ((compliant / total) * 100).toFixed(1) : 0

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Program Partner Compliance
      </h3>
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Compliance Rate</span>
          <span className="text-2xl font-bold text-gray-900">{complianceRate}%</span>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{compliant}</div>
            <div className="text-xs text-gray-600 mt-1">✅ Compliant</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{needsUpgrade}</div>
            <div className="text-xs text-gray-600 mt-1">⚠️ Needs Upgrade</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{noMembership}</div>
            <div className="text-xs text-gray-600 mt-1">❌ No Membership</div>
          </div>
        </div>
        <div className="text-sm text-gray-500 mt-4 pt-4 border-t">
          {total} expected Program Partners
        </div>
      </div>
    </div>
  )
}
