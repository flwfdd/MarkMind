// Graph types
export interface GraphNode {
    id: string
    type: string
    label: string
    desc?: string | null
    meta?: Record<string, unknown> | null
    doc_type?: string | null
    created_at?: string | null
}

export interface GraphEdge {
    source: string
    target: string
    type: string
    desc?: string | null
}

export interface GraphOverview {
    nodes: GraphNode[]
    edges: GraphEdge[]
}

export interface NodeDetail {
    node: GraphNode
    full_content?: string | null
    recommendations: GraphNode[]
}

// Search types
export interface SearchRequest {
    query: string
    limit?: number
}

export interface SearchItem {
    score: number
    node: GraphNode
}

export interface SearchResult {
    results: SearchItem[]
}

// Chat types
export interface ChatMessage {
    role: string
    content: string
    name?: string | null
}

export interface ChatRequest {
    messages: ChatMessage[]
}

// Upload types
export interface UploadRequest {
    file?: File | null
    title?: string | null
    content?: string | null
    type?: string
    meta?: string | null
}
