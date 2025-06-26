// Design tokens matching wireframes.md specifications

export const colors = {
  // Primary colors from wireframes
  primary: '#0066CC',
  primaryLight: '#3D8BFF', 
  primaryDark: '#004C99',
  
  // Secondary colors
  secondary: '#FF6B35',
  secondaryLight: '#FF8A5B',
  secondaryDark: '#E55A2B',
  
  // Status colors  
  success: '#22C55E',
  successLight: '#4ADE80',
  warning: '#F59E0B',
  warningLight: '#FBBF24',
  error: '#EF4444',
  errorLight: '#F87171',
  
  // Neutral colors
  white: '#FFFFFF',
  black: '#000000',
  background: '#F8FAFC',
  surface: '#FFFFFF', 
  border: '#E2E8F0',
  
  // Text colors
  text: '#1E293B',
  textSecondary: '#64748B',
  textLight: '#94A3B8',
  
  // Additional colors
  shadow: '#000000',
  overlay: 'rgba(0, 0, 0, 0.5)',
  focus: '#0066CC',
} as const

export const spacing = {
  xs: 4,
  sm: 8, 
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
} as const

export const typography = {
  // From wireframes.md typography scale
  h1: { 
    fontSize: 32, 
    fontWeight: '700' as const, 
    lineHeight: 40,
    fontFamily: 'Poppins-Bold'
  },
  h2: { 
    fontSize: 24, 
    fontWeight: '600' as const, 
    lineHeight: 32,
    fontFamily: 'Poppins-SemiBold'
  },
  h3: { 
    fontSize: 20, 
    fontWeight: '500' as const, 
    lineHeight: 28,
    fontFamily: 'Poppins-Medium'
  },
  body: { 
    fontSize: 16, 
    fontWeight: '400' as const, 
    lineHeight: 24,
    fontFamily: 'Inter-Regular'
  },
  caption: { 
    fontSize: 14, 
    fontWeight: '400' as const, 
    lineHeight: 20,
    fontFamily: 'Inter-Regular'
  },
  button: { 
    fontSize: 16, 
    fontWeight: '600' as const, 
    lineHeight: 24,
    fontFamily: 'Inter-SemiBold'
  },
} as const

export const shadows = {
  sm: {
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  lg: {
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
} as const

export const animations = {
  // Button press animation from wireframes
  buttonPress: {
    scale: 0.98,
    duration: 150,
  },
  // Card selection animation
  cardSelect: {
    shadowOpacity: 0.2,
    shadowRadius: 12,
    duration: 200,
  },
  // Loading animation
  loading: {
    opacity: [1, 0.5, 1],
    duration: 1500,
    repeat: -1,
  },
} as const

export type Colors = typeof colors
export type Spacing = typeof spacing  
export type BorderRadius = typeof borderRadius
export type Typography = typeof typography
export type Shadows = typeof shadows
export type Animations = typeof animations