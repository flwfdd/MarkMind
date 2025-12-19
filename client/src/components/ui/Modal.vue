<script setup lang="ts">
import { ref, watch } from 'vue'
import { cn } from '@/lib/utils'
import { X } from 'lucide-vue-next'
import Button from './Button.vue'

interface Props {
    open: boolean
    class?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
    'update:open': [value: boolean]
}>()

const isVisible = ref(props.open)

watch(
    () => props.open,
    (val) => {
        isVisible.value = val
    },
)

function close() {
    emit('update:open', false)
}

function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
        close()
    }
}
</script>

<template>
    <Teleport to="body">
        <Transition name="modal">
            <div v-if="isVisible" class="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40"
                @click="handleBackdropClick">
                <div :class="cn(
                    'relative max-h-[85vh] w-full max-w-2xl overflow-auto rounded-xl border border-stone-200 bg-white p-6',
                    props.class,
                )
                    ">
                    <Button variant="ghost" size="icon" class="absolute right-4 top-4" @click="close">
                        <X class="h-4 w-4" />
                    </Button>
                    <slot />
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
</style>
