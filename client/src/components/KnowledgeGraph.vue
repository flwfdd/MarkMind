<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import Graph from 'graphology'
import Sigma from 'sigma'
import type { GraphNode, GraphEdge } from '@/types'
import { getGraphOverview } from '@/api'
import Spinner from '@/components/ui/Spinner.vue'
import { getNodeColor, docColors, conceptColor } from '@/lib/nodeTypes'

interface Props {
    highlightNodeId?: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
    nodeClick: [node: GraphNode]
    nodeHover: [node: GraphNode | null]
}>()

// Highlight node when parent passes a highlightNodeId (e.g., from search hover)
watch(
    () => props.highlightNodeId,
    (id) => {
        if (!id) {
            resetNodeStyles()
            return
        }
        if (graphInstance && graphInstance.hasNode(id)) {
            highlightConnectedNodes(id)
        }
    },
)

const containerRef = ref<HTMLElement>()
const loading = ref(true)
const error = ref<string | null>(null)

let sigmaInstance: Sigma | null = null
let graphInstance: Graph | null = null
let nodes: GraphNode[] = []

const hoveredNode = ref<string | null>(null)

const edgeColors: Record<string, string> = {
    mentions: '#F5D9BA',
    related: '#CAEBE3',
    default: '#AAAAAA',
}

function getEdgeColor(type: string): string {
    return edgeColors[type] ?? edgeColors.default!
}

async function loadGraph() {
    loading.value = true
    error.value = null

    try {
        const data = await getGraphOverview()
        nodes = data.nodes

        if (!containerRef.value) return

        // Create graphology instance
        graphInstance = new Graph()

        // Add nodes
        data.nodes.forEach((node, index) => {
            const angle = (2 * Math.PI * index) / data.nodes.length
            const radius = 5 + Math.random() * 3
            const color = getNodeColor(node)
            graphInstance!.addNode(node.id, {
                x: Math.cos(angle) * radius + (Math.random() - 0.5) * 2,
                y: Math.sin(angle) * radius + (Math.random() - 0.5) * 2,
                size: node.type === 'doc' ? 12 : 10,
                label: node.label,
                color,
                nodeType: node.type,
                docType: node.doc_type || null,
                originalColor: color,
            })
        })

        // Add edges (skip duplicates; if an edge exists update its attributes)
        data.edges.forEach((edge, index) => {
            if (!graphInstance!.hasNode(edge.source) || !graphInstance!.hasNode(edge.target)) return

            // If an edge already exists between these nodes, update its attrs
            try {
                // Try to get the existing edge key for simple graphs
                const existingKey = graphInstance!.edge(edge.source, edge.target)
                if (existingKey && graphInstance!.hasEdge(existingKey)) {
                    graphInstance!.setEdgeAttribute(existingKey, 'edgeType', edge.type)
                    graphInstance!.setEdgeAttribute(existingKey, 'color', getEdgeColor(edge.type))
                    graphInstance!.setEdgeAttribute(existingKey, 'originalColor', getEdgeColor(edge.type))
                    return
                }
            } catch (e) {
                // Some graphology implementations may throw (e.g., multigraph) — fallback to scanning edges
                let foundKey: string | null = null
                graphInstance!.forEachEdge((ek, attrs, s, t) => {
                    if ((s === edge.source && t === edge.target) || (s === edge.target && t === edge.source)) {
                        foundKey = ek
                    }
                })
                if (foundKey && graphInstance!.hasEdge(foundKey)) {
                    graphInstance!.setEdgeAttribute(foundKey, 'edgeType', edge.type)
                    graphInstance!.setEdgeAttribute(foundKey, 'color', getEdgeColor(edge.type))
                    graphInstance!.setEdgeAttribute(foundKey, 'originalColor', getEdgeColor(edge.type))
                    return
                }
            }

            // Create new edge
            graphInstance!.addEdge(edge.source, edge.target, {
                size: 1.5,
                color: getEdgeColor(edge.type),
                edgeType: edge.type,
                originalColor: getEdgeColor(edge.type),
            })
        })

        // Create sigma instance
        sigmaInstance = new Sigma(graphInstance, containerRef.value, {
            renderLabels: true,
            labelRenderedSizeThreshold: 6,
            labelFont: 'Inter, system-ui, sans-serif',
            labelSize: 12,
            labelColor: { color: '#57534e' },
            defaultEdgeType: 'line',
            stagePadding: 50,
        })

        // Hover handling
        sigmaInstance.on('enterNode', ({ node }) => {
            hoveredNode.value = node
            highlightConnectedNodes(node)
            const nodeData = nodes.find((n) => n.id === node)
            if (nodeData) emit('nodeHover', nodeData)
        })

        sigmaInstance.on('leaveNode', () => {
            hoveredNode.value = null
            resetNodeStyles()
            emit('nodeHover', null)
        })

        // Click handling
        sigmaInstance.on('clickNode', ({ node }) => {
            const nodeData = nodes.find((n) => n.id === node)
            if (nodeData) emit('nodeClick', nodeData)
        })

        // Removed drag-to-chat handling (replaced by explicit 'add to context' action in node detail modal)

    } catch (e) {
        error.value = e instanceof Error ? e.message : 'Failed to load graph'
    } finally {
        loading.value = false
    }
}

