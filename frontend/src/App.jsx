import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  // State variables — these control what the UI shows
  const [file, setFile] = useState(null)           // the selected PDF file
  const [status, setStatus] = useState("")          // "uploading", "success", "error"
  const [message, setMessage] = useState("")        // status message to display
  const [invoiceData, setInvoiceData] = useState(null) // extracted data from backend
  const [pendingPOs, setPendingPOs] = useState(null)
  const [loadingPOs, setLoadingPOs] = useState(false)

  // Called when user selects a file
  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setStatus("")
    setMessage("")
  }

  // Called when user drops a file onto the drop zone
  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.name.endsWith(".pdf")) {
      setFile(droppedFile)
      setStatus("")
      setMessage("")
    } else {
      setMessage("Please drop a PDF file")
    }
  }

  // Called when user clicks "Upload"
  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file first")
      return
    }

    setStatus("uploading")
    setMessage("Processing invoice...")

    // FormData is how you send files over HTTP
    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await axios.post("http://localhost:8000/api/upload-invoice", formData)
      setStatus("success")
      setMessage("Invoice uploaded successfully!")
      setInvoiceData(response.data.invoice_data)
    } catch (error) {
      setStatus("error")
      setMessage("Upload failed: " + (error.response?.data?.detail || error.message))
    }
  }

  const handleFetchPOs = async () => {
    setLoadingPOs(true)
    try {
      const invoices = await axios.get("http://localhost:8000/api/pending-pos")
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

      {/* Drop zone area */}
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
            <p>Drag and drop a PDF here, or click below to browse</p>
          </>
        )}
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          id="file-input"
        />
        <label htmlFor="file-input" className="browse-btn">Browse Files</label>
      </div>

      {/* Upload button */}
      <button
        className="upload-btn"
        onClick={handleUpload}
        disabled={!file || status === "uploading"}
      >
        {status === "uploading" ? "Processing..." : "Upload Invoice"}
      </button>

      {/* Status message */}
      {message && (
        <p className={`status ${status}`}>{message}</p>
      )}

      {/* Show extracted data on success */}
      {invoiceData && (
        <div className="result">
          <h3>Extracted Data</h3>
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
