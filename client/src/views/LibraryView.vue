<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Upload, FileText, X, Plus, ArrowLeft, Trash } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'
import Modal from '@/components/ui/Modal.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { getGraphOverview, uploadDocument, deleteDocument } from '@/api'
import type { GraphNode } from '@/types'
import { getTypeLabel, getBadgeStyle } from '@/lib/nodeTypes'

const documents = ref<GraphNode[]>([])
const loading = ref(true)
const uploadModalOpen = ref(false)

// Upload form state
const uploadFile = ref<File | null>(null)
const uploadTitle = ref('')
const uploadContent = ref('')
const uploadType = ref('text')
const uploading = ref(false)
const uploadError = ref<string | null>(null)

const fileInputRef = ref<HTMLInputElement>()

const typeOptions = [
    { value: 'text', label: '文本' },
    { value: 'md', label: 'Markdown' },
    { value: 'pdf', label: 'PDF' },
]

async function loadDocuments() {
    loading.value = true
    try {
        const data = await getGraphOverview()
        // Graph nodes use type 'doc' for documents; sort by created_at desc
        documents.value = data.nodes
            .filter((n) => n.type === 'doc')
            .sort((a, b) => {
                const da = a.created_at ? new Date(a.created_at).getTime() : 0
                const db = b.created_at ? new Date(b.created_at).getTime() : 0
                return db - da
            })
    } catch (e) {
        console.error('Failed to load documents:', e)
    } finally {
        loading.value = false
    }
}

function handleFileSelect(e: Event) {
    const target = e.target as HTMLInputElement
    const file = target.files?.[0]
    if (file) {
        uploadFile.value = file
        if (!uploadTitle.value) {
            uploadTitle.value = file.name.replace(/\.[^/.]+$/, '')
        }
        // Auto-detect type
        if (file.name.endsWith('.pdf')) {
            uploadType.value = 'pdf'
        } else if (file.name.endsWith('.md')) {
            uploadType.value = 'md'
        }
    }
}

function clearFile() {
    uploadFile.value = null
    if (fileInputRef.value) {
        fileInputRef.value.value = ''
    }
}

async function confirmDelete(docId: string) {
    const ok = window.confirm('确定要删除该文档吗？此操作不可恢复。')
    if (!ok) return
    try {
        await deleteDocument(docId)
        await loadDocuments()
    } catch (e) {
        console.error('Delete failed:', e)
        alert(e instanceof Error ? e.message : '删除失败')
    }
}

function openFileDialog() {
    fileInputRef.value?.click()
}

async function handleUpload() {
    if (!uploadFile.value && !uploadContent.value) {
        uploadError.value = '请选择文件或输入内容'
        return
    }

    if (!uploadFile.value && !uploadTitle.value) {
        uploadError.value = '请输入标题'
        return
    }

    uploading.value = true
    uploadError.value = null

    try {
        await uploadDocument(
            uploadFile.value,
            uploadTitle.value || null,
            uploadContent.value || null,
            uploadType.value,
        )

        // Reset form
        uploadFile.value = null
        uploadTitle.value = ''
        uploadContent.value = ''
        uploadType.value = 'text'
        uploadModalOpen.value = false

        // Reload documents
        await loadDocuments()
    } catch (e) {
        uploadError.value = e instanceof Error ? e.message : '上传失败'
    } finally {
        uploading.value = false
    }
}

onMounted(() => {
    loadDocuments()
})
</script>

