import React, { useState } from 'react';
import { FileText, Clock, Lightbulb, CheckSquare } from 'lucide-react';
import { colors } from '../constants/theme';
import { Card, IconBox, ListItem } from '../components/Common';

const LearningAssistant = () => {
  const [todos, setTodos] = useState([
    { id: 1, text: '完成项目文档整理', completed: false },
    { id: 2, text: '回顾上周学习笔记', completed: false },
    { id: 3, text: '准备周会分享内容', completed: false },
    { id: 4, text: '更新知识图谱', completed: false },
  ]);

  const reviewReports = [
    { title: 'React 进阶学习笔记', date: '2025-12-10', views: 5 },
    { title: 'TypeScript 类型系统深度解析', date: '2025-12-08', views: 3 },
    { title: '前端性能优化实践', date: '2025-12-05', views: 8 },
  ];

  const dustCollections = [
    { title: 'Python 数据分析教程', lastView: '2025-10-15', daysAgo: 60 },
    { title: 'Docker 容器化实践', lastView: '2025-09-20', daysAgo: 85 },
    { title: 'Kubernetes 入门指南', lastView: '2025-08-30', daysAgo: 106 },
  ];

  const inspirations = [
    '真正的知识不在于知道答案，而在于提出正确的问题。',
    '学习的本质是将知识内化，而不是简单的记忆。',
    '知识管理的核心是建立知识之间的联系。',
    '持续学习和定期复盘是成长的关键。',
    '最好的学习方式是教会别人。',
  ];

  const randomInspiration = inspirations[Math.floor(Math.random() * inspirations.length)];

  const toggleTodo = (id) => {
    setTodos(todos.map(todo => 
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  return (
    <div className="h-full overflow-y-auto p-6" style={{ backgroundColor: colors.background }}>
      {/* 页面标题 */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2" style={{ color: colors.textPrimary }}>学习助手</h1>
        <p className="text-sm" style={{ color: colors.textSecondary }}>智能管理你的学习进程</p>
      </div>

      {/* 2x2 网格布局 */}
      <div className="grid grid-cols-2 gap-6 h-[calc(100%-5rem)]">
        {/* 左上：收藏回顾报告 */}
        <Card className="flex flex-col overflow-hidden">
          {/* 固定标题 */}
          <div className="flex items-center space-x-3 p-6 pb-4 border-b" style={{ borderColor: colors.border }}>
            <IconBox icon={FileText} color={colors.greenLight} iconColor={colors.green} />
            <div>
              <h2 className="text-xl font-bold" style={{ color: colors.textPrimary }}>收藏回顾报告</h2>
              <p className="text-xs" style={{ color: colors.textSecondary }}>查看你最近收藏和阅读的文档</p>
            </div>
          </div>
          {/* 可滚动内容 */}
          <div className="flex-1 overflow-y-auto p-6 pt-4">
            <div className="space-y-3">
              {reviewReports.map((report, index) => (
                <ListItem
                  key={index}
                  icon={FileText}
                  iconBg={colors.greenLight}
                  iconColor={colors.green}
                  title={report.title}
                  meta={
                    <>
                      <span>收藏于：{report.date}</span>
                      <span>已阅读 {report.views} 次</span>
                    </>
                  }
                />
              ))}
            </div>
          </div>
        </Card>

        {/* 右上：吃灰收藏名单 */}
        <Card className="flex flex-col overflow-hidden">
          {/* 固定标题 */}
          <div className="flex items-center space-x-3 p-6 pb-4 border-b" style={{ borderColor: colors.border }}>
            <IconBox icon={Clock} color={colors.orangeLight} iconColor={colors.orange} />
            <div>
              <h2 className="text-xl font-bold" style={{ color: colors.textPrimary }}>吃灰收藏名单</h2>
              <p className="text-xs" style={{ color: colors.textSecondary }}>这些文档已经很久没有阅读了</p>
            </div>
          </div>
          {/* 可滚动内容 */}
          <div className="flex-1 overflow-y-auto p-6 pt-4">
            <div className="space-y-3">
              {dustCollections.map((item, index) => (
                <ListItem
                  key={index}
                  icon={Clock}
                  iconBg={colors.orangeLight}
                  iconColor={colors.orange}
                  title={item.title}
                  meta={
                    <>
                      <span>最后阅读：{item.lastView}</span>
                      <span className="font-medium px-2 py-0.5 rounded-full text-xs" style={{ backgroundColor: colors.orangeLight, color: colors.orange }}>
                        已闲置 {item.daysAgo} 天
                      </span>
                    </>
                  }
                />
              ))}
            </div>
          </div>
        </Card>

        {/* 左下：待办事项 */}
        <Card className="flex flex-col overflow-hidden">
          {/* 固定标题 */}
          <div className="flex items-center space-x-3 p-6 pb-4 border-b" style={{ borderColor: colors.border }}>
            <IconBox icon={CheckSquare} color={colors.primaryLight} iconColor={colors.primary} />
            <div>
              <h2 className="text-xl font-bold" style={{ color: colors.textPrimary }}>待办事项</h2>
              <p className="text-xs" style={{ color: colors.textSecondary }}>管理你的学习和工作任务</p>
            </div>
          </div>
          {/* 可滚动内容 */}
          <div className="flex-1 overflow-y-auto p-6 pt-4">
            <div className="space-y-2">
              {todos.map((todo) => (
                <div
                  key={todo.id}
                  className="border rounded-lg p-4 transition-all"
                  style={{ borderColor: colors.border }}
                >
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => toggleTodo(todo.id)}
                      className="flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors"
                      style={todo.completed ? {
                        backgroundColor: colors.primary,
                        borderColor: colors.primary
                      } : {
                        borderColor: '#C8CCD1'
                      }}
                    >
                      {todo.completed && (
                        <svg
                          className="w-3 h-3 text-white"
                          fill="none"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path d="M5 13l4 4L19 7"></path>
                        </svg>
                      )}
                    </button>
                    <span className={`flex-1 transition-all ${
                      todo.completed ? 'line-through' : ''
                    }`} style={{ color: todo.completed ? colors.textTertiary : colors.textPrimary }}>
                      {todo.text}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* 右下：今日灵感 */}
        <div className="rounded-xl flex flex-col overflow-hidden relative" style={{ backgroundColor: '#8B9DC6' }}>
          {/* 固定标题 */}
          <div className="flex items-center space-x-3 p-6 pb-4 border-b relative z-10" style={{ borderColor: 'rgba(255, 255, 255, 0.2)' }}>
            <div className="p-2 rounded-lg" style={{ backgroundColor: 'rgba(255, 255, 255, 0.3)' }}>
              <Lightbulb className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">今日灵感</h2>
              <p className="text-xs text-white opacity-90">每日一句，激励你的学习之旅</p>
            </div>
          </div>
          {/* 可滚动内容 */}
          <div className="flex-1 flex items-center justify-center p-6 relative z-10">
            <div className="rounded-lg p-6 w-full" style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}>
              <p className="text-xl leading-relaxed font-medium text-white text-center">{randomInspiration}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningAssistant;
