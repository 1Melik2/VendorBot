import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  // State variables — these control what the UI shows
  const [file, setFile] = useState(null)           // the selected PDF file
  const [status, setStatus] = useState("")          // "uploading", "success", "error"
  const [message, setMessage] = useState("")        // status message to display
  const [invoiceData, setInvoiceData] = useState(null) // extracted data from backend

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

  return (
    <div className="app">
      <h1>VendorBot</h1>
      <p className="subtitle">Automated Invoice Upload for VendorCafe</p>

      {/* Drop zone area */}
      <div
        className="dropzone"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        {file ? (
          <p>Selected: {file.name}</p>
        ) : (
          <p>Drag and drop a PDF here, or click below to browse</p>
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
    </div>
  )
}

export default App
