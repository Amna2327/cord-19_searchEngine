import { useState, useEffect, useRef } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string) => void
  onAutocomplete: (prefix: string, limit?: number) => Promise<string[]>
  initialQuery?: string
}

export default function SearchBar({ onSearch, onAutocomplete, initialQuery = '' }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false)
  const debounceTimerRef = useRef<number | null>(null)
  const searchBarRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchBarRef.current && !searchBarRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // If query is too short, clear suggestions
    if (query.trim().length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    // Debounce autocomplete
    setIsLoadingSuggestions(true)
    debounceTimerRef.current = window.setTimeout(async () => {
      try {
        const results = await onAutocomplete(query.trim(), 8)
        setSuggestions(results)
        setShowSuggestions(true)
      } catch (error) {
        console.error('Autocomplete error:', error)
        setSuggestions([])
      } finally {
        setIsLoadingSuggestions(false)
      }
    }, 300)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [query, onAutocomplete])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setShowSuggestions(false)
    onSearch(query.trim())
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    setShowSuggestions(false)
    onSearch(suggestion)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  return (
    <div ref={searchBarRef} className="relative w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <Search className="absolute left-4 text-primary-600 w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Search CORD-19 research papers..."
            className="w-full pl-12 pr-4 py-4 text-lg rounded-xl border-2 border-pastel-purple/30
                     bg-white text-gray-800
                     focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                     transition-all duration-200 shadow-lg hover:shadow-xl"
            style={{
              background: 'linear-gradient(135deg, #ffffff 0%, #fef7ff 100%)',
            }}
          />
          {isLoadingSuggestions && (
            <Loader2 className="absolute right-4 text-primary-600 w-5 h-5 animate-spin" />
          )}
        </div>
      </form>

      {/* Autocomplete Suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white rounded-xl shadow-xl border-2 border-pastel-purple/30 max-h-60 overflow-y-auto"
             style={{
               background: 'linear-gradient(135deg, #ffffff 0%, #fef7ff 100%)',
             }}>
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full text-left px-4 py-3 hover:bg-pastel-purple/20 
                       transition-colors duration-150 first:rounded-t-xl last:rounded-b-xl
                       text-gray-800 font-medium"
            >
              <span>{suggestion}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}


