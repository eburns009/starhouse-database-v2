import Modal from '../ui/Modal'
import Button from '../ui/Button'

const shortcuts = [
  {
    category: 'Navigation',
    items: [
      { key: 'Ctrl + K', description: 'Open search' },
      { key: 'Ctrl + N', description: 'Create new contact' },
      { key: 'Escape', description: 'Close modal or cancel action' }
    ]
  },
  {
    category: 'Contact Actions',
    items: [
      { key: 'Ctrl + E', description: 'Edit contact (when viewing)' },
      { key: 'Ctrl + S', description: 'Save changes (when editing)' },
      { key: 'Ctrl + D', description: 'Delete contact (when viewing)' }
    ]
  },
  {
    category: 'List Operations',
    items: [
      { key: 'Ctrl + A', description: 'Select all contacts' },
      { key: 'Ctrl + Shift + A', description: 'Clear selection' },
      { key: 'Ctrl + F', description: 'Open advanced filters' }
    ]
  },
  {
    category: 'Bulk Actions',
    items: [
      { key: 'Ctrl + T', description: 'Add tag to selected' },
      { key: 'Ctrl + X', description: 'Export selected' }
    ]
  },
  {
    category: 'Help',
    items: [
      { key: 'Ctrl + /', description: 'Show this help dialog' },
      { key: '?', description: 'Show this help dialog' }
    ]
  }
]

export default function KeyboardShortcutsHelp({ isOpen, onClose }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Keyboard Shortcuts">
      <div style={{ minWidth: '500px' }}>
        <p style={{ marginBottom: '20px', color: '#6b7280', fontSize: '14px' }}>
          Use these keyboard shortcuts to navigate and perform actions quickly.
        </p>

        {shortcuts.map((section, idx) => (
          <div key={idx} style={{ marginBottom: '24px' }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#374151',
              marginBottom: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              {section.category}
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {section.items.map((item, itemIdx) => (
                <div
                  key={itemIdx}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px 12px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '6px'
                  }}
                >
                  <span style={{ fontSize: '14px', color: '#4b5563' }}>
                    {item.description}
                  </span>
                  <kbd style={{
                    padding: '4px 8px',
                    backgroundColor: 'white',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    color: '#374151',
                    fontWeight: '600',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                  }}>
                    {item.key}
                  </kbd>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          marginTop: '20px',
          paddingTop: '16px',
          borderTop: '1px solid #e5e7eb'
        }}>
          <Button variant="primary" onClick={onClose}>
            Got it!
          </Button>
        </div>
      </div>
    </Modal>
  )
}
