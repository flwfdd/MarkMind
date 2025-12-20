<script setup lang="ts">
import { ref } from 'vue'
import { Search } from 'lucide-vue-next'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Spinner from '@/components/ui/Spinner.vue'
import type { GraphNode } from '@/types'
import { searchGraph } from '@/api'
import { getTypeLabel, getBadgeStyle } from '@/lib/nodeTypes'

const emit = defineEmits<{
    nodeClick: [node: GraphNode]
    nodeHover: [nodeId: string | null]
}>()

const query = ref('')
const results = ref<any[]>([])
const loading = ref(false)
const searched = ref(false)

async function handleSearch() {
    if (!query.value.trim()) return

    loading.value = true
    searched.value = true

    try {
        const data = await searchGraph({ query: query.value, limit: 10 })
        results.value = data.results || []
    } catch (e) {
        console.error('Search failed:', e)
        results.value = []
    } finally {
        loading.value = false
    }
}

function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
        handleSearch()
    }
}


</script>

<template>
    <div class="flex h-full flex-col">
        <!-- Search input -->
        <div class="flex gap-2 p-4">
            <Input v-model="query" placeholder="搜索知识库..." type="search" class="flex-1" @keydown="handleKeydown" />
            <Button @click="handleSearch" :disabled="loading">
                <Search class="h-4 w-4" />
            </Button>
        </div>

        <!-- Results -->
        <div class="flex-1 overflow-y-auto px-4 pb-4">
            <div v-if="loading" class="flex justify-center py-8">
                <Spinner />
            </div>

            <div v-else-if="searched && results.length === 0" class="py-8 text-center text-stone-400">
                未找到相关结果
            </div>

            <div v-else-if="results.length > 0" class="space-y-2">
                <div v-for="(item, index) in results" :key="item.node.id"
                    class="cursor-pointer rounded-lg border border-stone-200 bg-white p-3 transition-colors hover:bg-stone-50"
                    @click="emit('nodeClick', item.node)" @mouseenter="emit('nodeHover', item.node.id)"
                    @mouseleave="emit('nodeHover', null)">
                    <div class="flex items-start justify-between gap-2">
                        <div class="min-w-0 flex-1">
                            <div class="flex items-center gap-2">
                                <Badge :style="getBadgeStyle(item.node.type, item.node.doc_type)">
                                    {{ getTypeLabel(item.node.type, item.node.doc_type) }}
                                </Badge>
                                <span class="text-xs text-stone-400">
                                    {{ ((item.score ?? 0) * 100).toFixed(0) }}%
                                </span>
                            </div>
                            <h4 class="mt-1 truncate font-medium text-stone-700">
                                {{ item.node.label }}
                            </h4>
                            <p v-if="item.node.desc" class="mt-1 line-clamp-2 text-sm text-stone-500">
                                {{ item.node.desc }}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div v-else class="py-8 text-center text-stone-400">
                输入关键词搜索知识库
            </div>
        </div>
    </div>
</template>
