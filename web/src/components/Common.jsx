import React from 'react';
import { colors } from '../constants/theme';

// 通用卡片容器
export const Card = ({ children, className = '', style = {} }) => (
  <div
    className={`bg-white rounded-xl border ${className}`}
    style={{ borderColor: colors.border, ...style }}
  >
    {children}
  </div>
);

// 通用按钮
export const Button = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  disabled = false,
  className = '',
  icon: Icon,
  ...props 
}) => {
  const variantStyles = {
    primary: {
      backgroundColor: colors.primary,
      color: colors.white,
    },
    secondary: {
      backgroundColor: 'transparent',
      color: colors.textSecondary,
      border: `1px solid ${colors.border}`,
    },
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      style={variantStyles[variant]}
      {...props}
    >
      {Icon && <Icon className="w-4 h-4" />}
      <span>{children}</span>
    </button>
  );
};

// 图标容器
export const IconBox = ({ icon: Icon, color = colors.primaryLight, iconColor = colors.primaryDark, size = 'md' }) => {
  const sizes = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3',
  };
  
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <div className={`${sizes[size]} rounded-lg`} style={{ backgroundColor: color }}>
      <Icon className={iconSizes[size]} style={{ color: iconColor }} />
    </div>
  );
};

// 文档/列表项卡片
export const ListItem = ({ 
  icon: Icon, 
  iconBg = colors.primaryLight,
  iconColor = colors.primaryDark,
  title, 
  subtitle, 
  meta,
  onClick,
  className = '' 
}) => (
  <div
    onClick={onClick}
    className={`bg-white rounded-xl border p-4 transition-all cursor-pointer hover:shadow-sm ${className}`}
    style={{ borderColor: colors.border }}
  >
    <div className="flex items-start space-x-3">
      <div className="p-2 rounded-lg" style={{ backgroundColor: iconBg }}>
        <Icon className="w-4 h-4" style={{ color: iconColor }} />
      </div>
      <div className="flex-1">
        <h3 className="font-semibold mb-1" style={{ color: colors.textPrimary }}>
          {title}
        </h3>
        {subtitle && (
          <p className="text-xs" style={{ color: colors.textSecondary }}>
            {subtitle}
          </p>
        )}
        {meta && (
          <div className="flex items-center space-x-4 text-xs mt-1" style={{ color: colors.textSecondary }}>
            {meta}
          </div>
        )}
      </div>
    </div>
  </div>
);

// 加载动画（打字中的三个点）
export const TypingIndicator = ({ color = colors.primary }) => (
  <div className="flex space-x-2">
    {[0, 150, 300].map((delay, idx) => (
      <div
        key={idx}
        className="w-2 h-2 rounded-full animate-bounce"
        style={{ 
          backgroundColor: color,
          animationDelay: `${delay}ms`
        }}
      />
    ))}
  </div>
);

// 分类标签
export const Badge = ({ children, active = false, count, onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-200 text-sm w-full"
    style={active ? {
      backgroundColor: colors.primary,
      color: colors.white
    } : {
      color: colors.textPrimary
    }}
    onMouseEnter={(e) => {
      if (!active) {
        e.currentTarget.style.backgroundColor = colors.backgroundLight;
      }
    }}
    onMouseLeave={(e) => {
      if (!active) {
        e.currentTarget.style.backgroundColor = 'transparent';
      }
    }}
  >
    <span className="font-medium">{children}</span>
    {count !== undefined && (
      <span 
        className="text-xs px-2 py-0.5 rounded-full" 
        style={{ 
          backgroundColor: active ? 'rgba(255, 255, 255, 0.3)' : colors.border,
          color: active ? colors.white : colors.textSecondary
        }}
      >
        {count}
      </span>
    )}
  </button>
);