function highlightConnectedNodes(nodeId: string) {
    if (!graphInstance || !sigmaInstance) return

    const connectedNodes = new Set([nodeId])
    const connectedEdges = new Set<string>()

    graphInstance.forEachEdge(nodeId, (edge, attrs, source, target) => {
        connectedNodes.add(source)
        connectedNodes.add(target)
        connectedEdges.add(edge)
    })

    graphInstance.forEachNode((node, attrs) => {
        graphInstance!.setNodeAttribute(
            node,
            'color',
            connectedNodes.has(node) ? attrs.originalColor : '#E8E4E0',
        )
    })

    graphInstance.forEachEdge((edge, attrs) => {
        graphInstance!.setEdgeAttribute(
            edge,
            'color',
            connectedEdges.has(edge) ? attrs.originalColor : '#F0EDEA',
        )
    })

    sigmaInstance.refresh()
}

function resetNodeStyles() {
    if (!graphInstance || !sigmaInstance) return

    graphInstance.forEachNode((node, attrs) => {
        graphInstance!.setNodeAttribute(node, 'color', attrs.originalColor)
    })

    graphInstance.forEachEdge((edge, attrs) => {
        graphInstance!.setEdgeAttribute(edge, 'color', attrs.originalColor)
    })

    sigmaInstance.refresh()
}

onMounted(() => {
    loadGraph()
})

onUnmounted(() => {
    if (sigmaInstance) {
        sigmaInstance.kill()
        sigmaInstance = null
    }
})

// Expose refresh method
defineExpose({
    refresh: loadGraph,
})
</script>

<template>
    <div class="relative h-full w-full overflow-hidden rounded-xl bg-stone-100">
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
            <Spinner size="lg" />
        </div>

        <div v-else-if="error" class="absolute inset-0 flex items-center justify-center text-stone-500">
            {{ error }}
        </div>

        <div ref="containerRef" class="h-full w-full" />

        <!-- Legend -->
        <div class="absolute bottom-4 left-4 flex flex-col gap-2 rounded-lg bg-white/80 p-3">
            <div class="flex items-center gap-2 text-xs text-stone-600">
                <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: docColors.pdf }" />
                <span>PDF</span>
            </div>
            <div class="flex items-center gap-2 text-xs text-stone-600">
                <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: docColors.md }" />
                <span>Markdown</span>
            </div>
            <div class="flex items-center gap-2 text-xs text-stone-600">
                <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: docColors.xhs }" />
                <span>小红书</span>
            </div>
            <div class="flex items-center gap-2 text-xs text-stone-600">
                <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: docColors.text }" />
                <span>文本</span>
            </div>
            <div class="flex items-center gap-2 text-xs text-stone-600">
                <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: conceptColor }" />
                <span>概念</span>
            </div>
        </div>
    </div>
</template>
