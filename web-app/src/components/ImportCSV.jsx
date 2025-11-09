import { useState } from 'react'
import { supabase } from '../lib/supabase'
import './ImportCSV.css'

export default function ImportCSV() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState([])
  const [importing, setImporting] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  function handleFileChange(e) {
    const selectedFile = e.target.files[0]
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile)
      setError(null)
      parseCSV(selectedFile)
    } else {
      setError('Please select a valid CSV file')
      setFile(null)
      setPreview([])
    }
  }

  function parseCSV(file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const text = e.target.result
        const lines = text.split('\n').filter(line => line.trim())

        if (lines.length === 0) {
          setError('CSV file is empty')
          return
        }

        // Auto-detect delimiter (tab or comma)
        const firstLine = lines[0]
        const delimiter = firstLine.includes('\t') ? '\t' : ','

        const headers = firstLine.split(delimiter).map(h => h.trim())

        console.log('Headers found:', headers)
        console.log('Delimiter:', delimiter === '\t' ? 'TAB' : 'COMMA')

        const data = lines.slice(1, 6).map(line => {
          const values = line.split(delimiter)
          return headers.reduce((obj, header, index) => {
            obj[header] = values[index]?.trim() || ''
            return obj
          }, {})
        })

        console.log('Data before filter:', data)
        console.log('First row keys:', data.length > 0 ? Object.keys(data[0]) : 'no data')

        const filteredData = data.filter(row => row.ID || row.id)
        console.log('Data after filter:', filteredData)
        console.log('Filtered data length:', filteredData.length)

        if (filteredData.length === 0) {
          setError('No valid data rows found in CSV')
          return
        }

        console.log('About to set preview with:', filteredData)
        setPreview(filteredData)
        console.log('setPreview called')
      } catch (err) {
        console.error('Parse error:', err)
        setError('Error parsing CSV: ' + err.message)
      }
    }
    reader.readAsText(file)
  }

  async function handleImport() {
    if (!file) return

    setImporting(true)
    setError(null)
    setResults(null)

    try {
      const reader = new FileReader()
      reader.onload = async (e) => {
        const text = e.target.result
        const lines = text.split('\n').filter(line => line.trim())

        // Auto-detect delimiter
        const firstLine = lines[0]
        const delimiter = firstLine.includes('\t') ? '\t' : ','

        const headers = firstLine.split(delimiter).map(h => h.trim())

        const rows = lines.slice(1).map(line => {
          const values = line.split(delimiter)
          return headers.reduce((obj, header, index) => {
            obj[header] = values[index]?.trim() || ''
            return obj
          }, {})
        }).filter(row => row.ID || row.id)

        let contactsCreated = 0
        let contactsUpdated = 0
        let transactionsCreated = 0
        let transactionsSkipped = 0
        let productsMatched = 0
        let productsCreated = 0
        let errors = []

        for (const row of rows) {
          try {
            // 1. Find or create contact
            const email = row['Customer Email']
            if (!email) continue

            let { data: existingContact, error: contactLookupError } = await supabase
              .from('contacts')
              .select('id, address_line_1, address_line_2, city, state, postal_code, country, phone')
              .eq('email', email)
              .single()

            // PGRST116 means "not found" which is fine
            if (contactLookupError && contactLookupError.code !== 'PGRST116') {
              console.error('Contact lookup error:', contactLookupError)
              errors.push(`Row ${row['ID']}: Contact lookup error - ${contactLookupError.message}`)
              continue
            }

            const nameParts = (row['Customer Name'] || '').split(' ')
            const firstName = nameParts[0] || ''
            const lastName = nameParts.slice(1).join(' ') || ''

            const contactData = {
              email,
              first_name: firstName,
              last_name: lastName,
              kajabi_id: row['Customer ID'],
              phone: row['Phone'] || null,
              address_line_1: row['Address'] || null,
              address_line_2: row['Address 2'] || null,
              city: row['City'] || null,
              state: row['State'] || null,
              postal_code: row['Zipcode'] || null,
              country: row['Country'] || null,
              source_system: 'kajabi'
            }

            let contactId

            if (existingContact) {
              // Update only if address is missing or phone is missing
              const needsUpdate =
                (!existingContact.address_line_1 && contactData.address_line_1) ||
                (!existingContact.phone && contactData.phone)

              if (needsUpdate) {
                const updateData = {}
                if (!existingContact.address_line_1 && contactData.address_line_1) {
                  updateData.address_line_1 = contactData.address_line_1
                  updateData.address_line_2 = contactData.address_line_2
                  updateData.city = contactData.city
                  updateData.state = contactData.state
                  updateData.postal_code = contactData.postal_code
                  updateData.country = contactData.country
                }
                if (!existingContact.phone && contactData.phone) {
                  updateData.phone = contactData.phone
                }

                const { error: updateError } = await supabase
                  .from('contacts')
                  .update(updateData)
                  .eq('id', existingContact.id)

                if (updateError) {
                  console.error('Contact update error:', updateError)
                  errors.push(`Row ${row['ID']}: Contact update error - ${updateError.message}`)
                  continue
                }

                contactsUpdated++
              }
              contactId = existingContact.id
            } else {
              const { data: newContact, error: insertError } = await supabase
                .from('contacts')
                .insert([contactData])
                .select()
                .single()

              if (insertError) {
                console.error('Contact insert error:', insertError)
                errors.push(`Row ${row['ID']}: Contact insert error - ${insertError.message}`)
                continue
              }

              contactId = newContact.id
              contactsCreated++
            }

            // 2. Find or create product by Offer ID/Title
            const offerTitle = row['Offer Title']
            const offerId = row['Offer ID']
            let productId = null

            if (offerTitle && offerId) {
              // First try to find by Kajabi Offer ID
              let { data: product, error: productError } = await supabase
                .from('products')
                .select('id, name, kajabi_offer_id')
                .eq('kajabi_offer_id', offerId)
                .single()

              if (productError && productError.code !== 'PGRST116') {
                console.error('Product lookup error:', productError)
              }

              // If not found by Offer ID, try by name
              if (!product) {
                const { data: productByName } = await supabase
                  .from('products')
                  .select('id, name, kajabi_offer_id')
                  .ilike('name', offerTitle)
                  .single()

                product = productByName

                // If found by name, update with Offer ID
                if (product && !product.kajabi_offer_id) {
                  await supabase
                    .from('products')
                    .update({ kajabi_offer_id: offerId })
                    .eq('id', product.id)
                }
              }

              if (product) {
                productId = product.id
                productsMatched++
              } else {
                // Create new product from offer
                const { data: newProduct, error: productInsertError } = await supabase
                  .from('products')
                  .insert([{
                    name: offerTitle,
                    kajabi_offer_id: offerId,
                    active: true
                  }])
                  .select()
                  .single()

                if (productInsertError) {
                  console.error('Product insert error:', productInsertError, 'Offer:', offerTitle)
                  errors.push(`Row ${row['ID']}: Product insert error - ${productInsertError.message}`)
                } else if (newProduct) {
                  productId = newProduct.id
                  productsCreated++
                }
              }
            }

            // 3. Check if transaction already exists
            const { data: existingTx } = await supabase
              .from('transactions')
              .select('id')
              .eq('kajabi_transaction_id', row['ID'])
              .single()

            if (existingTx) {
              // Transaction already exists, skip it
              transactionsSkipped++
              continue
            }

            // Create new transaction
            // Map CSV status to payment_status enum
            let txStatus = 'completed'
            const csvStatus = (row['Status'] || '').toLowerCase()
            if (csvStatus === 'succeeded') txStatus = 'completed'
            else if (csvStatus === 'failed') txStatus = 'failed'
            else if (csvStatus === 'pending') txStatus = 'pending'
            else if (csvStatus === 'refunded') txStatus = 'refunded'

            // Map CSV type to transaction_type enum
            let txType = 'subscription'
            const csvType = (row['Type'] || '').toLowerCase()
            if (csvType.includes('purchase') || csvType.includes('one-time')) txType = 'purchase'
            else if (csvType.includes('subscription') || csvType.includes('recurring')) txType = 'subscription'
            else if (csvType.includes('refund')) txType = 'refund'

            const { error: txError } = await supabase
              .from('transactions')
              .insert([{
                contact_id: contactId,
                product_id: productId,
                kajabi_transaction_id: row['ID'],
                amount: parseFloat(row['Amount']) || 0,
                currency: row['Currency'] || 'USD',
                transaction_type: txType,
                payment_method: row['Payment Method'] || null,
                transaction_date: row['Created At'] || new Date().toISOString(),
                status: txStatus,
                payment_processor: row['Provider'] || null,
                order_number: row['Order No.'] || null,
                tax_amount: parseFloat(row['Tax Amount']) || null,
                quantity: parseInt(row['Quantity']) || 1,
                coupon_code: row['Coupon Used'] || null
              }])

            if (txError) {
              console.error('Transaction insert error:', txError, 'Row:', row['ID'])
              errors.push(`Row ${row['ID']}: Transaction error - ${txError.message}`)
            }

            if (!txError) {
              transactionsCreated++
            }

          } catch (err) {
            errors.push(`Row ${row.ID}: ${err.message}`)
          }
        }

        setResults({
          contactsCreated,
          contactsUpdated,
          transactionsCreated,
          transactionsSkipped,
          productsMatched,
          productsCreated,
          errors,
          total: rows.length
        })
      }
      reader.readAsText(file)
    } catch (err) {
      setError(err.message)
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="import-container">
      <h1>Import Transactions from CSV</h1>
      <p className="import-description">
        Upload your Kajabi transactions CSV to import transactions and update contact addresses
      </p>

      <div className="import-steps">
        <div className={`step ${file ? 'completed' : 'active'}`}>
          <div className="step-number">1</div>
          <div className="step-label">Select CSV File</div>
        </div>
        <div className="step-arrow">→</div>
        <div className={`step ${preview.length > 0 && !results ? 'active' : ''} ${results ? 'completed' : ''}`}>
          <div className="step-number">2</div>
          <div className="step-label">Preview Data</div>
        </div>
        <div className="step-arrow">→</div>
        <div className={`step ${results ? 'active' : ''}`}>
          <div className="step-number">3</div>
          <div className="step-label">Import & Review</div>
        </div>
      </div>

      <div className="import-section">
        <label htmlFor="csv-upload" className="upload-label">
          <input
            type="file"
            id="csv-upload"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <div className="upload-box">
            {file ? (
              <div>
                <p className="file-name">✓ {file.name}</p>
                <p className="file-size">{(file.size / 1024).toFixed(2)} KB</p>
              </div>
            ) : (
              <div>
                <p className="upload-icon">📄</p>
                <p>Click to select CSV file</p>
                <p className="upload-hint">or drag and drop</p>
              </div>
            )}
          </div>
        </label>

        {error && <div className="error-message">{error}</div>}

        {preview.length > 0 && !results && (
          <div className="preview-section">
            <div className="preview-header">
              <h3>📋 Preview Data (First 5 Rows)</h3>
              <p className="preview-description">
                Review the data below to make sure it looks correct before importing
              </p>
            </div>

            <div className="preview-summary">
              <div className="summary-item">
                <strong>File:</strong> {file?.name}
              </div>
              <div className="summary-item">
                <strong>Preview:</strong> Showing first 5 of many rows
              </div>
              <div className="summary-item">
                <strong>What will happen:</strong> Create/update contacts, add addresses, create transactions, create/match products
              </div>
            </div>

            <div className="preview-table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Amount</th>
                    <th>Offer</th>
                    <th>Address</th>
                    <th>Phone</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i}>
                      <td>{row['Customer Email']}</td>
                      <td>{row['Customer Name']}</td>
                      <td>${row['Amount']} {row['Currency']}</td>
                      <td>{row['Offer Title']}</td>
                      <td>{row['Address']}, {row['City']}, {row['State']} {row['Zipcode']}</td>
                      <td>{row['Phone']}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="preview-actions">
              <button
                className="cancel-btn"
                onClick={() => {
                  setFile(null)
                  setPreview([])
                  setError(null)
                }}
              >
                Cancel
              </button>
              <button
                className="import-btn"
                onClick={handleImport}
                disabled={importing}
              >
                {importing ? '⏳ Importing...' : '✓ Looks Good - Import All Data'}
              </button>
            </div>
          </div>
        )}

        {results && (
          <div className="results-section">
            <h3>Import Complete!</h3>
            <div className="results-stats">
              <div className="stat">
                <span className="stat-value">{results.contactsCreated}</span>
                <span className="stat-label">New Contacts</span>
              </div>
              <div className="stat">
                <span className="stat-value">{results.contactsUpdated}</span>
                <span className="stat-label">Contacts Updated</span>
              </div>
              <div className="stat">
                <span className="stat-value">{results.transactionsCreated}</span>
                <span className="stat-label">Transactions Added</span>
              </div>
              <div className="stat">
                <span className="stat-value">{results.transactionsSkipped}</span>
                <span className="stat-label">Transactions Skipped (Duplicates)</span>
              </div>
              <div className="stat">
                <span className="stat-value">{results.productsCreated}</span>
                <span className="stat-label">Products Created</span>
              </div>
              <div className="stat">
                <span className="stat-value">{results.productsMatched}</span>
                <span className="stat-label">Products Matched</span>
              </div>
            </div>

            {results.errors.length > 0 && (
              <div className="errors-list">
                <h4>Errors ({results.errors.length})</h4>
                {results.errors.slice(0, 10).map((err, i) => (
                  <p key={i} className="error-item">{err}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
