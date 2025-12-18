import { Document } from '../types'
import { ArrowLeft, Calendar, Users, BookOpen, FileText, BookOpenCheck } from 'lucide-react'

interface DocumentViewerProps {
  document: Document
  onBack: () => void
}

function formatTextForDisplay(text: string | undefined): string {
  if (!text) return ''
  
  // Keep the text as-is but ensure proper whitespace handling
  let formatted = text
    // Clean up excessive spaces (but keep single spaces between words)
    .replace(/[ \t]{2,}/g, ' ')
    // Add line breaks after sentences for better readability
    .replace(/([.!?])\s+([A-Z])/g, '$1\n\n$2')
    // Clean up excessive line breaks
    .replace(/\n{4,}/g, '\n\n\n')
    .trim()
  
  return formatted
}

function formatTextWithSections(text: string | undefined): JSX.Element[] {
  if (!text) return []
  
  // Check if text contains section markers
  if (!text.includes('##SECTION_START##')) {
    // No sections, return as plain text
    return [
      <div key="plain-text" className="text-gray-700 leading-relaxed whitespace-pre-wrap">
        {text}
      </div>
    ]
  }
  
  // Split by section markers and parse
  const sectionPattern = /##SECTION_START##(.*?)##SECTION_END##/g
  const parts: JSX.Element[] = []
  const sections: Array<{ name: string; startIndex: number; endIndex: number }> = []
  let match
  
  // First pass: find all section markers
  while ((match = sectionPattern.exec(text)) !== null) {
    sections.push({
      name: match[1].trim(),
      startIndex: match.index,
      endIndex: sectionPattern.lastIndex
    })
  }
  
  // Second pass: extract text between sections and add headings
  for (let i = 0; i < sections.length; i++) {
    const section = sections[i]
    const nextSection = sections[i + 1]
    
    // Add section heading
    if (section.name) {
      parts.push(
        <h3 key={`heading-${section.startIndex}`} className="text-xl font-semibold text-gray-800 mt-6 mb-3 first:mt-0">
          {section.name}
        </h3>
      )
    }
    
    // Extract text content after this section marker
    const contentStart = section.endIndex
    const contentEnd = nextSection ? nextSection.startIndex : text.length
    const content = text.substring(contentStart, contentEnd).trim()
    
    if (content) {
      parts.push(
        <div key={`content-${section.startIndex}`} className="mb-4 text-gray-700 leading-relaxed whitespace-pre-wrap">
          {content}
        </div>
      )
    }
  }
  
  // Add any text before the first section
  if (sections.length > 0 && sections[0].startIndex > 0) {
    const textBefore = text.substring(0, sections[0].startIndex).trim()
    if (textBefore) {
      parts.unshift(
        <div key="text-before" className="mb-4 text-gray-700 leading-relaxed whitespace-pre-wrap">
          {textBefore}
        </div>
      )
    }
  }
  
  return parts.length > 0 ? parts : [
    <div key="plain-text" className="text-gray-700 leading-relaxed whitespace-pre-wrap">
      {text}
    </div>
  ]
}

function formatAbstract(abstract: string | undefined): string {
  if (!abstract) return ''
  // Add paragraph breaks for better readability
  return abstract
    .replace(/\b(background|methods|results|conclusion|introduction)\b/gi, '\n\n$1')
    .replace(/\s+/g, ' ')
    .trim()
}

function formatAuthors(authors: string | undefined): string {
  if (!authors) return ''
  // Format authors list nicely
  return authors
    .split(',')
    .map(a => a.trim())
    .join(', ')
}

