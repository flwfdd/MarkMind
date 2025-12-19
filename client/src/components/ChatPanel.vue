<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { Send, X } from 'lucide-vue-next'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Spinner from '@/components/ui/Spinner.vue'
import type { ChatMessage, GraphNode } from '@/types'
import { chat } from '@/api'

interface DisplayMessage extends ChatMessage {
    id: string
    isStreaming?: boolean
}

const props = defineProps<{
    droppedNode?: GraphNode | null
}>()

const emit = defineEmits<{
    'update:droppedNode': [node: GraphNode | null]
}>()

const messages = ref<DisplayMessage[]>([])
const inputValue = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement>()
const pendingNodes = ref<GraphNode[]>([])

// Watch for dropped nodes
watch(
    () => props.droppedNode,
    (node) => {
        if (node) {
            const existsIndex = pendingNodes.value.findIndex((n) => n.id === node.id)
            if (existsIndex >= 0) {
                // 如果已经存在，将其移到末尾以示最近使用（并避免重复）
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

async function sendMessage() {
    const trimmedInput = inputValue.value.trim()
    if (!trimmedInput && pendingNodes.value.length === 0) return
    if (loading.value) return

    // Build message content
    let content = trimmedInput
    if (pendingNodes.value.length > 0) {
        const nodeContext = pendingNodes.value
            .map((n) => `[${n.type}: ${n.label}]${n.desc ? ` - ${n.desc}` : ''}`)
            .join('\n')
        content = nodeContext + (content ? '\n\n' + content : '')
    }

    const userMessage: DisplayMessage = {
        id: Date.now().toString(),
        role: 'user',
        content,
    }

    messages.value.push(userMessage)
    inputValue.value = ''
    pendingNodes.value = []

    // Create assistant message placeholder
    const assistantMessage: DisplayMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        isStreaming: true,
    }
    messages.value.push(assistantMessage)

    loading.value = true
    scrollToBottom()

    try {
        // Build chat history
        const chatMessages = messages.value
            .filter((m) => !m.isStreaming)
            .map((m) => ({ role: m.role, content: m.content }))

        const response = await chat({ messages: chatMessages })

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
                        const parsed = JSON.parse(data)
                        if (parsed.content) {
                            assistantMessage.content += parsed.content
                            scrollToBottom()
                        }
                    } catch {
                        // Raw text content
                        assistantMessage.content += data
                        scrollToBottom()
                    }
                }
            }
        }

        assistantMessage.isStreaming = false
    } catch (e) {
        console.error('Chat failed:', e)
        assistantMessage.content =
            assistantMessage.content || '抱歉，发生了错误，请重试。'
        assistantMessage.isStreaming = false
    } finally {
        loading.value = false
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

function formatContent(content: string): string {
    // Basic markdown-like formatting
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code class="bg-stone-200 px-1 rounded">$1</code>')
        .replace(/\n/g, '<br>')
}
</script>

<template>
    <div class="flex h-full flex-col" data-chat-panel>
        <!-- Messages -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
            <div v-if="messages.length === 0" class="flex h-full items-center justify-center text-stone-400">
                <p class="text-center">
                    开始对话，或在节点详情点击“加入上下文”将节点添加到对话
                </p>
            </div>

            <div v-for="message in messages" :key="message.id" :class="[
                'max-w-[85%] rounded-xl px-4 py-3',
                message.role === 'user'
                    ? 'ml-auto bg-stone-600 text-stone-50'
                    : 'bg-white border border-stone-200 text-stone-700',
            ]">
                <div v-if="message.role === 'assistant'" class="prose prose-sm prose-stone"
                    v-html="formatContent(message.content)" />
                <div v-else class="whitespace-pre-wrap text-sm">
                    {{ message.content }}
                </div>
                <Spinner v-if="message.isStreaming && !message.content" size="sm" class="mt-2" />
            </div>
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
                <Input v-model="inputValue" placeholder="输入消息..." class="flex-1" @keydown="handleKeydown" />
                <Button @click="sendMessage" :disabled="loading">
                    <Send class="h-4 w-4" />
                </Button>
            </div>
        </div>
    </div>
</template>
