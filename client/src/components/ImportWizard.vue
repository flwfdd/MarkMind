<template>
    <Modal :open="show" @update:open="handleClose" class="max-w-4xl" :hide-close="true">
        <div class="import-wizard">
            <!-- Step 1: Input -->
            <div v-if="step === 1" class="step">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <svg class="h-6 w-6 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                        <h2 class="text-xl font-bold">导入文档 - 输入信息</h2>
                    </div>
                    <div class="flex gap-2">
                        <Button variant="secondary" @click="$emit('close')">取消</Button>
                        <Button @click="handleNext" :disabled="!formData.content || loading">{{ loading ? '处理中...' :
                            '下一步'
                        }}</Button>
                    </div>
                </div>

                <div class="grid gap-4 md:grid-cols-2">
                    <!-- Left column: Upload (top) and URL parse (bottom) -->
                    <div class="flex flex-col gap-4">
                        <Card
                            :class="dragging ? 'p-6 flex flex-col justify-center items-center text-center cursor-pointer border-stone-400 bg-stone-50' : 'p-6 flex flex-col justify-center items-center text-center cursor-pointer border-dashed hover:border-stone-400'"
                            @click="openFileDialog" @drop.prevent="handleDrop" @dragover.prevent="handleDragOver"
                            @dragleave.prevent="handleDragLeave">
                            <input ref="fileInput" type="file" class="hidden" @change="handleFileChange"
                                accept=".pdf,.txt,.md,.markdown,.html,.htm" />

                            <div class="flex flex-col items-center gap-3">
                                <div class="flex items-center justify-center h-14 w-14 rounded-full bg-stone-100">
                                    <svg class="h-6 w-6 text-stone-600" fill="none" viewBox="0 0 24 24"
                                        stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M12 4v16m8-8H4" />
                                    </svg>
                                </div>

                                <div class="text-sm text-stone-600">拖拽文件到此处，或点击选择文件</div>
                                <div class="text-xs text-stone-400">支持 PDF、Markdown、TXT、HTML</div>
                            </div>
                        </Card>

                        <!-- URL parse card (below upload) -->
                        <Card class="p-4 bg-stone-50 border border-stone-200">
                            <div>
                                <div class="text-sm font-medium text-stone-600 mb-2">网页链接解析</div>
                                <div class="flex gap-2">
                                    <Input v-model="url" placeholder="在此粘贴网页链接并点击解析" class="flex-1" />
                                    <Button @click="handleParseUrl" :disabled="!url || parsing">{{ parsing ? '解析中...' :
                                        '解析' }}</Button>
                                </div>
                                <div class="text-xs text-stone-400 mt-2">支持解析 HTML、PDF、小红书笔记
                                </div>
                            </div>
                        </Card>
                    </div>

                    <!-- Right: Manual fields -->
                    <Card class="p-4 flex flex-col gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-1">标题</label>
                            <Input v-model="formData.title" placeholder="文档标题" />
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1">类型</label>
                            <div class="flex gap-2">
                                <button
                                    v-for="opt in [{ value: 'text', label: '文本' }, { value: 'md', label: 'Markdown' }, { value: 'pdf', label: 'PDF' }, { value: 'xhs', label: '小红书' }]"
                                    :key="opt.value" :class="[
                                        'rounded-lg border px-4 py-2 text-sm transition-colors',
                                        formData.type === opt.value
                                            ? 'border-stone-600 bg-stone-600 text-white'
                                            : 'border-stone-300 text-stone-600 hover:bg-stone-100',
                                    ]" @click="formData.type = opt.value">
                                    {{ opt.label }}
                                </button>
                            </div>
                        </div>

                        <div>
                            <label class="block text-sm font-medium mb-1">链接</label>
                            <Input v-model="url" placeholder="可选：页面链接，将保存到文档的 url 字段" />
                            <div v-if="url && url.length > 0" class="text-xs text-stone-400 mt-1">已填写链接会在预览和最终导入时保存
                            </div>
                        </div>

                        <div class="flex-1">
                            <label class="block text-sm font-medium mb-1">内容 <span
                                    class="text-xs text-stone-400 ml-2">字数: {{ contentCharCount }} · 预计 tokens: {{
                                        contentTokenEstimate }}</span></label>
                            <Textarea v-model="formData.content" placeholder="输入或粘贴文档内容" :rows="10" class="h-48" />
                        </div>
                    </Card>
                </div>

                <div v-if="error" class="mt-4 p-3 bg-red-100 text-red-700 rounded">
                    {{ error }}
                </div>
            </div>

            <!-- Step 2: Preview -->
            <div v-if="step === 2 && preview" class="step">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-xl font-bold">导入文档 - 预览确认</h2>
                    <div class="flex gap-2">
                        <Button variant="secondary" @click="step = 1">返回</Button>
                        <Button variant="secondary" @click="$emit('close')">取消</Button>
                        <Button @click="handleConfirm" :disabled="loading">{{ loading ? '导入中...' : '确认导入' }}</Button>
                    </div>
                </div>

                <div class="grid gap-4 md:grid-cols-2 max-h-[70vh] overflow-y-auto">
                    <!-- Left: Document Info only -->
                    <div class="space-y-4">
                        <Card class="p-4 bg-stone-50 border border-stone-200 rounded-lg">
                            <div class="flex items-start justify-between">
                                <div>
                                    <div class="text-sm text-stone-500">标题</div>
                                    <Input v-model="preview.title" class="mt-2" />
                                </div>
                                <div class="text-xs text-stone-400">类型: {{ preview.type }}</div>
                            </div>

                            <div class="mt-4">
                                <div class="text-sm text-stone-500">摘要</div>
                                <Textarea v-model="preview.summary" :rows="3" class="w-full mt-2" />
                            </div>

                            <div class="mt-4">
                                <div class="text-sm text-stone-500">链接</div>
                                <Input v-model="preview.url" class="mt-2" />
                                <div class="text-xs text-stone-400 mt-2">页面链接将被保存到文档的 url 字段</div>
                            </div>

                            <div class="mt-4">
                                <div class="text-sm text-stone-500">内容预览 <span class="text-xs text-stone-400 ml-2">字数:
                                        {{ previewCharCount }} · 预计 tokens: {{ previewTokenEstimate }}</span></div>
                                <Textarea v-model="preview.content" :rows="6" class="w-full mt-2" />
                            </div>
                        </Card>
                    </div>

                    <!-- Right: Concepts & Relations -->
                    <div class="space-y-4">
                        <!-- Extracted Concepts Card -->
                        <Card class="p-4 bg-stone-50 border border-stone-200 rounded-lg">
                            <div class="flex items-center justify-between">
                                <div class="font-semibold">识别的概念 ({{ preview.concepts.length }})</div>
                                <Button @click="addConcept" variant="outline" size="sm">+ 添加</Button>
                            </div>

                            <div class="mt-3 space-y-2">
                                <div v-for="(concept, idx) in preview.concepts" :key="idx"
                                    class="p-3 rounded border border-stone-200 bg-white">
                                    <div class="flex items-center gap-2">
                                        <Input v-model="concept.name" class="flex-1 min-w-0 h-9 text-sm font-medium" />
                                        <Button variant="ghost" size="icon" @click="removeConcept(idx)">
                                            <X class="h-4 w-4 text-red-500" />
                                        </Button>
                                    </div>
                                    <Textarea v-model="concept.desc" :rows="2" class="w-full mt-2" />
                                </div>
                            </div>
                        </Card>

                        <!-- Existing Concepts Card (moved to right) -->
                        <Card>
                            <div class="font-semibold">匹配的现有概念 ({{ preview.existing_concepts.length }})</div>
                            <div class="mt-3 grid grid-cols-1 gap-2">
                                <div v-for="concept in preview.existing_concepts" :key="concept.id"
                                    class="p-3 rounded border border-stone-200 bg-white">
                                    <div class="font-medium">{{ concept.name }}</div>
                                    <div class="text-gray-600 text-xs mt-1">{{ concept.desc }}</div>
                                </div>
                            </div>
                        </Card>

                        <!-- Relations Card -->
                        <Card class="p-4 bg-stone-50 border border-stone-200 rounded-lg">
                            <div class="flex items-center justify-between">
                                <div class="font-semibold">概念关系 ({{ preview.relations.length }})</div>
                                <Button @click="addRelation" variant="outline" size="sm">+ 添加</Button>
                            </div>

                            <div class="mt-3 space-y-2">
                                <div v-for="(relation, idx) in preview.relations" :key="idx"
                                    class="p-3 rounded border border-stone-200 flex flex-wrap items-center gap-2">
                                    <Input v-model="relation.from_concept" class="flex-1 min-w-0 h-9 text-sm"
                                        placeholder="来源" />
                                    <span class="hidden md:block text-gray-500">→</span>
                                    <Input v-model="relation.to_concept" class="flex-1 min-w-0 h-9 text-sm"
                                        placeholder="目标" />
                                    <Input v-model="relation.desc" class="flex-[2_1_0%] min-w-0 h-9 text-sm"
                                        placeholder="关系描述" />
                                    <Button variant="ghost" size="icon" @click="removeRelation(idx)">
                                        <X class="h-4 w-4 text-red-500" />
                                    </Button>
                                </div>
                            </div>
                        </Card>
                    </div>
                </div>

                <div v-if="error" class="mt-4 p-3 bg-red-100 text-red-700 rounded">
                    {{ error }}
                </div>
            </div>

            <div v-if="loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
                <Spinner />
            </div>
        </div>
    </Modal>
