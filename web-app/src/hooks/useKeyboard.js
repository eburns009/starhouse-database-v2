import { useEffect } from 'react'

export function useKeyboard(key, handler, options = {}) {
  useEffect(() => {
    if (!key || !handler) return

    const handleKeyDown = (event) => {
      // Check modifiers
      const ctrlPressed = event.ctrlKey || event.metaKey
      const shiftPressed = event.shiftKey
      const altPressed = event.altKey

      // Check if this key matches
      const keyMatches = event.key.toLowerCase() === key.toLowerCase() || event.key === key

      // Check if modifiers match
      const ctrlMatches = options.ctrl ? ctrlPressed : !ctrlPressed || key === 'Escape'
      const shiftMatches = options.shift ? shiftPressed : !shiftPressed
      const altMatches = options.alt ? altPressed : !altPressed

      if (keyMatches && ctrlMatches && shiftMatches && altMatches) {
        handler(event)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [key, handler, options.ctrl, options.shift, options.alt])
}
