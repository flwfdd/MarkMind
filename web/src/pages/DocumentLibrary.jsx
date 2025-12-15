import React, { useState } from 'react';
import { Upload, FileText, ChevronRight } from 'lucide-react';
import { colors } from '../constants/theme';
import { Card, Button, IconBox, Badge } from '../components/Common';

const DocumentLibrary = () => {
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedDocCategory, setSelectedDocCategory] = useState('前端开发');

  const categories = [
    {
      id: 1,
      name: '前端开发',
      count: 12,
      documents: [
        { id: 1, title: 'React Hooks 完整指南', date: '2025-12-10', size: '2.3 MB' },
        { id: 2, title: 'TypeScript 高级类型系统', date: '2025-12-08', size: '1.8 MB' },
        { id: 3, title: 'Webpack 配置优化实践', date: '2025-12-05', size: '3.1 MB' },
        { id: 4, title: 'Vue3 Composition API 深入解析', date: '2025-12-03', size: '2.7 MB' },
      ],
    },
    {
      id: 2,
      name: '后端技术',
      count: 8,
      documents: [
        { id: 5, title: 'Node.js 性能优化技巧', date: '2025-12-09', size: '1.9 MB' },
        { id: 6, title: 'MySQL 索引优化指南', date: '2025-12-07', size: '2.2 MB' },
        { id: 7, title: 'Redis 缓存策略详解', date: '2025-12-04', size: '1.5 MB' },
      ],
    },
    {
      id: 3,
      name: '系统设计',
      count: 6,
      documents: [
        { id: 8, title: '微服务架构设计模式', date: '2025-12-06', size: '4.2 MB' },
        { id: 9, title: '分布式系统理论与实践', date: '2025-12-02', size: '3.8 MB' },
      ],
    },
    {
      id: 4,
      name: '数据结构与算法',
      count: 15,
      documents: [
        { id: 10, title: '二叉树遍历算法总结', date: '2025-12-11', size: '1.2 MB' },
        { id: 11, title: '动态规划经典问题', date: '2025-12-09', size: '2.5 MB' },
        { id: 12, title: '排序算法性能对比分析', date: '2025-12-01', size: '1.7 MB' },
      ],
    },
    {
      id: 5,
      name: '产品设计',
      count: 4,
      documents: [
        { id: 13, title: 'UI/UX 设计原则', date: '2025-11-28', size: '3.5 MB' },
        { id: 14, title: '用户体验优化案例', date: '2025-11-25', size: '2.9 MB' },
      ],
    },
  ];

  const currentDocCategory = categories.find(cat => cat.name === selectedDocCategory);

  const handleUpload = () => {
    setUploadingFile(true);
    // 模拟上传
    setTimeout(() => {
      setUploadingFile(false);
      alert('文档上传成功！');
    }, 1500);
  };

  return (
    <div className="h-full flex">
      {/* 左侧：文档分类导航 */}
      <div className="w-64 bg-white border-r p-4 overflow-y-auto" style={{ borderColor: colors.border }}>
        <div className="mb-6">
          <h2 className="text-lg font-semibold px-3 mb-3" style={{ color: colors.textPrimary }}>我的文档库</h2>
        </div>
        
        {/* 文档分类 */}
        <div className="space-y-1">
          {categories.map((category) => (
            <Badge
              key={category.id}
              active={selectedDocCategory === category.name}
              count={category.count}
              onClick={() => setSelectedDocCategory(category.name)}
            >
              {category.name}
            </Badge>
          ))}
        </div>
      </div>

      {/* 右侧：文档内容展示区 */}
      <div className="flex-1 p-6 overflow-y-auto" style={{ backgroundColor: colors.background }}>
        <Card className="p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-1" style={{ color: colors.textPrimary }}>{selectedDocCategory}</h1>
              <p className="text-sm" style={{ color: colors.textSecondary }}>
                共 {currentDocCategory?.count} 篇文档
              </p>
            </div>
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={uploadingFile}
              icon={Upload}
              className="px-6 py-3"
            >
              {uploadingFile ? '上传中...' : '文档上传'}
            </Button>
          </div>
        </Card>

        <div className="space-y-3">
          {currentDocCategory?.documents.map((doc) => (
            <Card
              key={doc.id}
              className="p-6 transition-all cursor-pointer hover:shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <IconBox icon={FileText} color={colors.primaryLight} iconColor={colors.primaryDark} size="lg" />
                  <div className="flex-1">
                    <h3 className="font-semibold mb-1 transition-colors" style={{ color: colors.textPrimary }}>
                      {doc.title}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm" style={{ color: colors.textSecondary }}>
                      <span>更新时间：{doc.date}</span>
                      <span>大小：{doc.size}</span>
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 transition-colors" style={{ color: colors.textTertiary }} />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DocumentLibrary;
