<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
    variant?: 'default' | 'secondary' | 'ghost' | 'outline'
    size?: 'default' | 'sm' | 'lg' | 'icon'
    class?: string
    disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
    variant: 'default',
    size: 'default',
    disabled: false,
})

const variantClasses = {
    default: 'bg-stone-600 text-stone-50 hover:bg-stone-500',
    secondary: 'bg-stone-200 text-stone-700 hover:bg-stone-300',
    ghost: 'hover:bg-stone-100 text-stone-600',
    outline: 'border border-stone-300 text-stone-600 hover:bg-stone-100',
}

const sizeClasses = {
    default: 'h-10 px-4 py-2',
    sm: 'h-8 px-3 text-sm',
    lg: 'h-12 px-6',
    icon: 'h-10 w-10',
}
</script>

<template>
    <button :class="cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 disabled:pointer-events-none disabled:opacity-50',
        variantClasses[props.variant],
        sizeClasses[props.size],
        props.class,
    )
        " :disabled="props.disabled">
        <slot />
    </button>
</template>
