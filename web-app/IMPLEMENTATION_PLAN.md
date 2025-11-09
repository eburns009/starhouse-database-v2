# Contacts Module - Complete Implementation Plan

**Start Date:** 2025-11-04
**Goal:** Implement all missing features for production-ready contacts module

---

## Implementation Order

### Phase 1: Foundation (Steps 1-4)
1. ✅ Set up Tailwind CSS + UI utilities
2. ✅ Create form components & validation
3. ✅ Add toast notification system
4. ✅ Create modal/dialog components

### Phase 2: Core CRUD (Steps 5-7)
5. ✅ Create Contact form with validation
6. ✅ Edit Contact form
7. ✅ Delete/Archive with confirmation

### Phase 3: Tags & Search (Steps 8-9)
8. ✅ Tags management (display, add, remove, filter)
9. ✅ Advanced search with multiple filters

### Phase 4: Bulk Operations (Steps 10-11)
10. ✅ Bulk selection UI
11. ✅ Bulk actions (tag, delete, export)

### Phase 5: Export & Extras (Steps 12-15)
12. ✅ CSV/Excel export
13. ✅ Duplicate detection UI
14. ✅ Keyboard shortcuts
15. ✅ Mobile responsiveness

---

## Technical Approach

**UI Framework:** Tailwind CSS (utility-first)
**Forms:** React Hook Form + Zod validation
**Notifications:** Custom toast system
**State:** React useState + useCallback (keep it simple)
**Export:** Papa Parse for CSV, SheetJS for Excel

---

## File Structure

```
web-app/src/
├── components/
│   ├── ui/              # Reusable UI components
│   │   ├── Button.jsx
│   │   ├── Input.jsx
│   │   ├── Select.jsx
│   │   ├── Modal.jsx
│   │   ├── Toast.jsx
│   │   └── Checkbox.jsx
│   ├── contacts/
│   │   ├── ContactListEnhanced.jsx    (UPDATE)
│   │   ├── ContactDetail.jsx          (UPDATE)
│   │   ├── ContactForm.jsx            (NEW)
│   │   ├── ContactEditForm.jsx        (NEW)
│   │   ├── DeleteConfirmation.jsx     (NEW)
│   │   ├── TagsManager.jsx            (NEW)
│   │   ├── AdvancedSearch.jsx         (NEW)
│   │   ├── BulkActionsBar.jsx         (NEW)
│   │   ├── ExportDialog.jsx           (NEW)
│   │   └── DuplicateDetection.jsx     (NEW)
│   └── ...
├── lib/
│   ├── supabase.js
│   ├── validation.js    (NEW - Zod schemas)
│   └── utils.js         (NEW - helpers)
└── hooks/
    ├── useToast.js      (NEW)
    ├── useKeyboard.js   (NEW)
    └── useContacts.js   (NEW - data fetching)
```

---

## Dependencies to Add

```json
{
  "dependencies": {
    "react-hook-form": "^7.x",
    "zod": "^3.x",
    "@hookform/resolvers": "^3.x",
    "papaparse": "^5.x",
    "xlsx": "^0.18.x"
  },
  "devDependencies": {
    "tailwindcss": "^3.x",
    "postcss": "^8.x",
    "autoprefixer": "^10.x"
  }
}
```

---

## Implementation Timeline

**Phase 1-2:** ~2 hours (Foundation + Core CRUD)
**Phase 3:** ~1 hour (Tags & Search)
**Phase 4:** ~1 hour (Bulk Operations)
**Phase 5:** ~1 hour (Export & Polish)

**Total Estimated Time:** ~5 hours of focused implementation

---

## Let's Begin!

Starting with Phase 1: Foundation
