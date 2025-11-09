import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function DebugData() {
  const [data, setData] = useState({
    contacts: 0,
    subscriptions: 0,
    tags: 0,
    transactions: 0,
    products: 0,
    sampleSubscriptions: [],
    sampleTags: [],
    sampleProducts: [],
    sourceSystems: []
  })

  useEffect(() => {
    fetchDebugData()
  }, [])

  async function fetchDebugData() {
    try {
      // Count contacts
      const { count: contactCount } = await supabase
        .from('contacts')
        .select('*', { count: 'exact', head: true })

      // Count subscriptions
      const { count: subsCount, data: subsData } = await supabase
        .from('subscriptions')
        .select('*', { count: 'exact' })
        .limit(5)

      // Count tags
      const { count: tagCount, data: tagData } = await supabase
        .from('tags')
        .select('*', { count: 'exact' })
        .limit(10)

      // Count transactions
      const { count: transCount } = await supabase
        .from('transactions')
        .select('*', { count: 'exact', head: true })

      // Count and sample products
      const { count: productCount, data: productData } = await supabase
        .from('products')
        .select('*', { count: 'exact' })
        .limit(10)

      // Get source systems
      const { data: contactsData } = await supabase
        .from('contacts')
        .select('source_system')
        .not('source_system', 'is', null)
        .limit(1000)

      const uniqueSources = [...new Set(contactsData?.map(c => c.source_system).filter(Boolean))]

      setData({
        contacts: contactCount || 0,
        subscriptions: subsCount || 0,
        tags: tagCount || 0,
        transactions: transCount || 0,
        products: productCount || 0,
        sampleSubscriptions: subsData || [],
        sampleTags: tagData || [],
        sampleProducts: productData || [],
        sourceSystems: uniqueSources
      })
    } catch (err) {
      console.error('Debug error:', err)
    }
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'monospace', fontSize: '14px' }}>
      <h2>Database Debug Info</h2>

      <div style={{ marginTop: '2rem' }}>
        <h3>Table Counts:</h3>
        <ul>
          <li>Contacts: {data.contacts.toLocaleString()}</li>
          <li>Subscriptions: {data.subscriptions.toLocaleString()}</li>
          <li>Tags: {data.tags.toLocaleString()}</li>
          <li>Transactions: {data.transactions.toLocaleString()}</li>
          <li>Products: {data.products.toLocaleString()}</li>
        </ul>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h3>Source Systems Found:</h3>
        <ul>
          {data.sourceSystems.map(source => (
            <li key={source}>{source}</li>
          ))}
        </ul>
      </div>

      {data.sampleSubscriptions.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Sample Subscriptions (first 5):</h3>
          <pre style={{ background: '#f5f5f5', padding: '1rem', overflow: 'auto' }}>
            {JSON.stringify(data.sampleSubscriptions, null, 2)}
          </pre>
        </div>
      )}

      {data.sampleTags.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Sample Tags:</h3>
          <pre style={{ background: '#f5f5f5', padding: '1rem', overflow: 'auto' }}>
            {JSON.stringify(data.sampleTags, null, 2)}
          </pre>
        </div>
      )}

      {data.sampleProducts.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Sample Products:</h3>
          <pre style={{ background: '#f5f5f5', padding: '1rem', overflow: 'auto' }}>
            {JSON.stringify(data.sampleProducts, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
