// Centralized type labels and color mappings for nodes
export const docColors: Record<string, string> = {
    pdf: '#A7D8F0', // pastel blue
    md: '#C6F6D5', // pastel mint
    xhs: '#FFD1DD', // pastel pink
    text: '#E6D8FF', // pastel lavender
    default: '#F0E8D8', // soft cream
}
export const conceptColor = '#FFE5B4' // pastel peach

export function getTypeColor(type: string, docType?: string | null): string {
    if (type === 'doc') {
        const dcolors: Record<string, string> = {
            pdf: docColors.pdf || "",
            md: docColors.md || "",
            xhs: docColors.xhs || "",
            text: docColors.text || "",
        }
        return dcolors[docType || 'text'] || docColors.default || ""
    }
    const colors: Record<string, string> = {
        concept: conceptColor,
    }
    return colors[type] || docColors.default || ""
}

export function getTypeLabel(type: string, docType?: string | null): string {
    if (type === 'doc') {
        const dlabels: Record<string, string> = {
            pdf: 'PDF',
            md: 'Markdown',
            xhs: '小红书',
            text: '文本',
        }
        return dlabels[docType || 'text'] || '文档'
    }
    const labels: Record<string, string> = {
        concept: '概念',
    }
    return labels[type] || type
}

export function getNodeColor(node: any): string {
    if (node && node.type === 'doc') {
        return getTypeColor('doc', node.doc_type)
    }
    return conceptColor
}

export function getBadgeStyle(type: string, docType?: string | null) {
    return { backgroundColor: getTypeColor(type, docType), color: '#3b3b3b' }
}
