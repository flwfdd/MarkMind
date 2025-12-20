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
export interface ToolCall {
    id: string
    name: string
    arguments: string // JSON string
}

export interface ChatMessage {
    role: 'system' | 'user' | 'assistant' | 'tool'
    content?: string | null
    // For assistant messages with tool calls
    tool_calls?: ToolCall[] | null
    // For tool response messages
    tool_call_id?: string | null
    name?: string | null
}

export interface ChatRequest {
    messages: ChatMessage[]
}

export interface ChatStreamEvent {
    event: 'message_delta' | 'message_complete' | 'round_complete' | 'error'
    messageId?: string | null
    delta?: string | null
    message?: ChatMessage | null
    messages?: ChatMessage[] | null
    error?: string | null
}

// Upload types
export interface UploadRequest {
    file?: File | null
    title?: string | null
    content?: string | null
    type?: string
    meta?: string | null
}
