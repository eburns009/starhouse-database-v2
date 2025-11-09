import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import './ActivityTimeline.css'

const PAGE_SIZE = 50

export default function ActivityTimeline({ contactId }) {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [page, setPage] = useState(0)
  const [typeFilter, setTypeFilter] = useState('all')

  useEffect(() => {
    fetchActivities(true)
  }, [contactId, typeFilter])

  async function fetchActivities(reset = false) {
    try {
      if (reset) {
        setLoading(true)
        setPage(0)
        setActivities([])
      }

      const currentPage = reset ? 0 : page
      const offset = currentPage * PAGE_SIZE

      const { data, error: activityError } = await supabase
        .rpc('get_contact_activity', {
          p_contact_id: contactId,
          p_limit: PAGE_SIZE,
          p_offset: offset
        })

      if (activityError) throw activityError

      let filteredData = data || []

      // Apply type filter if not 'all'
      if (typeFilter !== 'all') {
        filteredData = filteredData.filter(a => a.activity_type === typeFilter)
      }

      setActivities(reset ? filteredData : [...activities, ...filteredData])
      setHasMore(filteredData.length === PAGE_SIZE)
      if (!reset) {
        setPage(currentPage + 1)
      }
    } catch (err) {
      console.error('Error fetching activities:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getActivityIcon = (type) => {
    const icons = {
      webhook: '🔗',
      transaction: '💰',
      tag: '🏷️',
      note: '📝',
      role: '👤',
      subscription: '🔄'
    }
    return icons[type] || '•'
  }

  const getActivityColor = (type) => {
    const colors = {
      webhook: 'blue',
      transaction: 'green',
      tag: 'purple',
      note: 'orange',
      role: 'teal',
      subscription: 'indigo'
    }
    return colors[type] || 'gray'
  }

  const formatCurrency = (amount) => {
    if (!amount) return null
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatDate = (date) => {
    if (!date) return 'Unknown date'
    const d = new Date(date)
    const now = new Date()
    const diffMs = now - d
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    // Time part
    const timeStr = d.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })

    // Date part
    if (diffDays === 0) return `Today at ${timeStr}`
    if (diffDays === 1) return `Yesterday at ${timeStr}`
    if (diffDays < 7) return `${diffDays}d ago at ${timeStr}`

    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
      hour: 'numeric',
      minute: '2-digit'
    })
  }

  if (loading && activities.length === 0) {
    return (
      <div className="timeline-loading">
        <div className="spinner"></div>
        <p>Loading activity...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="timeline-error">
        <p>Error loading activity: {error}</p>
      </div>
    )
  }

  return (
    <div className="activity-timeline">
      {/* Filter */}
      <div className="timeline-filter">
        <label>Filter by type:</label>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Activity</option>
          <option value="transaction">Transactions</option>
          <option value="note">Notes</option>
          <option value="role">Role Changes</option>
          <option value="tag">Tags</option>
          <option value="webhook">Webhooks</option>
          <option value="subscription">Subscriptions</option>
        </select>
      </div>

      {/* Timeline */}
      {activities.length === 0 ? (
        <div className="timeline-empty">
          <p>No activity to display</p>
        </div>
      ) : (
        <>
          <div className="timeline-list">
            {activities.map((activity, idx) => (
              <div key={idx} className="timeline-item">
                <div className={`timeline-icon ${getActivityColor(activity.activity_type)}`}>
                  {getActivityIcon(activity.activity_type)}
                </div>
                <div className="timeline-content">
                  <div className="timeline-header">
                    <span className={`activity-type ${getActivityColor(activity.activity_type)}`}>
                      {activity.activity_name}
                    </span>
                    <span className="timeline-date">
                      {formatDate(activity.activity_date)}
                    </span>
                  </div>
                  <div className="timeline-details">
                    {activity.details}
                    {activity.amount && (
                      <span className="activity-amount">
                        {formatCurrency(activity.amount)}
                      </span>
                    )}
                  </div>
                  {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                    <div className="timeline-metadata">
                      {activity.metadata.source && (
                        <span className="metadata-badge">
                          Source: {activity.metadata.source}
                        </span>
                      )}
                      {activity.metadata.author_name && (
                        <span className="metadata-badge">
                          By: {activity.metadata.author_name}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Load More */}
          {hasMore && (
            <div className="timeline-load-more">
              <button
                onClick={() => fetchActivities(false)}
                className="btn-load-more"
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