</template>

<script setup lang="ts">
import { ref, computed, Text } from 'vue'
import Modal from './ui/Modal.vue'
import Card from './ui/Card.vue'
import Input from './ui/Input.vue'
import Textarea from './ui/Textarea.vue'
import Button from './ui/Button.vue'
import Spinner from './ui/Spinner.vue'
import { X } from 'lucide-vue-next'
import { parseDocument, previewDocument, confirmImport } from '@/api'
import type { DocumentPreview, ExtractedConcept, ExtractedRelation } from '@/types'

interface Props {
    show: boolean
}

defineProps<Props>()
const emit = defineEmits<{
    close: []
    success: []
}>()

const step = ref(1)
const fileInput = ref<HTMLInputElement | null>(null)
const dragging = ref(false)

function handleClose(value: boolean) {
    if (!value) {
        emit('close')
    }
}

function openFileDialog() {
    fileInput.value?.click()
}

function handleDragOver() {
    dragging.value = true
}

function handleDragLeave() {
    dragging.value = false
}

function handleDrop(e: DragEvent) {
    dragging.value = false
    const file = e.dataTransfer?.files?.[0]
    if (!file) return
    processFile(file)
}

const url = ref('')
const formData = ref({
    title: '',
    content: '',
    type: 'text',
})
const preview = ref<DocumentPreview | null>(null)
const loading = ref(false)
const parsing = ref(false)
const error = ref('')

