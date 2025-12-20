<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { Plus } from 'lucide-vue-next'
import type { GraphNode, NodeDetail } from '@/types'
import { getNodeDetail } from '@/api'
import { getTypeLabel, getBadgeStyle } from '@/lib/nodeTypes'

const props = defineProps<{
    node: GraphNode | null
    open: boolean
}>()

const emit = defineEmits<{
    'update:open': [value: boolean]
    nodeClick: [node: GraphNode]
    'add-to-context': [node: GraphNode]
}>()

const loading = ref(false)
const detail = ref<NodeDetail | null>(null)
const error = ref<string | null>(null)

watch(
    () => props.node,
    async (newNode) => {
        if (!newNode) {
            detail.value = null
            return
        }

        loading.value = true
        error.value = null

        try {
            detail.value = await getNodeDetail(newNode.id)
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Failed to load node detail'
            detail.value = null
        } finally {
            loading.value = false
        }
    },
    { immediate: true },
)



function handleRecommendationClick(node: GraphNode) {
    emit('update:open', false)
    setTimeout(() => {
        emit('nodeClick', node)
    }, 200)
}

function handleAddToContext(node: GraphNode) {
    // Close modal then notify parent to add node to chat context
    emit('update:open', false)
    setTimeout(() => {
        emit('add-to-context', node)
    }, 200)
}

// Helpers for linkifying text safely (escape + URL -> <a ...>)
function escapeHtml(str: string) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
}

const urlRegex = /((?:https?:\/\/|www\.)[^\s"'<>]+)/gi

function linkify(text: string) {
    if (!text) return ''
    const escaped = escapeHtml(text)
    return escaped.replace(urlRegex, (m) => {
        const href = m.startsWith('http') ? m : `https://${m}`
        return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="text-stone-600 underline">${m}</a>`
    })
}

const linkifiedDesc = computed(() => {
    return detail.value && detail.value.node && detail.value.node.desc
        ? linkify(detail.value.node.desc)
        : ''
})

const linkifiedFullContent = computed(() => {
    if (!detail.value || !detail.value.full_content) return ''
    // Keep original newlines and rely on CSS 'whitespace-pre-wrap' to preserve line breaks
    return linkify(detail.value.full_content)
})
</script>

<template>
    <Modal :open="open" @update:open="emit('update:open', $event)">
        <div v-if="loading" class="flex justify-center py-12">
            <Spinner size="lg" />
        </div>

        <div v-else-if="error" class="py-12 text-center text-stone-500">
            {{ error }}
        </div>

        <div v-else-if="detail" class="space-y-6">
            <!-- Header -->
            <div>
                <div class="flex items-center gap-2">
                    <Badge :style="getBadgeStyle(detail.node.type, detail.node.doc_type)">
                        {{ getTypeLabel(detail.node.type, detail.node.doc_type) }}
                    </Badge>
                    <Badge :style="getBadgeStyle(detail.node.type, detail.node.doc_type)"
                        class="cursor-pointer flex items-center gap-1" @click="handleAddToContext(detail.node)"
                        aria-label="加入上下文">
                        <Plus class="h-3 w-3" />
                        加入上下文
                    </Badge>
                </div>

                <h2 class="mt-2 text-xl font-semibold text-stone-800">
                    {{ detail.node.label }}
                </h2>
                <p v-if="detail.node.desc" class="mt-1 text-stone-500" v-html="linkifiedDesc"></p>
                <a v-if="detail.node.url" :href="detail.node.url" target="_blank" rel="noopener noreferrer"
                    class="text-sm text-stone-600 underline break-all">
                    {{ detail.node.url }}
                </a>
                <p v-if="detail.node.created_at" class="mt-1 text-xs text-stone-400">
                    创建于: {{ new Date(detail.node.created_at).toLocaleString() }}
                </p>
            </div>

            <!-- Content -->
            <div v-if="detail.full_content" class="max-h-64 overflow-y-auto rounded-lg bg-stone-100 p-4">
                <div class="whitespace-pre-wrap text-sm text-stone-700" v-html="linkifiedFullContent"></div>
            </div>

            <!-- Recommendations -->
            <div v-if="detail.recommendations.length > 0">
                <h3 class="mb-3 font-medium text-stone-700">相关推荐</h3>
                <div class="space-y-2">
                    <div v-for="rec in detail.recommendations" :key="rec.id"
                        class="cursor-pointer rounded-lg border border-stone-200 bg-white p-3 transition-colors hover:bg-stone-50"
                        @click="handleRecommendationClick(rec)">
                        <div class="flex items-center gap-2">
                            <Badge :style="getBadgeStyle(rec.type, rec.doc_type)" class="text-xs">
                                {{ getTypeLabel(rec.type, rec.doc_type) }}
                            </Badge>
                            <span class="font-medium text-stone-700">{{ rec.label }}</span>
                        </div>
                        <p v-if="rec.desc" class="mt-1 line-clamp-1 text-sm text-stone-500">
                            {{ rec.desc }}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </Modal>
</template>
