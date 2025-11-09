import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { NOTE_TYPES } from '../../types/contacts'
import './NotesPanel.css'

export default function NotesPanel({ contactId, onUpdate }) {
  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isAdding, setIsAdding] = useState(false)
  const [saving, setSaving] = useState(false)
  const [typeFilter, setTypeFilter] = useState('all')
  const [newNote, setNewNote] = useState({
    note_type: 'general',
    subject: '',
    content: '',
    author_name: '',
    is_pinned: false
  })

  useEffect(() => {
    fetchNotes()
  }, [contactId, typeFilter])

  async function fetchNotes() {
    try {
      setLoading(true)
      setError(null)

      let query = supabase
        .from('contact_notes')
        .select('*')
        .eq('contact_id', contactId)
        .order('is_pinned', { ascending: false })
        .order('created_at', { ascending: false })

      // Apply type filter
      if (typeFilter !== 'all') {
        query = query.eq('note_type', typeFilter)
      }

      const { data, error: fetchError } = await query

      if (fetchError) throw fetchError

      setNotes(data || [])
    } catch (err) {
      console.error('Error fetching notes:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddNote(e) {
    e.preventDefault()
    try {
      setSaving(true)
      setError(null)

      const { data, error: insertError } = await supabase
        .from('contact_notes')
        .insert({
          contact_id: contactId,
          note_type: newNote.note_type,
          subject: newNote.subject || null,
          content: newNote.content,
          author_name: newNote.author_name || null,
          is_pinned: newNote.is_pinned
        })
        .select()

      if (insertError) throw insertError

      // Reset form
      setNewNote({
        note_type: 'general',
        subject: '',
        content: '',
        author_name: '',
        is_pinned: false
      })
      setIsAdding(false)

      // Refresh notes
      await fetchNotes()
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Error adding note:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleTogglePin(noteId, currentPinned) {
    try {
      const { error: updateError } = await supabase
        .from('contact_notes')
        .update({ is_pinned: !currentPinned })
        .eq('id', noteId)
        .eq('contact_id', contactId)

      if (updateError) throw updateError

      // Refresh notes
      await fetchNotes()
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Error toggling pin:', err)
      setError(err.message)
    }
  }

  async function handleDeleteNote(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) {
      return
    }

    try {
      const { error: deleteError } = await supabase
        .from('contact_notes')
        .delete()
        .eq('id', noteId)
        .eq('contact_id', contactId)

      if (deleteError) throw deleteError

      // Refresh notes
      await fetchNotes()
      if (onUpdate) onUpdate()
    } catch (err) {
      console.error('Error deleting note:', err)
      setError(err.message)
    }
  }

  const getNoteTypeColor = (type) => {
    const colors = {
      general: 'blue',
      call: 'green',
      meeting: 'purple',
      email: 'orange',
      internal: 'teal',
      follow_up: 'red'
    }
    return colors[type] || 'gray'
  }

  const getNoteTypeIcon = (type) => {
    const icons = {
      general: '📝',
      call: '📞',
      meeting: '🤝',
      email: '✉️',
      internal: '🔒',
      follow_up: '⏰'
    }
    return icons[type] || '📄'
  }

  const formatDate = (date) => {
    if (!date) return 'Unknown date'
    const d = new Date(date)
    const now = new Date()
    const diffMs = now - d
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return `Today at ${d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
    if (diffDays === 1) return `Yesterday at ${d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
    if (diffDays < 7) return `${diffDays}d ago`

    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    })
  }

  return (
    <div className="notes-panel">
      <div className="notes-header">
        <div className="header-controls">
          <h3>Notes</h3>
          <div className="notes-filter">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Types</option>
              <option value="general">General</option>
              <option value="call">Call</option>
              <option value="meeting">Meeting</option>
              <option value="email">Email</option>
              <option value="internal">Internal</option>
              <option value="follow_up">Follow Up</option>
            </select>
          </div>
        </div>
        {!isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="btn-add"
          >
            + Add Note
          </button>
        )}
      </div>

      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Add Note Form */}
      {isAdding && (
        <form onSubmit={handleAddNote} className="add-note-form">
          <div className="form-row">
            <div className="form-group">
              <label>Type *</label>
              <select
                value={newNote.note_type}
                onChange={(e) => setNewNote({ ...newNote, note_type: e.target.value })}
                className="form-input"
                required
              >
                <option value="general">General</option>
                <option value="call">Call</option>
                <option value="meeting">Meeting</option>
                <option value="email">Email</option>
                <option value="internal">Internal</option>
                <option value="follow_up">Follow Up</option>
              </select>
            </div>

            <div className="form-group">
              <label>Author Name</label>
              <input
                type="text"
                value={newNote.author_name}
                onChange={(e) => setNewNote({ ...newNote, author_name: e.target.value })}
                placeholder="Your name"
                className="form-input"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Subject</label>
            <input
              type="text"
              value={newNote.subject}
              onChange={(e) => setNewNote({ ...newNote, subject: e.target.value })}
              placeholder="Brief subject line"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Content *</label>
            <textarea
              value={newNote.content}
              onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
              placeholder="Write your note here..."
              className="form-textarea"
              rows="6"
              required
            />
          </div>

          <div className="form-checkboxes">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={newNote.is_pinned}
                onChange={(e) => setNewNote({ ...newNote, is_pinned: e.target.checked })}
              />
              <span>Pin this note to the top</span>
            </label>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              disabled={saving}
              className="btn-save"
            >
              {saving ? 'Saving...' : 'Add Note'}
            </button>
            <button
              type="button"
              onClick={() => {
                setIsAdding(false)
                setError(null)
              }}
              className="btn-cancel"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Notes List */}
      {loading && notes.length === 0 ? (
        <div className="notes-loading">
          <div className="spinner"></div>
          <p>Loading notes...</p>
        </div>
      ) : notes.length === 0 ? (
        <div className="notes-empty">
          <p>No notes found</p>
        </div>
      ) : (
        <div className="notes-list">
          {notes.map((note) => (
            <div
              key={note.id}
              className={`note-card ${note.is_pinned ? 'pinned' : ''}`}
            >
              <div className="note-header">
                <div className="note-header-left">
                  <span className={`note-type-icon ${getNoteTypeColor(note.note_type)}`}>
                    {getNoteTypeIcon(note.note_type)}
                  </span>
                  <span className={`note-type-badge ${getNoteTypeColor(note.note_type)}`}>
                    {note.note_type}
                  </span>
                  {note.is_pinned && (
                    <span className="pinned-badge" title="Pinned">
                      📌
                    </span>
                  )}
                </div>
                <div className="note-actions">
                  <button
                    onClick={() => handleTogglePin(note.id, note.is_pinned)}
                    className="btn-action"
                    title={note.is_pinned ? 'Unpin note' : 'Pin note'}
                  >
                    {note.is_pinned ? 'Unpin' : 'Pin'}
                  </button>
                  <button
                    onClick={() => handleDeleteNote(note.id)}
                    className="btn-action btn-danger"
                    title="Delete note"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {note.subject && (
                <h4 className="note-subject">{note.subject}</h4>
              )}

              <div className="note-content">
                {note.content}
              </div>

              <div className="note-footer">
                <span className="note-date">{formatDate(note.created_at)}</span>
                {note.author_name && (
                  <span className="note-author">by {note.author_name}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
