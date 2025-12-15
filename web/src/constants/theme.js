// Morandi 配色方案
export const colors = {
  // 背景色
  background: '#F5F5F0',
  backgroundLight: '#F8F8F3',
  
  // 边框色
  border: '#E8E8E0',
  borderHover: '#F0F0E8',
  
  // 主色调
  primary: '#7C8DB0',
  primaryLight: '#C8D4E8',
  primaryDark: '#5C7BA6',
  
  // 辅助色
  green: '#6B9D7E',
  greenLight: '#E8F0EC',
  orange: '#C9956F',
  orangeLight: '#F0E8E0',
  purple: '#B08DA6',
  
  // 文字色
  textPrimary: '#4A5568',
  textSecondary: '#6B7C93',
  textTertiary: '#A8A8A0',
  
  // 白色
  white: '#FFFFFF',
};

// 常用样式
export const commonStyles = {
  card: {
    backgroundColor: colors.white,
    borderColor: colors.border,
    borderRadius: '0.75rem', // rounded-xl
  },
  
  button: {
    primary: {
      backgroundColor: colors.primary,
      color: colors.white,
    },
    secondary: {
      backgroundColor: 'transparent',
      color: colors.textSecondary,
    },
  },
  
  input: {
    borderColor: colors.border,
    color: colors.textPrimary,
  },
};

// 动画延迟
export const animationDelays = ['0ms', '150ms', '300ms'];
