<script setup lang="ts">
import { ref, nextTick, watch, computed, onMounted, onBeforeUnmount } from 'vue'
import { Send, X, ChevronDown, ChevronRight, Wrench, Trash2 } from 'lucide-vue-next'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'
import type { ChatMessage, ChatStreamEvent, GraphNode, NodeDetail } from '@/types'
import { chat, getNodeDetail } from '@/api'
import MarkdownIt from 'markdown-it'

// Display message extends ChatMessage with UI state
interface DisplayMessage extends ChatMessage {
    id: string
    isStreaming?: boolean
}

const props = defineProps<{
    droppedNode?: GraphNode | null
}>()

const emit = defineEmits<{
    'update:droppedNode': [node: GraphNode | null]
    'nodeHover': [nodeId: string | null]
    'nodeClick': [node: GraphNode]
}>()

// Full conversation history (will be sent to backend)
const conversationHistory = ref<ChatMessage[]>([])
// Messages for display (includes streaming state)
const displayMessages = ref<DisplayMessage[]>([])
// Current streaming message content (for delta accumulation)
const streamingContent = ref('')
// Collapsed state for tool calls and tool messages
const collapsedItems = ref<Set<string>>(new Set())

const inputValue = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement>()
const pendingNodes = ref<GraphNode[]>([])

// Markdown renderer
const md = new MarkdownIt({
    html: false,
    linkify: true,
    breaks: true,
})


// Node hover handling via event delegation on the messages container
function handleNodeMouseOver(e: Event) {
    const target = e.target as HTMLElement | null
    if (!target) return
    const el = target.closest('[data-node-id]') as HTMLElement | null
    if (el) {
        const nodeId = el.getAttribute('data-node-id')
        if (nodeId) emit('nodeHover', nodeId)
    }
}

function handleNodeMouseOut(e: Event) {
    const target = e.target as HTMLElement | null
    if (!target) return
    const el = target.closest('[data-node-id]') as HTMLElement | null
    if (el) {
        emit('nodeHover', null)
    }
}

async function handleNodeClickEvent(e: Event) {
    const target = e.target as HTMLElement | null
    if (!target) return
    const el = target.closest('[data-node-id]') as HTMLElement | null
    if (!el) return

    const nodeId = el.getAttribute('data-node-id')
    if (!nodeId) return

    try {
        // Fetch node detail from API and emit nodeClick with the GraphNode
        const detail: NodeDetail = await getNodeDetail(nodeId)
        if (detail && detail.node) {
            emit('nodeClick', detail.node)
        } else {
            // If API didn't return structured detail, emit minimal node object
            emit('nodeClick', { id: nodeId, label: nodeId, type: 'unknown' })
        }
    } catch (err) {
        console.error('Failed to load node detail for click:', err)
        // Fallback: emit minimal node object so UI can still open modal
        emit('nodeClick', { id: nodeId, label: nodeId, type: 'unknown' })
    }
}

onMounted(() => {
    if (messagesContainer.value) {
        messagesContainer.value.addEventListener('mouseover', handleNodeMouseOver)
        messagesContainer.value.addEventListener('mouseout', handleNodeMouseOut)
        messagesContainer.value.addEventListener('click', handleNodeClickEvent)
    }
})

onBeforeUnmount(() => {
    if (messagesContainer.value) {
        messagesContainer.value.removeEventListener('mouseover', handleNodeMouseOver)
        messagesContainer.value.removeEventListener('mouseout', handleNodeMouseOut)
        messagesContainer.value.removeEventListener('click', handleNodeClickEvent)
    }
})

function clearChat() {
    conversationHistory.value = []
    displayMessages.value = []
    streamingContent.value = ''
    collapsedItems.value.clear()
}

