import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [step, setStep] = useState("")            // "checking", "pending", "uploading", "success", "skipped", "error"
  const [message, setMessage] = useState("")
  const [invoiceData, setInvoiceData] = useState(null)
  const [pendingPOs, setPendingPOs] = useState(null)
  const [loadingPOs, setLoadingPOs] = useState(false)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setStep("")
    setMessage("")
    setInvoiceData(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.name.endsWith(".pdf")) {
      setFile(droppedFile)
      setStep("")
      setMessage("")
      setInvoiceData(null)
    } else {
      setMessage("Please drop a PDF file")
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file first")
      return
    }

    const formData = new FormData()
    formData.append("file", file)

    // Step 1: Check if PO is pending
    setStep("checking")
    setMessage("📄 Extracting PO number & checking VendorCafe...")
    setInvoiceData(null)

    try {
      const checkRes = await axios.post("/api/check-invoice", formData)
      setInvoiceData(checkRes.data.invoice_data)

      if (!checkRes.data.is_pending) {
        setStep("skipped")
        setMessage(checkRes.data.message)
        return
      }

      // Step 2: PO is pending — upload it
      setStep("uploading")
      setMessage(`✅ PO #${checkRes.data.invoice_data.po_number} is pending — uploading to VendorCafe...`)

      // Need to re-send the file since it's a new request
      const uploadForm = new FormData()
      uploadForm.append("file", file)

      const uploadRes = await axios.post("/api/upload-invoice", uploadForm)
      setStep("success")
      setMessage(uploadRes.data.message)

    } catch (error) {
      setStep("error")
      setMessage("Failed: " + (error.response?.data?.detail || error.message))
    }
  }

  const handleFetchPOs = async () => {
    setLoadingPOs(true)
    try {
      const invoices = await axios.get("/api/pending-pos")
      setPendingPOs(invoices.data.pos)
    } catch (error) {
      setMessage("Failed to fetch POs: " + (error.response?.data?.detail || error.message))
    }
    setLoadingPOs(false)
  }

  return (
    <div className="app">
      <div className="header">
        <h1>⚡ VendorBot</h1>
        <p className="subtitle">Automated Invoice Upload for VendorCafe</p>
      </div>

      {/* Drop zone */}
      <div
        className={`dropzone ${file ? 'dropzone-active' : ''}`}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        {file ? (
          <div className="file-selected">
            <span className="file-icon">📄</span>
            <p>{file.name}</p>
          </div>
        ) : (
          <>
            <span className="upload-icon">📁</span>
            <p>Drag and drop an invoice PDF here, or click below to browse</p>
          </>
        )}
        <input type="file" accept=".pdf" onChange={handleFileChange} id="file-input" />
        <label htmlFor="file-input" className="browse-btn">Browse Files</label>
      </div>

      {/* Upload button */}
      <button
        className="upload-btn"
        onClick={handleUpload}
        disabled={!file || step === "checking" || step === "uploading"}
      >
        {step === "checking" ? "Checking PO..." : step === "uploading" ? "Uploading..." : "Upload Invoice"}
      </button>

      {/* Progress steps */}
      {step && (
        <div className={`status ${step}`}>
          <p>{message}</p>
          {step === "uploading" && (
            <p className="status-hint">Review the form in the browser, then click Submit. Close the tab when done.</p>
          )}
        </div>
      )}

      {/* Show extracted data */}
      {invoiceData && (step === "success" || step === "skipped") && (
        <div className="result">
          <h3>{step === "skipped" ? "⊘ Invoice Skipped" : "✓ Invoice Uploaded"}</h3>
          <p>PO Number: {invoiceData.po_number}</p>
          <p>Invoice #: {invoiceData.invoice_num}</p>
          <p>Date: {invoiceData.date}</p>
          <p>Total: ${invoiceData.total}</p>
        </div>
      )}

      {/* Pending POs Section */}
      <hr className="section-divider" />
      <h2 className="section-title">📋 Pending Purchase Orders</h2>
      <button className="check-btn" onClick={handleFetchPOs} disabled={loadingPOs}>
        {loadingPOs ? "Checking VendorCafe..." : "Check Pending POs"}
      </button>

      {pendingPOs && pendingPOs.length > 0 && (
        <p className="po-count">
          {pendingPOs.length} invoice{pendingPOs.length > 1 ? 's' : ''} need uploading
        </p>
      )}

      {pendingPOs && pendingPOs.length > 0 && pendingPOs.map((po, i) => (
        <div className="po-card" key={i}>
          <div className="po-header">
            <span className="po-number">PO #{po.po_number}</span>
            <span className="po-pending">Pending: ${po.pending_amount}</span>
          </div>
          <div className="po-details">
            <span>{po.property_name}</span>
            <span>Unit {po.unit}</span>
            <span>Amount: ${po.po_amount}</span>
            <span>{po.order_date}</span>
          </div>
        </div>
      ))}

      <footer className="footer">
        <p>VendorBot v1.0</p>
      </footer>
    </div>
  )
}

export default App