export default function DocumentViewer({ document, onBack }: DocumentViewerProps) {
  const { metadata, abstract, sections, text, references } = document
  
  const formattedAbstract = formatAbstract(abstract)
  const formattedText = formatTextForDisplay(text)
  const formattedSections = formatTextForDisplay(sections)

  return (
    <div className="max-w-5xl mx-auto">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 mb-6 px-4 py-2 text-gray-600 
                 hover:text-primary-700 hover:bg-pastel-purple/20 rounded-lg
                 transition-all duration-200 font-medium"
      >
        <ArrowLeft className="w-5 h-5" />
        <span>Back to search results</span>
      </button>

      {/* Document Content */}
      <div className="bg-white rounded-2xl shadow-xl p-8 md:p-10 border border-gray-100"
           style={{
             background: 'linear-gradient(135deg, #ffffff 0%, #fef7ff 100%)',
           }}>
        
        {/* Title */}
        <h1 className="text-4xl font-bold text-gray-800 mb-6 leading-tight">
          {metadata.title || 'Untitled Document'}
        </h1>

        {/* Metadata Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 pb-8 border-b-2 border-pastel-purple/30">
          {metadata.authors && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-pastel-blue/30 border border-pastel-blue/50">
              <Users className="w-5 h-5 mt-0.5 flex-shrink-0 text-primary-600" />
              <div className="flex-1">
                <div className="font-semibold text-gray-700 mb-1 text-sm uppercase tracking-wide">Authors</div>
                <div className="text-gray-800 leading-relaxed">{formatAuthors(metadata.authors)}</div>
              </div>
            </div>
          )}
          
          {metadata.journal && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-pastel-mint/30 border border-pastel-mint/50">
              <BookOpen className="w-5 h-5 mt-0.5 flex-shrink-0 text-primary-600" />
              <div className="flex-1">
                <div className="font-semibold text-gray-700 mb-1 text-sm uppercase tracking-wide">Journal</div>
                <div className="text-gray-800">{metadata.journal}</div>
              </div>
            </div>
          )}
          
          {metadata.publish_time && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-pastel-peach/30 border border-pastel-peach/50">
              <Calendar className="w-5 h-5 mt-0.5 flex-shrink-0 text-primary-600" />
              <div className="flex-1">
                <div className="font-semibold text-gray-700 mb-1 text-sm uppercase tracking-wide">Published</div>
                <div className="text-gray-800">{metadata.publish_time}</div>
              </div>
            </div>
          )}
          
          <div className="flex items-start gap-3 p-4 rounded-xl bg-pastel-lavender/30 border border-pastel-lavender/50">
            <FileText className="w-5 h-5 mt-0.5 flex-shrink-0 text-primary-600" />
            <div className="flex-1">
              <div className="font-semibold text-gray-700 mb-1 text-sm uppercase tracking-wide">Paper ID</div>
              <div className="font-mono text-xs text-gray-600 break-all">{document.paper_id}</div>
            </div>
          </div>
        </div>

        {/* Abstract */}
        {formattedAbstract && (
          <section className="mb-10">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 pb-2 border-b-2 border-pastel-purple/30">
              Abstract
            </h2>
            <div className="text-gray-700 leading-relaxed text-lg whitespace-pre-line 
                          bg-pastel-purple/10 p-6 rounded-xl border border-pastel-purple/20">
              {formattedAbstract}
            </div>
          </section>
        )}

        {/* Sections */}
        {formattedSections && (
          <section className="mb-10">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 pb-2 border-b-2 border-pastel-blue/30">
              Key Sections
            </h2>
            <div className="text-gray-700 leading-relaxed whitespace-pre-line 
                          bg-pastel-blue/10 p-6 rounded-xl border border-pastel-blue/20">
              {formattedSections}
            </div>
          </section>
        )}

        {/* Full Text */}
        {(formattedText || text) && (
          <section className="mb-10">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 pb-2 border-b-2 border-pastel-mint/30">
              Full Paper Content
            </h2>
            <div className="p-6 rounded-xl
                          bg-gradient-to-b from-pastel-mint/10 to-pastel-lavender/10
                          border border-pastel-mint/20
                          text-base">
              {formatTextWithSections(text || formattedText)}
            </div>
          </section>
        )}
        
        {/* References */}
        {references && references.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4 pb-2 border-b-2 border-pastel-peach/30 flex items-center gap-2">
              <BookOpenCheck className="w-6 h-6 text-primary-600" />
              References
            </h2>
            <div className="space-y-3">
              {references.map((ref, idx) => (
                <div 
                  key={ref.bibref_id || idx}
                  className="p-4 rounded-lg bg-pastel-peach/10 border border-pastel-peach/30 hover:bg-pastel-peach/20 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <span className="font-mono text-sm font-semibold text-primary-700 mt-1 min-w-[60px]">
                      {ref.bibref_id}
                    </span>
                    <div className="flex-1">
                      {ref.title && (
                        <div className="font-semibold text-gray-800 mb-1">{ref.title}</div>
                      )}
                      <div className="text-sm text-gray-700 space-y-1">
                        {ref.authors && (
                          <div><span className="font-medium">Authors:</span> {ref.authors}</div>
                        )}
                        <div className="flex flex-wrap gap-3">
                          {ref.year && (
                            <span><span className="font-medium">Year:</span> {ref.year}</span>
                          )}
                          {ref.venue && (
                            <span><span className="font-medium">Venue:</span> {ref.venue}</span>
                          )}
                          {ref.volume && (
                            <span><span className="font-medium">Volume:</span> {ref.volume}</span>
                          )}
                          {ref.pages && (
                            <span><span className="font-medium">Pages:</span> {ref.pages}</span>
                          )}
                        </div>
                        {ref.issn && (
                          <div><span className="font-medium">ISSN:</span> {ref.issn}</div>
                        )}
                        {ref.ref_id && (
                          <div className="text-xs text-gray-500 mt-1">
                            <span className="font-medium">Ref ID:</span> {ref.ref_id}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
        
        {/* Show message if no text available */}
        {!formattedText && !text && !references && (
          <section>
            <div className="text-center py-8 text-gray-500 italic">
              Full text content is not available for this document.
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
