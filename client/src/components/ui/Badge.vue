<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
    class?: string
}

const props = defineProps<Props>()
</script>

<template>
    <span :class="cn(
        'inline-flex items-center rounded-full bg-stone-200 px-2.5 py-0.5 text-xs font-medium text-stone-600',
        props.class,
    )
        ">
        <slot />
    </span>
</template>