// Watch for dropped nodes
watch(
    () => props.droppedNode,
    (node) => {
        if (node) {
            const existsIndex = pendingNodes.value.findIndex((n) => n.id === node.id)
            if (existsIndex >= 0) {
                const [existing] = pendingNodes.value.splice(existsIndex, 1)
                if (existing) {
                    pendingNodes.value.push(existing)
                }
            } else {
                pendingNodes.value.push(node)
            }
            emit('update:droppedNode', null)
        }
    },
)

function removeNode(index: number) {
    pendingNodes.value.splice(index, 1)
}

function toggleCollapse(id: string) {
    if (collapsedItems.value.has(id)) {
        collapsedItems.value.delete(id)
    } else {
        collapsedItems.value.add(id)
    }
}

function isCollapsed(id: string): boolean {
    return collapsedItems.value.has(id)
}

function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

async function sendMessage() {
    const trimmedInput = inputValue.value.trim()
    if (!trimmedInput && pendingNodes.value.length === 0) return
    if (loading.value) return

    // Build message content with node references
    let content = trimmedInput
    if (pendingNodes.value.length > 0) {
        const nodeContext = pendingNodes.value
            .map((n) => `[[node:${n.id}|${n.label}]]`)
            .join(' ')
        content = nodeContext + (content ? '\n\n' + content : '')
    }

    // Add user message to display
    const userMessage: DisplayMessage = {
        id: generateId(),
        role: 'user',
        content,
    }
    displayMessages.value.push(userMessage)

    inputValue.value = ''
    pendingNodes.value = []
    loading.value = true
    streamingContent.value = ''

    // Create initial streaming placeholder
    const streamingMessageId = generateId()
    const streamingMessage: DisplayMessage = {
        id: streamingMessageId,
        role: 'assistant',
        content: '',
        isStreaming: true,
    }
    displayMessages.value.push(streamingMessage)

    scrollToBottom()

    try {
        // Build request with current history + new user message
        const requestMessages: ChatMessage[] = [
            ...conversationHistory.value,
            { role: 'user', content },
        ]

        const response = await chat({ messages: requestMessages })
        if (!response.body) throw new Error('No response body')

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        let buffer = ''

        while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })

            // Parse SSE events
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6)
                    if (data === '[DONE]') continue

                    try {
                        const event: ChatStreamEvent = JSON.parse(data)
                        handleStreamEvent(event, streamingMessageId)
                    } catch (e) {
                        console.error('Failed to parse SSE event:', e)
                    }
                }
            }
        }
    } catch (e) {
        console.error('Chat failed:', e)
        // Update streaming message with error
        const msg = displayMessages.value.find(m => m.id === streamingMessageId)
        if (msg) {
            msg.content = msg.content || '抱歉，发生了错误，请重试。'
            msg.isStreaming = false
        }
    } finally {
        loading.value = false
        // Ensure streaming state is cleared
        const msg = displayMessages.value.find(m => m.isStreaming)
        if (msg) {
            msg.isStreaming = false
        }
    }
}

