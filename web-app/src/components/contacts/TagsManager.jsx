import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import Button from '../ui/Button'
import Input from '../ui/Input'

export default function TagsManager({ contactId, onUpdate }) {
  const [tags, setTags] = useState([])
  const [availableTags, setAvailableTags] = useState([])
  const [newTagName, setNewTagName] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchTags()
    fetchAvailableTags()
  }, [contactId])

  async function fetchTags() {
    const { data } = await supabase
      .from('contact_tags')
      .select('*, tags(*)')
      .eq('contact_id', contactId)
    setTags(data || [])
  }

  async function fetchAvailableTags() {
    const { data } = await supabase
      .from('tags')
      .select('*')
      .order('name')
    setAvailableTags(data || [])
  }

  async function addTag(tagId) {
    setLoading(true)
    try {
      const { error } = await supabase
        .from('contact_tags')
        .insert([{ contact_id: contactId, tag_id: tagId }])

      if (error) throw error
      await fetchTags()
      onUpdate?.()
    } catch (error) {
      console.error('Error adding tag:', error)
    } finally {
      setLoading(false)
    }
  }

  async function removeTag(tagId) {
    setLoading(true)
    try {
      const { error } = await supabase
        .from('contact_tags')
        .delete()
        .eq('contact_id', contactId)
        .eq('tag_id', tagId)

      if (error) throw error
      await fetchTags()
      onUpdate?.()
    } catch (error) {
      console.error('Error removing tag:', error)
    } finally {
      setLoading(false)
    }
  }

  async function createAndAddTag() {
    if (!newTagName.trim()) return

    setLoading(true)
    try {
      const { data: newTag, error } = await supabase
        .from('tags')
        .insert([{ name: newTagName.trim() }])
        .select()
        .single()

      if (error) throw error

      await addTag(newTag.id)
      setNewTagName('')
      await fetchAvailableTags()
    } catch (error) {
      console.error('Error creating tag:', error)
    } finally {
      setLoading(false)
    }
  }

  const currentTagIds = tags.map(t => t.tag_id)
  const unassignedTags = availableTags.filter(t => !currentTagIds.includes(t.id))

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Current Tags</h4>
        <div className="flex flex-wrap gap-2">
          {tags.length === 0 ? (
            <p className="text-sm text-gray-500">No tags assigned</p>
          ) : (
            tags.map(({ tags: tag }) => (
              <span
                key={tag.id}
                className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
              >
                {tag.name}
                <button
                  onClick={() => removeTag(tag.id)}
                  disabled={loading}
                  className="hover:text-blue-600"
                >
                  ×
                </button>
              </span>
            ))
          )}
        </div>
      </div>

      {unassignedTags.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-2">Add Existing Tag</h4>
          <div className="flex flex-wrap gap-2">
            {unassignedTags.map(tag => (
              <button
                key={tag.id}
                onClick={() => addTag(tag.id)}
                disabled={loading}
                className="px-3 py-1 border border-gray-300 rounded-full text-sm hover:bg-gray-50"
              >
                + {tag.name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Create New Tag</h4>
        <div className="flex gap-2">
          <Input
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            placeholder="Tag name"
            onKeyPress={(e) => e.key === 'Enter' && createAndAddTag()}
          />
          <Button onClick={createAndAddTag} disabled={!newTagName.trim() || loading}>
            Create
          </Button>
        </div>
      </div>
    </div>
  )
}
