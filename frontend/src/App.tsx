import { useState, useEffect, useCallback } from 'react'
import SearchBar from './components/SearchBar'
import SearchResults from './components/SearchResults'
import DocumentViewer from './components/DocumentViewer'
import { searchAPI, autocompleteAPI, getDocumentAPI } from './services/api'
import type { SearchResult, Document } from './types'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [showDocument, setShowDocument] = useState(false)
  const [totalResults, setTotalResults] = useState(0)

  const handleSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      setTotalResults(0)
      setQuery('')
      return
    }

    setLoading(true)
    setQuery(searchQuery.trim())
    try {
      // Use your ranking algorithm - results are already ranked by hybrid_rank
      const response = await searchAPI(searchQuery.trim(), 20) // Get top 20 based on ranking
      console.log('Search response:', response) // Debug log
      setResults(response.results || [])
      setTotalResults(response.total || 0)
      setQuery(response.query || searchQuery.trim())
    } catch (error: any) {
      console.error('Search error:', error)
      console.error('Error details:', error.response?.data || error.message)
      setResults([])
      setTotalResults(0)
      // Show user-friendly error
      if (error.response?.status === 503) {
        alert('Search engine is not ready. Please check if the backend server is running and initialized.')
      } else if (error.response?.status === 404) {
        alert('Backend API not found. Please ensure the backend server is running on port 8000.')
      } else {
        alert(`Search failed: ${error.message || 'Unknown error'}`)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const handleSelectDocument = useCallback(async (docId: string) => {
    setLoading(true)
    try {
      // Retrieve full document from data/docs
      const doc = await getDocumentAPI(docId)
      setSelectedDoc(doc)
      setShowDocument(true)
    } catch (error) {
      console.error('Error loading document:', error)
      alert('Error loading document. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleBackToResults = () => {
    setShowDocument(false)
    setSelectedDoc(null)
  }

  return (
    <div className="min-h-screen"
         style={{
           background: 'linear-gradient(135deg, #fef7ff 0%, #f0e8ff 25%, #e8d6ff 50%, #f0e8ff 75%, #fef7ff 100%)',
         }}>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <header className="mb-10 text-center">
          <h1 className="text-5xl font-bold mb-3 text-gray-800"
              style={{
                fontFamily: 'system-ui, -apple-system, sans-serif',
                letterSpacing: '0.5px',
              }}>
            CORD-19 Search Engine
          </h1>
          <p className="text-gray-600 text-lg">
            Advanced hybrid search powered by ranking algorithm
          </p>
        </header>

        {/* Search Bar */}
        <div className="mb-8">
          <SearchBar 
            onSearch={handleSearch}
            onAutocomplete={autocompleteAPI}
            initialQuery={query}
          />
        </div>

        {/* Results or Document Viewer */}
        {showDocument && selectedDoc ? (
          <DocumentViewer 
            document={selectedDoc}
            onBack={handleBackToResults}
          />
        ) : (
          <SearchResults
            results={results}
            loading={loading}
            totalResults={totalResults}
            query={query}
            onSelectDocument={handleSelectDocument}
          />
        )}
      </div>
    </div>
  )
}

export default App
