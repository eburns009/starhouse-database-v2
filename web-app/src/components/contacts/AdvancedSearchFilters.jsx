import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import Button from '../ui/Button'
import Input from '../ui/Input'
import Select from '../ui/Select'
import Modal from '../ui/Modal'

export default function AdvancedSearchFilters({ isOpen, onClose, onApply, initialFilters = {} }) {
  const [filters, setFilters] = useState({
    dateFrom: initialFilters.dateFrom || '',
    dateTo: initialFilters.dateTo || '',
    amountMin: initialFilters.amountMin || '',
    amountMax: initialFilters.amountMax || '',
    tags: initialFilters.tags || [],
    sourceSystem: initialFilters.sourceSystem || '',
    hasActiveSubscription: initialFilters.hasActiveSubscription || '',
    ...initialFilters
  })

  const [availableTags, setAvailableTags] = useState([])
  const [savedPresets, setSavedPresets] = useState([])
  const [presetName, setPresetName] = useState('')
  const [showSavePreset, setShowSavePreset] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchTags()
      loadPresets()
    }
  }, [isOpen])

  async function fetchTags() {
    try {
      const { data, error } = await supabase
        .from('tags')
        .select('id, name')
        .order('name')

      if (error) throw error
      setAvailableTags(data || [])
    } catch (err) {
      console.error('Error fetching tags:', err)
    }
  }

  function loadPresets() {
    const saved = localStorage.getItem('contactSearchPresets')
    if (saved) {
      try {
        setSavedPresets(JSON.parse(saved))
      } catch (err) {
        console.error('Error loading presets:', err)
      }
    }
  }

  function savePreset() {
    if (!presetName.trim()) return

    const newPreset = {
      id: Date.now(),
      name: presetName,
      filters: { ...filters }
    }

    const updated = [...savedPresets, newPreset]
    setSavedPresets(updated)
    localStorage.setItem('contactSearchPresets', JSON.stringify(updated))
    setPresetName('')
    setShowSavePreset(false)
  }

  function loadPreset(preset) {
    setFilters(preset.filters)
  }

  function deletePreset(presetId) {
    const updated = savedPresets.filter(p => p.id !== presetId)
    setSavedPresets(updated)
    localStorage.setItem('contactSearchPresets', JSON.stringify(updated))
  }

  function handleTagToggle(tagId) {
    setFilters(prev => {
      const tags = prev.tags || []
      if (tags.includes(tagId)) {
        return { ...prev, tags: tags.filter(id => id !== tagId) }
      } else {
        return { ...prev, tags: [...tags, tagId] }
      }
    })
  }

  function handleReset() {
    setFilters({
      dateFrom: '',
      dateTo: '',
      amountMin: '',
      amountMax: '',
      tags: [],
      sourceSystem: '',
      hasActiveSubscription: ''
    })
  }

  function handleApply() {
    // Clean up empty values
    const cleanFilters = Object.fromEntries(
      Object.entries(filters).filter(([_, value]) => {
        if (Array.isArray(value)) return value.length > 0
        return value !== '' && value !== null && value !== undefined
      })
    )

    onApply(cleanFilters)
    onClose()
  }

  const activeFilterCount = Object.values(filters).filter(value => {
    if (Array.isArray(value)) return value.length > 0
    return value !== '' && value !== null && value !== undefined
  }).length

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Advanced Search Filters">
      <div style={{ minWidth: '500px' }}>
        {/* Date Range */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>
            Transaction Date Range
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Input
              type="date"
              label="From"
              value={filters.dateFrom}
              onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
            />
            <Input
              type="date"
              label="To"
              value={filters.dateTo}
              onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
            />
          </div>
        </div>

        {/* Amount Range */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>
            Revenue Range
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Input
              type="number"
              label="Min Amount ($)"
              placeholder="0.00"
              value={filters.amountMin}
              onChange={(e) => setFilters(prev => ({ ...prev, amountMin: e.target.value }))}
              min="0"
              step="0.01"
            />
            <Input
              type="number"
              label="Max Amount ($)"
              placeholder="10000.00"
              value={filters.amountMax}
              onChange={(e) => setFilters(prev => ({ ...prev, amountMax: e.target.value }))}
              min="0"
              step="0.01"
            />
          </div>
        </div>

        {/* Tags */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>
            Tags ({filters.tags?.length || 0} selected)
          </h3>
          <div style={{
            maxHeight: '150px',
            overflowY: 'auto',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
            padding: '8px'
          }}>
            {availableTags.length === 0 ? (
              <p style={{ color: '#6b7280', fontSize: '14px', textAlign: 'center', padding: '8px' }}>
                No tags available
              </p>
            ) : (
              availableTags.map(tag => (
                <label
                  key={tag.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '6px 8px',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    transition: 'background-color 0.15s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <input
                    type="checkbox"
                    checked={filters.tags?.includes(tag.id) || false}
                    onChange={() => handleTagToggle(tag.id)}
                    style={{ marginRight: '8px' }}
                  />
                  <span style={{ fontSize: '14px' }}>{tag.name}</span>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Source System */}
        <div style={{ marginBottom: '20px' }}>
          <Select
            label="Source System"
            value={filters.sourceSystem}
            onChange={(e) => setFilters(prev => ({ ...prev, sourceSystem: e.target.value }))}
            options={[
              { value: '', label: 'All Systems' },
              { value: 'kajabi', label: 'Kajabi' },
              { value: 'paypal', label: 'PayPal' },
              { value: 'zoho', label: 'Zoho' },
              { value: 'manual', label: 'Manual Entry' }
            ]}
          />
        </div>

        {/* Subscription Status */}
        <div style={{ marginBottom: '20px' }}>
          <Select
            label="Subscription Status"
            value={filters.hasActiveSubscription}
            onChange={(e) => setFilters(prev => ({ ...prev, hasActiveSubscription: e.target.value }))}
            options={[
              { value: '', label: 'All Contacts' },
              { value: 'true', label: 'Active Subscribers' },
              { value: 'false', label: 'Inactive/Non-subscribers' }
            ]}
          />
        </div>

        {/* Saved Presets */}
        {savedPresets.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>
              Saved Presets
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {savedPresets.map(preset => (
                <div
                  key={preset.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px'
                  }}
                >
                  <button
                    onClick={() => loadPreset(preset)}
                    style={{
                      flex: 1,
                      textAlign: 'left',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    {preset.name}
                  </button>
                  <button
                    onClick={() => deletePreset(preset.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#ef4444',
                      cursor: 'pointer',
                      padding: '4px 8px'
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Save Preset */}
        {showSavePreset ? (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <Input
                placeholder="Preset name..."
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && savePreset()}
                autoFocus
              />
              <Button variant="primary" size="sm" onClick={savePreset}>
                Save
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowSavePreset(false)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSavePreset(true)}
            style={{ marginBottom: '20px' }}
          >
            💾 Save Current Filters as Preset
          </Button>
        )}

        {/* Action Buttons */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderTop: '1px solid #e5e7eb',
          paddingTop: '16px'
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>
            {activeFilterCount > 0 ? `${activeFilterCount} filter${activeFilterCount > 1 ? 's' : ''} active` : 'No filters active'}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button variant="ghost" onClick={handleReset}>
              Reset
            </Button>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleApply}>
              Apply Filters
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}
