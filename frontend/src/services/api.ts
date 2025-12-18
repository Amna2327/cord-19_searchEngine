import axios from 'axios'
import type { SearchResponse, Document, AutocompleteResponse } from '../types'

const API_BASE_URL = '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const searchAPI = async (query: string, limit: number = 15): Promise<SearchResponse> => {
  const response = await apiClient.post<SearchResponse>('/search', {
    query,
    limit,
    alpha: 0.6,
  })
  return response.data
}

export const autocompleteAPI = async (prefix: string, limit: number = 5): Promise<string[]> => {
  const response = await apiClient.get<AutocompleteResponse>('/autocomplete', {
    params: { prefix, limit },
  })
  return response.data.suggestions
}

export const getDocumentAPI = async (docId: string): Promise<Document> => {
  const response = await apiClient.get<Document>(`/document/${docId}`)
  return response.data
}


