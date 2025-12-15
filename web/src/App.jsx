import React, { useState } from 'react';
import { Home, BookOpen, Brain, Sparkles } from 'lucide-react';
import HomePage from './pages/HomePage';
import DocumentLibrary from './pages/DocumentLibrary';
import LearningAssistant from './pages/LearningAssistant';
import { colors } from './constants/theme';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  const menuItems = [
    { id: 'home', label: '主页', icon: Home },
    { id: 'documents', label: '我的文档库', icon: BookOpen },
    { id: 'assistant', label: '学习助手', icon: Sparkles },
  ];

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage />;
      case 'documents':
        return <DocumentLibrary />;
      case 'assistant':
        return <LearningAssistant />;
      default:
        return <HomePage />;
    }
  };

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: colors.background }}>
      {/* 顶部导航栏 */}
      <header className="bg-white border-b px-6 py-3" style={{ borderColor: colors.border }}>
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-2 group cursor-pointer">
            <div className="p-1.5 rounded-lg transition-colors" style={{ backgroundColor: colors.primary }}>
              <Brain className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold" style={{ color: colors.primaryDark }}>MarkMind</span>
          </div>

          {/* 导航菜单 */}
          <nav className="flex items-center space-x-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className="flex items-center space-x-2 px-4 py-2.5 rounded-lg transition-all duration-200"
                  style={isActive ? {
                    backgroundColor: colors.primary,
                    color: colors.white
                  } : {
                    color: colors.textSecondary
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = colors.borderHover;
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="flex-1 overflow-auto">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
