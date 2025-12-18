import { SearchResult } from '../types'
import { FileText, Calendar, Users, BookOpen, Loader2, ExternalLink } from 'lucide-react'

interface SearchResultsProps {
  results: SearchResult[]
  loading: boolean
  totalResults: number
  query: string
  onSelectDocument: (docId: string) => void
}

export default function SearchResults({
  results,
  loading,
  totalResults,
  query,
  onSelectDocument,
}: SearchResultsProps) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="w-8 h-8 text-pastel-purple animate-spin" />
        <span className="ml-3 text-gray-600">Searching through research papers...</span>
      </div>
    )
  }

  if (!query) {
    return (
      <div className="text-center py-20">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-pastel-purple/20 mb-4">
          <FileText className="w-10 h-10 text-pastel-purple" />
        </div>
        <p className="text-lg text-gray-600 font-medium">Enter a search query to find research papers</p>
        <p className="text-sm text-gray-500 mt-2">Use keywords related to your research interest</p>
      </div>
    )
  }

  if (results.length === 0 && query) {
    return (
      <div className="text-center py-20">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-pastel-blue/20 mb-4">
          <FileText className="w-10 h-10 text-pastel-blue" />
        </div>
        <p className="text-lg text-gray-700 font-semibold mb-2">No results found for "{query}"</p>
        <p className="text-sm text-gray-500 mb-4">Try different keywords or check your spelling</p>
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg max-w-md mx-auto">
          <p className="text-xs text-yellow-800 font-medium mb-1">Troubleshooting:</p>
          <ul className="text-xs text-yellow-700 text-left space-y-1">
            <li>• Ensure backend server is running on port 8000</li>
            <li>• Check browser console for errors (F12)</li>
            <li>• Verify search indices are loaded in backend</li>
          </ul>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <div className="flex justify-between items-center">
        <p className="text-gray-600">
          Found <span className="font-semibold text-gray-800">{totalResults}</span> result{totalResults !== 1 ? 's' : ''}
          {query && (
            <>
              {' '}for <span className="font-semibold text-gray-800">"{query}"</span>
            </>
          )}
        </p>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {results.map((result, index) => (
          <div
            key={result.doc_id}
            onClick={() => onSelectDocument(result.doc_id)}
            className="group relative bg-white rounded-2xl p-6 shadow-sm hover:shadow-xl 
                     border-2 border-transparent hover:border-pastel-purple/50 cursor-pointer
                     transition-all duration-300 hover:-translate-y-1"
            style={{
              background: 'linear-gradient(135deg, #ffffff 0%, #fef7ff 100%)',
            }}
          >
            {/* Ranking Badge */}
            <div className="absolute top-4 right-4">
              <span className="inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full 
                             bg-pastel-purple/30 text-primary-700 border border-pastel-purple/50">
                #{index + 1}
              </span>
            </div>

            {/* Title - Clickable */}
            <h3 
              className="text-xl font-bold text-gray-800 mb-3 pr-24 group-hover:text-primary-700 transition-colors
                       line-clamp-2 cursor-pointer"
            >
              {result.title || 'Untitled Document'}
            </h3>

            {/* Abstract Snippet - Clickable */}
            {result.abstract && (
              <p className="text-gray-600 mb-4 line-clamp-3 leading-relaxed cursor-pointer">
                {result.abstract}
              </p>
            )}

            {/* Metadata */}
            <div className="flex flex-wrap gap-4 text-sm mb-4">
              {result.authors && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Users className="w-4 h-4 text-pastel-blue" />
                  <span className="line-clamp-1 max-w-xs">{result.authors}</span>
                </div>
              )}
              {result.journal && (
                <div className="flex items-center gap-2 text-gray-600">
                  <BookOpen className="w-4 h-4 text-pastel-mint" />
                  <span>{result.journal}</span>
                </div>
              )}
              {result.publish_time && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar className="w-4 h-4 text-pastel-peach" />
                  <span>{result.publish_time}</span>
                </div>
              )}
            </div>

            {/* Click to View Link */}
            <div className="flex items-center gap-2 text-primary-600 font-medium text-sm 
                          group-hover:text-primary-700 transition-colors pt-2 border-t border-gray-100">
              <ExternalLink className="w-4 h-4" />
              <span>Click to view full paper</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
