export interface SearchResult {
  doc_id: string
  score: number
  title?: string
  authors?: string
  journal?: string
  publish_time?: string
  abstract?: string
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  query: string
}

export interface Reference {
  ref_id: string
  bibref_id: string
  title?: string
  authors?: string
  year?: number
  venue?: string
  volume?: string
  pages?: string
  issn?: string
}

export interface Document {
  paper_id: string
  metadata: {
    title?: string
    authors?: string
    journal?: string
    publish_time?: string
  }
  abstract?: string
  sections?: string
  text?: string
  references?: Reference[]
}

export interface AutocompleteResponse {
  suggestions: string[]
  prefix: string
}


