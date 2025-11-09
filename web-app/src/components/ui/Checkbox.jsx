import React, { forwardRef } from 'react'

const Checkbox = forwardRef(({
  label,
  error,
  className = '',
  ...props
}, ref) => {
  return (
    <div className="flex items-start">
      <div className="flex items-center h-5">
        <input
          ref={ref}
          type="checkbox"
          className={`
            w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded
            focus:ring-blue-500 focus:ring-2
            ${className}
          `}
          {...props}
        />
      </div>
      {label && (
        <div className="ml-2">
          <label className="text-sm font-medium text-gray-700">
            {label}
          </label>
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
        </div>
      )}
    </div>
  )
})

Checkbox.displayName = 'Checkbox'

export default Checkbox
