<script setup lang="ts">
import { ref } from 'vue'
import { Search, MessageSquare, Library } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import KnowledgeGraph from '@/components/KnowledgeGraph.vue'
import SearchPanel from '@/components/SearchPanel.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import NodeDetailModal from '@/components/NodeDetailModal.vue'
import Button from '@/components/ui/Button.vue'
import type { GraphNode } from '@/types'

type TabType = 'search' | 'chat'

const activeTab = ref<TabType>('search')
const selectedNode = ref<GraphNode | null>(null)
const modalOpen = ref(false)
const droppedNode = ref<GraphNode | null>(null)

function handleNodeClick(node: GraphNode) {
  selectedNode.value = node
  modalOpen.value = true
}

function handleAddToContext(node: GraphNode) {
  droppedNode.value = node
  activeTab.value = 'chat'
}

function handleRecommendationClick(node: GraphNode) {
  selectedNode.value = node
  modalOpen.value = true
}
</script>

<template>
  <div class="flex h-screen bg-stone-100">
    <!-- Main graph area -->
    <div class="relative flex-1">
      <!-- Header with nav -->
      <div class="absolute left-8 top-8 z-10">
        <RouterLink to="/library">
          <Button variant="secondary" class="bg-white/90">
            <Library class="mr-2 h-4 w-4" />
            知识库
          </Button>
        </RouterLink>
      </div>

      <div class="h-full rounded-2xl border-stone-200 bg-white overflow-hidden">
        <KnowledgeGraph @node-click="handleNodeClick" />
      </div>
    </div>

    <!-- Side panel -->
    <div class="w-96 flex flex-col border-l border-stone-200 bg-white">
      <!-- Tabs -->
      <div class="flex border-b border-stone-200">
        <button :class="[
          'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
          activeTab === 'search'
            ? 'border-b-2 border-stone-600 text-stone-700'
            : 'text-stone-400 hover:text-stone-600',
        ]" @click="activeTab = 'search'">
          <Search class="h-4 w-4" />
          搜索
        </button>
        <button :class="[
          'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
          activeTab === 'chat'
            ? 'border-b-2 border-stone-600 text-stone-700'
            : 'text-stone-400 hover:text-stone-600',
        ]" @click="activeTab = 'chat'">
          <MessageSquare class="h-4 w-4" />
          对话
        </button>
      </div>

      <!-- Panel content -->
      <div class="flex-1 overflow-hidden">
        <SearchPanel v-if="activeTab === 'search'" @node-click="handleNodeClick" />
        <ChatPanel v-else v-model:dropped-node="droppedNode" />
      </div>
    </div>

    <!-- Node detail modal -->
    <NodeDetailModal :node="selectedNode" v-model:open="modalOpen" @node-click="handleRecommendationClick"
      @add-to-context="handleAddToContext" />
  </div>
</template>