function handleStreamEvent(event: ChatStreamEvent, streamingMessageId: string) {
    switch (event.event) {
        case 'message_delta':
            // Accumulate delta to the correct streaming message by id (server may emit message_id)
            if (event.delta) {
                const msgId = (event as any).message_id || (event as any).messageId || streamingMessageId
                if (!msgId) break

                let msg = displayMessages.value.find(m => m.id === msgId && m.isStreaming)
                if (!msg) {
                    // Create placeholder streaming message if it doesn't exist
                    msg = {
                        id: msgId,
                        role: 'assistant',
                        content: event.delta,
                        isStreaming: true,
                    }
                    displayMessages.value.push(msg)
                } else {
                    msg.content = (msg.content || '') + event.delta
                }
                scrollToBottom()
            }
            break

        case 'message_complete':
            // Replace streaming message with complete message, or add new message
            if (event.message) {
                const msgId = (event as any).message_id || (event as any).messageId || streamingMessageId
                const completeMessage: DisplayMessage = {
                    id: msgId || generateId(),
                    ...event.message,
                    isStreaming: false,
                }

                // Try to find existing placeholder by id
                let replaced = false
                if (msgId) {
                    const idx = displayMessages.value.findIndex(m => m.id === msgId)
                    if (idx >= 0) {
                        displayMessages.value[idx] = completeMessage
                        replaced = true
                    }
                }

                if (!replaced) {
                    // As fallback, replace first streaming assistant placeholder
                    const streamingIdx = displayMessages.value.findIndex(
                        m => m.isStreaming && m.role === 'assistant'
                    )
                    if (streamingIdx >= 0 && event.message.role === 'assistant') {
                        displayMessages.value[streamingIdx] = completeMessage
                    } else {
                        displayMessages.value.push(completeMessage)
                    }
                }

                // Auto-collapse tool messages
                if (event.message.role === 'tool') {
                    collapsedItems.value.add(completeMessage.id)
                }
                // Ensure tool calls have unique ids so expand/collapse works per item
                if (event.message.tool_calls) {
                    for (const tc of event.message.tool_calls) {
                        // Some backends might omit an id for tool calls; generate one as a fallback
                        if (!tc.id) {
                            tc.id = generateId()
                        }
                        collapsedItems.value.add(tc.id)
                    }
                }

                // If this was the streaming message, clear streamingContent
                if (msgId && streamingContent.value) streamingContent.value = ''

                scrollToBottom()
            }
            break

        case 'round_complete':
            // Update conversation history with complete messages
            if (event.messages) {
                conversationHistory.value = event.messages

                // Clear any remaining streaming state
                displayMessages.value = displayMessages.value.map(m => ({
                    ...m,
                    isStreaming: false,
                }))
            }
            break

        case 'error':
            console.error('Stream error:', event.error)
            const msg = displayMessages.value.find(m => m.isStreaming)
            if (msg) {
                msg.content = `错误: ${event.error || '未知错误'}`
                msg.isStreaming = false
            }
            break
    }
}

function scrollToBottom() {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
    })
}

function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
    }
}

function formatContent(content: string | null | undefined): string {
    if (!content) return ''

    // First render markdown
    let html = md.render(content)

    // Then replace node references with clickable badges
    // Format: [[node:doc:abc123|Display Name]] or [[node:doc:abc123]]
    html = html.replace(
        /\[\[node:([^\]|]+)(?:\|([^\]]+))?\]\]/g,
        (match, nodeId, displayName) => {
            const display = displayName || nodeId
            return `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-200 cursor-pointer hover:bg-emerald-200 transition-colors" data-node-id="${nodeId}">${display}</span>`
        }
    )

    return html
}

function formatToolArgs(args: string): string {
    try {
        const parsed = JSON.parse(args)
        return JSON.stringify(parsed, null, 2)
    } catch {
        return args
    }
}
</script>

