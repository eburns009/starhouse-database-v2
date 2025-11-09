import { useState, useCallback } from 'react'

export function useToast() {
  const [toasts, setToasts] = useState([])

  const showToast = useCallback((message, type = 'info', duration = 5000) => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type, duration }])
  }, [])

  const success = useCallback((message) => showToast(message, 'success'), [showToast])
  const error = useCallback((message) => showToast(message, 'error'), [showToast])
  const warning = useCallback((message) => showToast(message, 'warning'), [showToast])
  const info = useCallback((message) => showToast(message, 'info'), [showToast])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  return {
    toasts,
    showToast,
    success,
    error,
    warning,
    info,
    removeToast
  }
}
