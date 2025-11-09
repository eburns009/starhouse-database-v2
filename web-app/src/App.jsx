import { useState } from 'react'
import ContactsList from './components/ContactsList'
import ContactListEnhanced from './components/contacts/ContactListEnhanced'
import ContactDetail from './components/contacts/ContactDetail'
import DebugData from './components/DebugData'
import ImportCSV from './components/ImportCSV'
import MembershipDashboard from './components/MembershipDashboard'
import MembersList from './components/members/MembersList'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('members') // 'members', 'dashboard', 'contacts', 'import', 'debug'
  const [selectedContactId, setSelectedContactId] = useState(null)

  return (
    <div className="app">
      <nav className="app-nav">
        <button
          className={currentView === 'members' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setCurrentView('members')}
        >
          Members
        </button>
        <button
          className={currentView === 'dashboard' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setCurrentView('dashboard')}
        >
          Member Dashboard
        </button>
        <button
          className={currentView === 'contacts' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setCurrentView('contacts')}
        >
          Contacts
        </button>
        <button
          className={currentView === 'import' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setCurrentView('import')}
        >
          Import CSV
        </button>
        <button
          className={currentView === 'debug' ? 'nav-btn active' : 'nav-btn'}
          onClick={() => setCurrentView('debug')}
        >
          Database Info
        </button>
      </nav>

      {currentView === 'members' && <MembersList />}
      {currentView === 'dashboard' && <MembershipDashboard />}
      {currentView === 'contacts' && (
        <ContactListEnhanced onSelectContact={setSelectedContactId} />
      )}
      {currentView === 'import' && <ImportCSV />}
      {currentView === 'debug' && <DebugData />}

      {/* Contact Detail Modal */}
      {selectedContactId && (
        <ContactDetail
          contactId={selectedContactId}
          onClose={() => setSelectedContactId(null)}
        />
      )}
    </div>
  )
}

export default App