<template>
    <div class="min-h-screen bg-stone-100">
        <!-- Header -->
        <header class="border-b border-stone-200 bg-white">
            <div class="mx-auto max-w-5xl px-6 py-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <RouterLink to="/"
                            class="flex items-center gap-2 text-stone-400 hover:text-stone-600 transition-colors">
                            <ArrowLeft class="h-4 w-4" />
                            返回
                        </RouterLink>
                        <h1 class="text-xl font-semibold text-stone-700">知识库</h1>
                    </div>
                    <Button @click="uploadModalOpen = true">
                        <Plus class="mr-2 h-4 w-4" />
                        上传文档
                    </Button>
                </div>
            </div>
        </header>

        <!-- Content -->
        <main class="mx-auto max-w-5xl px-6 py-8">
            <div v-if="loading" class="flex justify-center py-16">
                <Spinner size="lg" />
            </div>

            <div v-else-if="documents.length === 0" class="flex flex-col items-center justify-center py-16">
                <FileText class="h-12 w-12 text-stone-300" />
                <p class="mt-4 text-stone-500">暂无文档</p>
                <Button class="mt-4" @click="uploadModalOpen = true">
                    <Plus class="mr-2 h-4 w-4" />
                    上传第一个文档
                </Button>
            </div>

            <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card v-for="doc in documents" :key="doc.id"
                    class="cursor-pointer transition-colors hover:bg-stone-100">
                    <div class="flex items-start justify-between">
                        <!-- Left: icon + badge -->
                        <div class="flex flex-col items-center gap-2 m-2 ml-0">
                            <div class="flex h-10 w-10 items-center justify-center rounded-lg"
                                :style="{ backgroundColor: getBadgeStyle('doc', doc.doc_type).backgroundColor }">
                                <FileText class="h-5 w-5 text-stone-600" />
                            </div>
                            <Badge :style="getBadgeStyle('doc', doc.doc_type)" class="text-xs">
                                {{ getTypeLabel('doc', doc.doc_type) }}
                            </Badge>
                        </div>

                        <!-- Middle: main content -->
                        <div class="min-w-0 flex-1">
                            <h3 class="truncate font-medium text-stone-700">
                                {{ doc.label }}
                            </h3>
                            <p v-if="doc.desc" class="mt-1 line-clamp-2 text-sm text-stone-500">
                                {{ doc.desc }}
                            </p>
                            <div class="flex flex-row items-end justify-between">
                                <div class="text-xs text-stone-400 mt-2">
                                    {{ doc.created_at ? new Date(doc.created_at).toLocaleString() : '' }}
                                </div>
                                <button class="text-stone-400 hover:text-stone-600" @click.stop="confirmDelete(doc.id)">
                                    <Trash class="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                </Card>
            </div>
        </main>

        <!-- Upload Modal -->
        <Modal v-model:open="uploadModalOpen">
            <h2 class="text-lg font-semibold text-stone-700">上传文档</h2>

            <div class="mt-6 space-y-4">
                <!-- File upload -->
                <div>
                    <label class="mb-2 block text-sm font-medium text-stone-600">
                        文件
                    </label>
                    <input ref="fileInputRef" type="file" accept=".pdf,.md,.txt" class="hidden"
                        @change="handleFileSelect" />
                    <div v-if="!uploadFile"
                        class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-stone-300 bg-stone-50 px-6 py-8 transition-colors hover:border-stone-400"
                        @click="openFileDialog">
                        <Upload class="h-8 w-8 text-stone-400" />
                        <p class="mt-2 text-sm text-stone-500">
                            点击选择文件或拖拽到此处
                        </p>
                        <p class="mt-1 text-xs text-stone-400">
                            支持 PDF、Markdown、TXT
                        </p>
                    </div>
                    <div v-else
                        class="flex items-center justify-between rounded-lg border border-stone-300 bg-stone-50 px-4 py-3">
                        <div class="flex items-center gap-2">
                            <FileText class="h-5 w-5 text-stone-500" />
                            <span class="text-sm text-stone-600">{{ uploadFile.name }}</span>
                        </div>
                        <button class="text-stone-400 hover:text-stone-600" @click="clearFile">
                            <X class="h-4 w-4" />
                        </button>
                    </div>
                </div>

                <div class="relative">
                    <div class="absolute inset-0 flex items-center">
                        <span class="w-full border-t border-stone-200" />
                    </div>
                    <div class="relative flex justify-center text-xs uppercase">
                        <span class="bg-white px-2 text-stone-400">或者</span>
                    </div>
                </div>

                <!-- Title -->
                <div>
                    <label class="mb-2 block text-sm font-medium text-stone-600">
                        标题
                    </label>
                    <Input v-model="uploadTitle" placeholder="文档标题" />
                </div>

                <!-- Content -->
                <div>
                    <label class="mb-2 block text-sm font-medium text-stone-600">
                        内容
                    </label>
                    <textarea v-model="uploadContent" placeholder="直接输入文本内容..." rows="4"
                        class="w-full rounded-lg border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400" />
                </div>

                <!-- Type -->
                <div>
                    <label class="mb-2 block text-sm font-medium text-stone-600">
                        类型
                    </label>
                    <div class="flex gap-2">
                        <button v-for="option in typeOptions" :key="option.value" :class="[
                            'rounded-lg border px-4 py-2 text-sm transition-colors',
                            uploadType === option.value
                                ? 'border-stone-600 bg-stone-600 text-white'
                                : 'border-stone-300 text-stone-600 hover:bg-stone-100',
                        ]" @click="uploadType = option.value">
                            {{ option.label }}
                        </button>
                    </div>
                </div>

                <!-- Error -->
                <div v-if="uploadError" class="text-sm text-red-500">
                    {{ uploadError }}
                </div>

                <!-- Actions -->
                <div class="flex justify-end gap-2 pt-4">
                    <Button variant="outline" @click="uploadModalOpen = false">
                        取消
                    </Button>
                    <Button @click="handleUpload" :disabled="uploading">
                        <Spinner v-if="uploading" size="sm" class="mr-2" />
                        上传
                    </Button>
                </div>
            </div>
        </Modal>
    </div>
</template>