// Content length / token estimates (language-aware JS estimator covering Chinese and English)
function estimateTokensJS(text: string): number {
    if (!text) return 0

    // Tokenization heuristic:
    // - Count each CJK character (Chinese/Japanese/Korean) as one token
    // - Count each ASCII alphanumeric run as ceil(len/4) tokens (approx subword splits)
    // - Count other non-space characters (punctuation, symbols) as one token
    // The regex splits into CJK single characters, ASCII words, or any non-space character
    const re = /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]|[A-Za-z0-9]+|[^\s]/gu
    const parts = text.match(re) || []
    let tokens = 0
    for (const p of parts) {
        if (/^[A-Za-z0-9]+$/.test(p)) {
            tokens += Math.max(1, Math.ceil(p.length / 4))
        } else {
            tokens += 1
        }
    }
    return tokens
}

const contentCharCount = computed(() => (formData.value.content ? formData.value.content.length : 0))
const contentTokenEstimate = computed(() => estimateTokensJS(formData.value.content || ''))

const previewCharCount = computed(() => (preview.value && preview.value.content ? preview.value.content.length : 0))
const previewTokenEstimate = computed(() => estimateTokensJS(preview.value?.content || ''))

async function handleParseUrl() {
    if (!url.value) return

    parsing.value = true
    error.value = ''

    try {
        const result = await parseDocument({ url: url.value })
        formData.value.title = result.title
        formData.value.content = result.content
        formData.value.type = result.type
    } catch (e) {
        error.value = `解析失败: ${e}`
    } finally {
        parsing.value = false
    }
}

async function processFile(file: File) {
    parsing.value = true
    error.value = ''

    try {
        const reader = new FileReader()
        reader.onload = async (e) => {
            const content = e.target?.result as string
            const base64 = content.split(',')[1]

            const result = await parseDocument({
                file_content: base64,
                file_name: file.name,
            })

            formData.value.title = result.title
            formData.value.content = result.content
            formData.value.type = result.type
            parsing.value = false
        }
        reader.readAsDataURL(file)
    } catch (e) {
        error.value = `文件处理失败: ${e}`
        parsing.value = false
    }
}

async function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return
    await processFile(file)
}



async function handleNext() {
    if (!formData.value.content) return

    loading.value = true
    error.value = ''

    try {
        preview.value = await previewDocument(
            formData.value.title,
            formData.value.content,
            formData.value.type,
            url.value || null,
        )
        step.value = 2
    } catch (e) {
        error.value = `预览生成失败: ${e}`
    } finally {
        loading.value = false
    }
}

async function handleConfirm() {
    if (!preview.value) return

    loading.value = true
    error.value = ''

    try {
        await confirmImport({
            title: preview.value.title,
            summary: preview.value.summary,
            content: preview.value.content,
            type: preview.value.type,
            url: preview.value.url || undefined,
            concepts: preview.value.concepts,
            relations: preview.value.relations,
        })
        emit('success')
        emit('close')
        resetForm()
    } catch (e) {
        error.value = `导入失败: ${e}`
    } finally {
        loading.value = false
    }
}

function addConcept() {
    if (preview.value) {
        preview.value.concepts.push({ name: '', desc: '' })
    }
}

function removeConcept(index: number) {
    if (preview.value) {
        preview.value.concepts.splice(index, 1)
    }
}

function addRelation() {
    if (preview.value) {
        preview.value.relations.push({ from_concept: '', to_concept: '', desc: '' })
    }
}

function removeRelation(index: number) {
    if (preview.value) {
        preview.value.relations.splice(index, 1)
    }
}



function resetForm() {
    step.value = 1
    url.value = ''
    formData.value = { title: '', content: '', type: 'text' }
    preview.value = null
    error.value = ''
}
</script>

<style scoped>
.import-wizard {
    position: relative;
    min-height: 400px;
}

.step {
    animation: fadeIn 0.3s;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}
</style>
