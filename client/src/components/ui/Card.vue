<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
    class?: string
}

const props = defineProps<Props>()
</script>

<template>
    <div :class="cn('rounded-xl border border-stone-200 bg-stone-50 p-4', props.class)">
        <slot />
    </div>
</template>
