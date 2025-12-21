<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import Graph from 'graphology'
import Sigma from 'sigma'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import noverlap from 'graphology-layout-noverlap'
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
const isLayingOut = ref(false)

function randomAssign(graph: Graph) {
    // Simple random placement inside a box; keeps sizes small for FA2 to converge faster
    graph.forEachNode((n, attrs) => {
        graph.setNodeAttribute(n, 'x', (Math.random() - 0.5) * 20)
        graph.setNodeAttribute(n, 'y', (Math.random() - 0.5) * 20)
    })
}

/**
 * Apply layout pipeline: (optional) random -> forceAtlas2 -> noverlap
 * Uses the parameters you provided for better results on crowded graphs.
 */
async function applyLayout(applyRandom: boolean = false) {
    if (!graphInstance || !sigmaInstance) return
    if (isLayingOut.value) return
    isLayingOut.value = true

    try {
        // let UI update
        await new Promise((r) => setTimeout(r, 50))

        // Step 1 (optional): random layout
        if (applyRandom) {
            randomAssign(graphInstance)
        }

        // Step 2: ForceAtlas2
        ; (forceAtlas2 as any).assign(graphInstance, {
            iterations: 50,
            settings: {
                gravity: 1,
                scalingRatio: 5,
                strongGravityMode: false,
                barnesHutOptimize: true,
                barnesHutTheta: 0.5,
            },
        })

            // Step 3: noverlap to de-overlap nodes
            ; (noverlap as any).assign(graphInstance, {
                maxIterations: 50,
                settings: {
                    margin: 5,
                    ratio: 1.5,
                    speed: 1,
                },
            })

        sigmaInstance.refresh()
    } catch (e) {
        console.warn('applyLayout failed', e)
    } finally {
        isLayingOut.value = false
    }
}

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

        // Compute degree counts for sizing
        const degreeMap = new Map<string, number>()
        data.nodes.forEach((n) => degreeMap.set(n.id, 0))
        data.edges.forEach((e) => {
            if (degreeMap.has(e.source)) degreeMap.set(e.source, degreeMap.get(e.source)! + 1)
            if (degreeMap.has(e.target)) degreeMap.set(e.target, degreeMap.get(e.target)! + 1)
        })

        // Add nodes (size proportional to degree, and store originalSize)
        data.nodes.forEach((node, index) => {
            const angle = (2 * Math.PI * index) / data.nodes.length
            const radius = 5 + Math.random() * 3
            const color = getNodeColor(node)

            const degree = degreeMap.get(node.id) ?? 0
            // 缩小整体尺寸范围以避免节点与距离不协调
            const minSize = 4
            const maxSize = 12
            const scaleFactor = 3
            const baseSize = Math.min(maxSize, Math.max(minSize, Math.round(minSize + Math.log2(degree + 1) * scaleFactor)))
            // 概念节点相对更小一些
            const isConcept = node.type === 'concept' || (node as any).nodeType === 'concept' || (node as any).nodeType === 'Concept'
            const computedSize = isConcept ? Math.max(minSize, Math.round(baseSize * 0.55)) : baseSize

            graphInstance!.addNode(node.id, {
                x: Math.cos(angle) * radius + (Math.random() - 0.5) * 2,
                y: Math.sin(angle) * radius + (Math.random() - 0.5) * 2,
                size: computedSize,
                originalSize: computedSize,
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

            // Create new edge (store originalSize for hover revert)
            graphInstance!.addEdge(edge.source, edge.target, {
                size: 1.5,
                originalSize: 1.5,
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

        // Run initial layout pipeline: random -> forceAtlas2 -> noverlap
        await applyLayout(true)

        // Hover handling
        sigmaInstance.on('enterNode', ({ node }) => {
            hoveredNode.value = node
            highlightConnectedNodes(node)

            // Hide other, non-connected nodes/edges for focused inspection
            if (graphInstance) {
                const connected = new Set<string>([node])
                graphInstance.forEachEdge(node, (edge, attrs, s, t) => {
                    connected.add(s)
                    connected.add(t)
                })

                // Nodes: hide those not in connected set (but keep focused nodes visible)
                graphInstance.forEachNode((n, attrs) => {
                    if (!connected.has(n) && !attrs.focused) {
                        graphInstance!.setNodeAttribute(n, 'hoverHidden', true)
                        graphInstance!.setNodeAttribute(n, 'hidden', true)
                    } else {
                        // Ensure connected nodes are visible
                        graphInstance!.removeNodeAttribute(n, 'hoverHidden')
                        graphInstance!.setNodeAttribute(n, 'hidden', false)
                    }
                })

                // Edges: hide those not between connected nodes
                graphInstance.forEachEdge((e, attrs, s, t) => {
                    if (!connected.has(s) || !connected.has(t)) {
                        graphInstance!.setEdgeAttribute(e, 'hoverHidden', true)
                        graphInstance!.setEdgeAttribute(e, 'hidden', true)
                    } else {
                        graphInstance!.removeEdgeAttribute(e, 'hoverHidden')
                        graphInstance!.setEdgeAttribute(e, 'hidden', false)
                    }
                })

                if (sigmaInstance) sigmaInstance.refresh()
            }

            const nodeData = nodes.find((n) => n.id === node)
            if (nodeData) emit('nodeHover', nodeData)
        })

        sigmaInstance.on('leaveNode', () => {
            hoveredNode.value = null

            // Remove hover-based hiding
            if (graphInstance) {
                graphInstance.forEachNode((n, attrs) => {
                    if (attrs.hoverHidden) {
                        graphInstance!.removeNodeAttribute(n, 'hoverHidden')
                        graphInstance!.removeNodeAttribute(n, 'hidden')
                    }
                })
                graphInstance.forEachEdge((e, attrs) => {
                    if (attrs.hoverHidden) {
                        graphInstance!.removeEdgeAttribute(e, 'hoverHidden')
                        graphInstance!.removeEdgeAttribute(e, 'hidden')
                    }
                })
                if (sigmaInstance) sigmaInstance.refresh()
            }

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
        const isConn = connectedNodes.has(node)
        const baseSize = attrs.originalSize ?? attrs.size ?? 8
        // make center node more prominent but restrained
        const size = node === nodeId ? Math.round(baseSize * 1.2) : isConn ? Math.round(baseSize * 1.1) : Math.round(baseSize * 0.85)
        graphInstance!.setNodeAttribute(node, 'color', isConn ? attrs.originalColor : '#E8E4E0')
        graphInstance!.setNodeAttribute(node, 'size', size)
    })

    graphInstance.forEachEdge((edge, attrs) => {
        const isConnEdge = connectedEdges.has(edge)
        const edgeBase = attrs.originalSize ?? attrs.size ?? 1
        graphInstance!.setEdgeAttribute(edge, 'color', isConnEdge ? attrs.originalColor : '#F0EDEA')
        graphInstance!.setEdgeAttribute(edge, 'size', isConnEdge ? Math.max(edgeBase * 1.3, 0.8) : Math.max(edgeBase * 0.6, 0.4))
    })

    sigmaInstance.refresh()
}

function resetNodeStyles() {
    if (!graphInstance || !sigmaInstance) return

    graphInstance.forEachNode((node, attrs) => {
        graphInstance!.setNodeAttribute(node, 'color', attrs.originalColor)
        if (attrs.originalSize !== undefined) {
            graphInstance!.setNodeAttribute(node, 'size', attrs.originalSize)
        }
        // ensure highlight-related attrs removed
        graphInstance!.removeNodeAttribute(node, 'highlighted')
        graphInstance!.removeNodeAttribute(node, 'connected')
        // cleanup hover-based hiding if present
        if (attrs.hoverHidden) {
            graphInstance!.removeNodeAttribute(node, 'hoverHidden')
            graphInstance!.removeNodeAttribute(node, 'hidden')
        }
    })

    graphInstance.forEachEdge((edge, attrs) => {
        graphInstance!.setEdgeAttribute(edge, 'color', attrs.originalColor)
        if (attrs.originalSize !== undefined) {
            graphInstance!.setEdgeAttribute(edge, 'size', attrs.originalSize)
        }
        graphInstance!.removeEdgeAttribute(edge, 'highlighted')
        if (attrs.hoverHidden) {
            graphInstance!.removeEdgeAttribute(edge, 'hoverHidden')
            graphInstance!.removeEdgeAttribute(edge, 'hidden')
        }
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
            <div class="mt-2">
                <button @click="applyLayout(true)" :disabled="isLayingOut"
                    class="rounded bg-stone-100 px-2 py-1 text-xs text-stone-700 hover:bg-stone-50 disabled:opacity-50">
                    <span v-if="isLayingOut" class="inline-flex items-center gap-2">
                        优化中...
                    </span>
                    <span v-else>优化布局</span>
                </button>
            </div>
        </div>
    </div>
</template>