<template>
    <div class="flex h-full flex-col" data-chat-panel>
        <!-- Messages -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3">
            <div v-if="displayMessages.length === 0" class="flex h-full items-center justify-center text-stone-400">
                <p class="text-center">
                    开始对话，或在节点详情点击"加入上下文"将节点添加到对话
                </p>
            </div>

            <template v-for="message in displayMessages" :key="message.id">
                <!-- User Message -->
                <div v-if="message.role === 'user'" class="flex justify-end">
                    <div class="max-w-[85%] rounded-xl px-4 py-3 bg-stone-600 text-stone-50">
                        <div class="prose prose-sm prose-invert max-w-none" v-html="formatContent(message.content)" />
                    </div>
                </div>

                <!-- Assistant Message -->
                <div v-else-if="message.role === 'assistant'" class="flex justify-start">
                    <div class="max-w-[85%] space-y-2">
                        <!-- Text content -->
                        <div v-if="message.content"
                            class="rounded-xl px-4 py-3 bg-white border border-stone-200 text-stone-700">
                            <div class="prose prose-sm prose-stone max-w-none"
                                v-html="formatContent(message.content)" />
                        </div>

                        <!-- Tool calls (collapsible) -->
                        <div v-if="message.tool_calls && message.tool_calls.length > 0" class="space-y-1">
                            <div v-for="toolCall in message.tool_calls" :key="toolCall.id"
                                class="rounded-lg border border-amber-200 bg-amber-50 overflow-hidden">
                                <button @click="toggleCollapse(toolCall.id)"
                                    class="w-full px-3 py-2 flex items-center gap-2 text-left hover:bg-amber-100 transition-colors">
                                    <component :is="isCollapsed(toolCall.id) ? ChevronRight : ChevronDown"
                                        class="w-4 h-4 text-amber-600" />
                                    <Wrench class="w-4 h-4 text-amber-600" />
                                    <span class="text-sm font-medium text-amber-800">
                                        调用工具: {{ toolCall.name }}
                                    </span>
                                </button>
                                <div v-if="!isCollapsed(toolCall.id)"
                                    class="px-3 pb-3 border-t border-amber-200 bg-amber-50/50">
                                    <pre
                                        class="text-xs text-amber-700 mt-2 whitespace-pre-wrap font-mono">{{ formatToolArgs(toolCall.arguments) }}</pre>
                                </div>
                            </div>
                        </div>

                        <!-- Streaming indicator -->
                        <Spinner v-if="message.isStreaming && !message.content && !message.tool_calls" size="sm"
                            class="mt-2" />
                    </div>
                </div>

                <!-- Tool Response Message (collapsible) -->
                <div v-else-if="message.role === 'tool'" class="flex justify-start">
                    <div class="max-w-[85%] rounded-lg border border-blue-200 bg-blue-50 overflow-hidden">
                        <button @click="toggleCollapse(message.id)"
                            class="w-full px-3 py-2 flex items-center gap-2 text-left hover:bg-blue-100 transition-colors">
                            <component :is="isCollapsed(message.id) ? ChevronRight : ChevronDown"
                                class="w-4 h-4 text-blue-600" />
                            <Wrench class="w-4 h-4 text-blue-600" />
                            <span class="text-sm font-medium text-blue-800">
                                工具结果: {{ message.name }}
                            </span>
                        </button>
                        <div v-if="!isCollapsed(message.id)"
                            class="px-3 pb-3 border-t border-blue-200 bg-blue-50/50 max-h-64 overflow-y-auto">
                            <pre
                                class="text-xs text-blue-700 mt-2 whitespace-pre-wrap font-mono">{{ message.content }}</pre>
                        </div>
                    </div>
                </div>
            </template>
        </div>

        <!-- Pending nodes -->
        <div v-if="pendingNodes.length > 0"
            class="flex flex-wrap gap-2 border-t border-stone-200 bg-stone-50 px-4 py-2">
            <div v-for="(node, index) in pendingNodes" :key="node.id"
                class="flex items-center gap-1 rounded-lg bg-white border border-stone-300 px-2 py-1">
                <span class="text-sm text-stone-600">{{ node.label }}</span>
                <button class="text-stone-400 hover:text-stone-600" @click="removeNode(index)">
                    <X class="h-3 w-3" />
                </button>
            </div>
        </div>

        <!-- Input -->
        <div class="border-t border-stone-200 p-4">
            <div class="flex gap-2">
                <Button v-if="displayMessages.length > 0" @click="clearChat" variant="ghost" title="清空对话"
                    class="text-stone-400 hover:text-stone-600">
                    <Trash2 class="h-4 w-4" />
                </Button>
                <Input v-model="inputValue" placeholder="输入消息..." class="flex-1" @keydown="handleKeydown" />
                <Button @click="sendMessage" :disabled="loading">
                    <Send class="h-4 w-4" />
                </Button>
            </div>
        </div>
    </div>
</template>
