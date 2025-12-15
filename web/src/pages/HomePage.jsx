import React, { useState, useRef, useEffect } from 'react';
import { Network, Send, Paperclip, X, Bot, User, Search } from 'lucide-react';
import { colors } from '../constants/theme';
import { TypingIndicator } from '../components/Common';

const HomePage = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: '你好！我是你的AI助手。你可以拖动左侧知识图谱中的节点到输入框，作为对话的上下文。',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [attachedNodes, setAttachedNodes] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [draggedNode, setDraggedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [scale, setScale] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [activeGraph, setActiveGraph] = useState('frontend');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const graphRef = useRef(null);

  // 知识图谱配置
  const knowledgeGraphs = {
    frontend: {
      name: '前端技术栈',
      color: '#7C8DB0',
      nodes: [
        { id: 1, title: 'React', x: 30, y: 30, description: 'React核心概念和最佳实践' },
        { id: 2, title: 'TypeScript', x: 60, y: 25, description: 'TypeScript类型系统详解' },
        { id: 3, title: '前端架构', x: 45, y: 55, description: '大型前端项目架构设计' },
        { id: 4, title: 'Node.js', x: 70, y: 60, description: 'Node.js后端开发' },
        { id: 5, title: '性能优化', x: 20, y: 65, description: 'Web性能优化技巧' },
        { id: 6, title: 'Vue.js', x: 15, y: 40, description: 'Vue框架核心原理' },
        { id: 7, title: 'Webpack', x: 35, y: 75, description: '模块打包工具配置' },
        { id: 8, title: 'CSS', x: 55, y: 15, description: 'CSS布局与动画' },
        { id: 9, title: 'HTTP', x: 80, y: 35, description: 'HTTP协议与网络通信' },
        { id: 10, title: 'Git', x: 25, y: 50, description: '版本控制与团队协作' },
        { id: 11, title: 'Docker', x: 75, y: 75, description: '容器化部署方案' },
        { id: 12, title: 'MongoDB', x: 65, y: 45, description: 'NoSQL数据库设计' },
        { id: 13, title: 'GraphQL', x: 85, y: 50, description: 'API查询语言' },
        { id: 14, title: 'Jest', x: 40, y: 20, description: '单元测试框架' },
        { id: 15, title: 'Redux', x: 50, y: 70, description: '状态管理方案' },
      ],
      connections: [
        { from: '30% 30%', to: '60% 25%' },
        { from: '30% 30%', to: '45% 55%' },
        { from: '60% 25%', to: '45% 55%' },
        { from: '45% 55%', to: '70% 60%' },
        { from: '45% 55%', to: '20% 65%' },
        { from: '30% 30%', to: '15% 40%' },
        { from: '20% 65%', to: '35% 75%' },
        { from: '60% 25%', to: '55% 15%' },
        { from: '60% 25%', to: '80% 35%' },
        { from: '45% 55%', to: '25% 50%' },
        { from: '70% 60%', to: '75% 75%' },
        { from: '70% 60%', to: '65% 45%' },
        { from: '65% 45%', to: '85% 50%' },
        { from: '55% 15%', to: '40% 20%' },
        { from: '30% 30%', to: '40% 20%' },
        { from: '45% 55%', to: '50% 70%' },
      ]
    },
    backend: {
      name: '后端技术栈',
      color: '#6B9D7E',
      nodes: [
        { id: 21, title: 'Java', x: 35, y: 25, description: 'Java企业级应用开发' },
        { id: 22, title: 'Spring Boot', x: 50, y: 45, description: 'Spring Boot框架' },
        { id: 23, title: 'MySQL', x: 68, y: 28, description: '关系型数据库' },
        { id: 24, title: 'Redis', x: 78, y: 55, description: '缓存与消息队列' },
        { id: 25, title: 'Kafka', x: 58, y: 72, description: '分布式消息系统' },
        { id: 26, title: 'Microservices', x: 28, y: 62, description: '微服务架构' },
        { id: 27, title: 'API设计', x: 42, y: 78, description: 'RESTful API设计' },
        { id: 28, title: 'Nginx', x: 82, y: 38, description: '反向代理与负载均衡' },
        { id: 29, title: 'Kubernetes', x: 72, y: 18, description: '容器编排平台' },
        { id: 30, title: 'PostgreSQL', x: 18, y: 45, description: '高级SQL数据库' },
        { id: 31, title: 'RabbitMQ', x: 62, y: 58, description: '消息中间件' },
        { id: 32, title: 'ElasticSearch', x: 48, y: 18, description: '分布式搜索引擎' },
      ],
      connections: [
        { from: '35% 25%', to: '50% 45%' },
        { from: '50% 45%', to: '68% 28%' },
        { from: '50% 45%', to: '78% 55%' },
        { from: '78% 55%', to: '58% 72%' },
        { from: '50% 45%', to: '28% 62%' },
        { from: '28% 62%', to: '42% 78%' },
        { from: '68% 28%', to: '82% 38%' },
        { from: '68% 28%', to: '72% 18%' },
        { from: '35% 25%', to: '18% 45%' },
        { from: '50% 45%', to: '62% 58%' },
        { from: '35% 25%', to: '48% 18%' },
        { from: '58% 72%', to: '62% 58%' },
      ]
    },
    ai: {
      name: 'AI与机器学习',
      color: '#C9956F',
      nodes: [
        { id: 41, title: 'Python', x: 38, y: 32, description: 'AI开发首选语言' },
        { id: 42, title: 'TensorFlow', x: 58, y: 22, description: '深度学习框架' },
        { id: 43, title: 'PyTorch', x: 72, y: 32, description: '深度学习框架' },
        { id: 44, title: 'NLP', x: 42, y: 55, description: '自然语言处理' },
        { id: 45, title: 'CV', x: 68, y: 55, description: '计算机视觉' },
        { id: 46, title: 'Transformer', x: 55, y: 72, description: 'Transformer架构' },
        { id: 47, title: 'LLM', x: 32, y: 72, description: '大语言模型' },
        { id: 48, title: 'Sklearn', x: 22, y: 52, description: '机器学习库' },
        { id: 49, title: 'Pandas', x: 28, y: 28, description: '数据分析库' },
        { id: 50, title: 'NumPy', x: 18, y: 42, description: '数值计算库' },
        { id: 51, title: 'Keras', x: 78, y: 45, description: '高级神经网络API' },
        { id: 52, title: 'OpenAI API', x: 48, y: 85, description: 'OpenAI接口' },
      ],
      connections: [
        { from: '38% 32%', to: '58% 22%' },
        { from: '38% 32%', to: '72% 32%' },
        { from: '58% 22%', to: '42% 55%' },
        { from: '72% 32%', to: '68% 55%' },
        { from: '42% 55%', to: '55% 72%' },
        { from: '68% 55%', to: '55% 72%' },
        { from: '55% 72%', to: '32% 72%' },
        { from: '38% 32%', to: '22% 52%' },
        { from: '38% 32%', to: '28% 28%' },
        { from: '28% 28%', to: '18% 42%' },
        { from: '72% 32%', to: '78% 45%' },
        { from: '32% 72%', to: '48% 85%' },
        { from: '55% 72%', to: '48% 85%' },
      ]
    },
    design: {
      name: '设计系统',
      color: '#B08DA6',
      nodes: [
        { id: 61, title: 'Figma', x: 38, y: 28, description: 'UI设计工具' },
        { id: 62, title: '设计规范', x: 62, y: 28, description: 'Design System' },
        { id: 63, title: '组件库', x: 50, y: 48, description: 'Component Library' },
        { id: 64, title: '用户体验', x: 28, y: 58, description: 'UX设计原则' },
        { id: 65, title: '交互设计', x: 72, y: 58, description: 'Interaction Design' },
        { id: 66, title: '视觉设计', x: 50, y: 72, description: 'Visual Design' },
        { id: 67, title: '响应式', x: 32, y: 78, description: '响应式设计' },
        { id: 68, title: '原型设计', x: 22, y: 42, description: 'Prototyping' },
        { id: 69, title: '设计Token', x: 78, y: 42, description: 'Design Tokens' },
        { id: 70, title: '无障碍', x: 68, y: 72, description: 'Accessibility' },
      ],
      connections: [
        { from: '38% 28%', to: '62% 28%' },
        { from: '62% 28%', to: '50% 48%' },
        { from: '38% 28%', to: '50% 48%' },
        { from: '50% 48%', to: '28% 58%' },
        { from: '50% 48%', to: '72% 58%' },
        { from: '50% 48%', to: '50% 72%' },
        { from: '28% 58%', to: '32% 78%' },
        { from: '38% 28%', to: '22% 42%' },
        { from: '62% 28%', to: '78% 42%' },
        { from: '72% 58%', to: '68% 72%' },
      ]
    }
  };

  // 当前选中的知识图谱
  const currentGraph = knowledgeGraphs[activeGraph];
  const knowledgeNodes = currentGraph.nodes;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: inputValue,
      attachments: [...attachedNodes],
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages([...messages, userMessage]);
    setInputValue('');
    setAttachedNodes([]);
    setIsTyping(true);

    // 模拟AI回复
    setTimeout(() => {
      const responses = [
        '根据你提供的知识节点，我为你整理了相关内容...',
        '基于这些主题，让我给你一些建议和总结...',
        '我已经分析了你附加的知识点，这里是详细说明...',
        '结合你的问题和选择的知识节点，我的理解是...',
      ];

      const botMessage = {
        id: Date.now(),
        type: 'bot',
        text: responses[Math.floor(Math.random() * responses.length)],
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDragStart = (node) => {
    setDraggedNode(node);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (draggedNode && !attachedNodes.find(n => n.id === draggedNode.id)) {
      setAttachedNodes([...attachedNodes, draggedNode]);
    }
    setDraggedNode(null);
  };

  const removeAttachment = (nodeId) => {
    setAttachedNodes(attachedNodes.filter(n => n.id !== nodeId));
  };

  // 缩放控制
  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY * -0.001;
    setScale(prev => Math.min(Math.max(prev + delta, 0.5), 3));
  };

  // 平移控制
  const handleMouseDown = (e) => {
    // 只有在点击背景区域（不是节点）时才启动平移
    const isNode = e.target.closest('.knowledge-node');
    if (!isNode) {
      e.preventDefault();
      setIsPanning(true);
      setStartPan({
        x: e.clientX - panOffset.x,
        y: e.clientY - panOffset.y
      });
    }
  };

  const handleMouseMove = (e) => {
    if (isPanning) {
      e.preventDefault();
      setPanOffset({
        x: e.clientX - startPan.x,
        y: e.clientY - startPan.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  // 重置视图
  const handleResetView = () => {
    setScale(1);
    setPanOffset({ x: 0, y: 0 });
  };

  // 检查节点是否匹配搜索
  const isNodeMatched = (node) => {
    if (!searchTerm) return true;
    return node.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
           node.description.toLowerCase().includes(searchTerm.toLowerCase());
  };

  // 统计匹配的节点数量
  const matchedCount = searchTerm 
    ? knowledgeNodes.filter(node => isNodeMatched(node)).length 
    : knowledgeNodes.length;

  return (
    <div className="h-full flex gap-6 p-6" style={{ backgroundColor: colors.background }}>
      {/* 左侧：知识图谱 */}
      <div className="w-1/2 bg-white rounded-xl border p-6 flex flex-col" style={{ borderColor: colors.border }}>
        <div className="flex items-center space-x-2 mb-4">
          <div className="p-2 rounded-lg" style={{ backgroundColor: colors.primaryLight }}>
            <Network className="w-5 h-5" style={{ color: colors.primaryDark }} />
          </div>
          <h2 className="text-lg font-semibold" style={{ color: colors.textPrimary }}>知识图谱</h2>
        </div>
        
        {/* 图谱切换菜单 */}
        <div className="mb-4 flex space-x-2 pb-3 border-b" style={{ borderColor: colors.border }}>
          {Object.entries(knowledgeGraphs).map(([key, graph]) => (
            <button
              key={key}
              onClick={() => {
                setActiveGraph(key);
                setSearchTerm('');
                setScale(1);
                setPanOffset({ x: 0, y: 0 });
              }}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                backgroundColor: activeGraph === key ? graph.color : 'transparent',
                color: activeGraph === key ? colors.white : colors.textSecondary,
                border: activeGraph === key ? 'none' : `1px solid ${colors.border}`
              }}
            >
              {graph.name}
            </button>
          ))}
        </div>
        
        {/* 搜索栏 */}
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" style={{ color: colors.textTertiary }} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="搜索知识节点..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg outline-none focus:border-2 transition-all"
              style={{ 
                borderColor: searchTerm ? colors.primary : colors.border,
                color: colors.textPrimary
              }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 hover:opacity-70"
              >
                <X className="w-4 h-4" style={{ color: colors.textTertiary }} />
              </button>
            )}
          </div>
          {searchTerm && (
            <p className="text-xs mt-2 px-1" style={{ color: colors.textSecondary }}>
              找到 {matchedCount} 个相关节点
            </p>
          )}
        </div>
        
        <div 
          ref={graphRef}
          className="relative rounded-lg flex-1 overflow-hidden" 
          style={{ 
            backgroundColor: colors.borderHover,
            cursor: isPanning ? 'grabbing' : 'grab'
          }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {/* 内容容器 - 支持缩放和平移 */}
          <div 
            className="absolute inset-0 transition-transform duration-200"
            style={{ 
              transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${scale})`,
              transformOrigin: 'center'
            }}
          >
          {/* 图谱节点 */}
          {knowledgeNodes.map((node) => {
            const matched = isNodeMatched(node);
            return (
            <div
              key={node.id}
              draggable
              onDragStart={() => handleDragStart(node)}
              className="knowledge-node absolute transform -translate-x-1/2 -translate-y-1/2 cursor-move group/node transition-opacity duration-300"
              style={{ 
                left: `${node.x}%`, 
                top: `${node.y}%`,
                opacity: !searchTerm || matched ? 1 : 0.3
              }}
              title={node.description}
            >
              <div 
                className="bg-white border-2 rounded-full px-4 py-2 hover:scale-110 transition-all duration-200" 
                style={{ 
                  borderColor: matched && searchTerm ? '#6B9D7E' : currentGraph.color,
                  boxShadow: matched && searchTerm ? '0 0 0 3px rgba(107, 157, 126, 0.2)' : 'none'
                }}
              >
                <span 
                  className="text-sm font-semibold" 
                  style={{ 
                    color: matched && searchTerm ? '#6B9D7E' : currentGraph.color
                  }}
                >
                  {node.title}
                </span>
              </div>
              {/* 悬停提示 */}
              <div className="absolute hidden group-hover/node:block bg-white rounded px-3 py-2 mt-2 whitespace-nowrap z-10 border text-xs" style={{ color: colors.textPrimary, borderColor: colors.border }}>
                <p className="font-medium mb-1">{node.title}</p>
                <p style={{ color: colors.textSecondary }}>{node.description}</p>
                <p className="mt-1 text-xs" style={{ color: colors.textTertiary }}>拖动到右侧作为对话上下文</p>
              </div>
            </div>
            );
          })}
          
          {/* 连接线 */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ opacity: searchTerm ? 0.3 : 1, transition: 'opacity 300ms' }}>
            {currentGraph.connections.map((conn, idx) => {
              const [x1, y1] = conn.from.split(' ');
              const [x2, y2] = conn.to.split(' ');
              return (
                <line 
                  key={idx}
                  x1={x1} 
                  y1={y1} 
                  x2={x2} 
                  y2={y2} 
                  stroke={currentGraph.color} 
                  strokeWidth="2" 
                  opacity="0.3" 
                />
              );
            })}
          </svg>
          </div>

          {/* 提示文字 - 固定在左下角 */}
          <div className="absolute bottom-4 left-4 bg-white rounded-lg px-3 py-2 text-sm border pointer-events-none z-10" style={{ color: colors.textSecondary, borderColor: colors.border }}>
            <p className="flex items-center space-x-1">
              <span>💡</span>
              <span>拖动节点到右侧对话框 | 按住鼠标平移视图</span>
            </p>
          </div>

          {/* 缩放控制按钮 */}
          <div className="absolute bottom-4 right-4 flex flex-col space-y-2">
            <button
              onClick={handleZoomIn}
              className="w-10 h-10 bg-white rounded-lg border flex items-center justify-center hover:bg-gray-50 transition-colors"
              style={{ borderColor: colors.border }}
              title="放大"
            >
              <span className="text-xl font-semibold" style={{ color: colors.primaryDark }}>+</span>
            </button>
            <button
              onClick={handleZoomOut}
              className="w-10 h-10 bg-white rounded-lg border flex items-center justify-center hover:bg-gray-50 transition-colors"
              style={{ borderColor: colors.border }}
              title="缩小"
            >
              <span className="text-xl font-semibold" style={{ color: colors.primaryDark }}>−</span>
            </button>
            <button
              onClick={handleResetView}
              className="w-10 h-10 bg-white rounded-lg border flex items-center justify-center hover:bg-gray-50 transition-colors"
              style={{ borderColor: colors.border }}
              title="重置视图"
            >
              <span className="text-sm font-semibold" style={{ color: colors.primaryDark }}>⟲</span>
            </button>
            <div className="text-xs text-center bg-white rounded px-2 py-1 border" style={{ borderColor: colors.border, color: colors.textSecondary }}>
              {Math.round(scale * 100)}%
            </div>
          </div>

          {/* 无搜索结果提示 */}
          {searchTerm && matchedCount === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <Search className="w-12 h-12 mx-auto mb-2" style={{ color: colors.textTertiary }} />
                <p className="text-sm" style={{ color: colors.textSecondary }}>未找到匹配的知识节点</p>
                <p className="text-xs mt-1" style={{ color: colors.textTertiary }}>尝试使用其他关键词搜索</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 右侧：问答系统 */}
      <div className="w-1/2 flex flex-col bg-white rounded-xl border" style={{ borderColor: colors.border }}>
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start space-x-3 ${
                message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}
            >
              {/* 头像 */}
              <div
                className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-white"
                style={{ backgroundColor: message.type === 'bot' ? colors.primary : colors.green }}
              >
                {message.type === 'bot' ? (
                  <Bot className="w-5 h-5" />
                ) : (
                  <User className="w-5 h-5" />
                )}
              </div>

              {/* 消息内容 */}
              <div className={`max-w-[70%] ${message.type === 'user' ? 'items-end' : 'items-start'}`}>
                {/* 附件显示 */}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mb-2 flex flex-wrap gap-2">
                    {message.attachments.map((node) => (
                      <div
                        key={node.id}
                        className="px-3 py-1 rounded-full text-xs font-medium border"
                        style={{ backgroundColor: colors.primaryLight, borderColor: colors.primary, color: colors.primaryDark }}
                      >
                        <Paperclip className="w-3 h-3 inline mr-1" />
                        {node.title}
                      </div>
                    ))}
                  </div>
                )}
                
                <div
                  className="px-4 py-3 rounded-2xl"
                  style={message.type === 'bot' ? {
                    backgroundColor: colors.white,
                    border: `1px solid ${colors.border}`,
                    color: colors.textPrimary
                  } : {
                    backgroundColor: colors.primary,
                    color: colors.white
                  }}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
                </div>
                <span className="text-xs mt-1 px-2" style={{ color: colors.textTertiary }}>{message.time}</span>
              </div>
            </div>
          ))}

          {/* AI正在输入 */}
          {isTyping && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-white" style={{ backgroundColor: colors.primary }}>
                <Bot className="w-5 h-5" />
              </div>
              <div className="bg-white border px-4 py-3 rounded-2xl" style={{ borderColor: colors.border }}>
                <TypingIndicator color={colors.primary} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div 
          className="border-t p-4"
          style={{ borderColor: colors.border }}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {/* 已附加的节点 */}
          {attachedNodes.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedNodes.map((node) => (
                <div
                  key={node.id}
                  className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm border"
                  style={{ backgroundColor: colors.primaryLight, borderColor: colors.primary, color: colors.primaryDark }}
                >
                  <Paperclip className="w-3 h-3" />
                  <span>{node.title}</span>
                  <button
                    onClick={() => removeAttachment(node.id)}
                    className="hover:opacity-70"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-end space-x-3">
            <div className="flex-1 bg-white border rounded-xl px-4 py-3 focus-within:border transition-all" style={{ borderColor: colors.border }}>
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="请输入您的问题，或拖动左侧节点到此处..."
                className="w-full bg-transparent border-none outline-none resize-none"
                style={{ color: colors.textPrimary, minHeight: '24px', maxHeight: '120px' }}
                rows="1"
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isTyping}
              className="flex-shrink-0 w-12 h-12 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center"
              style={{ backgroundColor: colors.primary }}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
