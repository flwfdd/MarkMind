<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
    class?: string
    placeholder?: string
    modelValue?: string
    rows?: number
    disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
    rows: 4,
    disabled: false,
})

const emit = defineEmits<{
    'update:modelValue': [value: string]
}>()
</script>

<template>
    <textarea :rows="props.rows" :class="cn(
        'w-full rounded-lg border border-stone-300 bg-stone-50 px-3 py-2 text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400 disabled:cursor-not-allowed disabled:opacity-50',
        props.class,
    )" :placeholder="props.placeholder" :value="props.modelValue" :disabled="props.disabled"
        @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)" />
</template>
