import type {
    GraphOverview,
    NodeDetail,
    SearchRequest,
    SearchResult,
    ChatRequest,
} from '@/types'

// API base can be configured via Vite env var `VITE_API_BASE` (e.g. in .env)
// Fallback to localhost when the env var is not provided.
const API_BASE = (import.meta.env.VITE_API_BASE as string) || 'http://127.0.0.1:8080/api'

// Graph API
export async function getGraphOverview(): Promise<GraphOverview> {
    const res = await fetch(`${API_BASE}/graph/overview`)
    if (!res.ok) throw new Error('Failed to fetch graph overview')
    return res.json()
}

export async function getNodeDetail(nodeId: string): Promise<NodeDetail> {
    const res = await fetch(`${API_BASE}/graph/node/${encodeURIComponent(nodeId)}`)
    if (!res.ok) throw new Error('Failed to fetch node detail')
    return res.json()
}

export async function searchGraph(request: SearchRequest): Promise<SearchResult> {
    const res = await fetch(`${API_BASE}/graph/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    })
    if (!res.ok) throw new Error('Failed to search graph')
    return res.json()
}

// Chat API - returns a ReadableStream for streaming response
export async function chat(request: ChatRequest): Promise<Response> {
    const res = await fetch(`${API_BASE}/chat/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    })
    if (!res.ok) throw new Error('Failed to send chat message')
    return res
}

// Ingest API
export async function uploadDocument(
    file?: File | null,
    title?: string | null,
    content?: string | null,
    type: string = 'text',
    meta?: string | null,
): Promise<unknown> {
    const formData = new FormData()
    if (file) formData.append('file', file)
    if (title) formData.append('title', title)
    if (content) formData.append('content', content)
    formData.append('type', type)
    if (meta) formData.append('meta', meta)

    const res = await fetch(`${API_BASE}/ingest/upload`, {
        method: 'POST',
        body: formData,
    })
    if (!res.ok) throw new Error('Failed to upload document')
    return res.json()
}

export async function deleteDocument(docId: string): Promise<unknown> {
    const res = await fetch(`${API_BASE}/ingest/documents/${encodeURIComponent(docId)}`, {
        method: 'DELETE',
    })
    if (!res.ok) {
        throw new Error('Failed to delete document')
    }
    return res.json()
}
