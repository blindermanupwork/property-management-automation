import React from 'react'
import { Text as TamaguiText, styled } from '@tamagui/core'
import { typography, colors } from '../../../tokens'

export interface TextProps {
  variant?: 'h1' | 'h2' | 'h3' | 'body' | 'caption' | 'button'
  color?: 'primary' | 'secondary' | 'text' | 'textSecondary' | 'textLight' | 'white' | 'success' | 'warning' | 'error'
  align?: 'left' | 'center' | 'right'
  weight?: 'regular' | 'medium' | 'semibold' | 'bold'
  children: React.ReactNode
}

const StyledText = styled(TamaguiText, {
  name: 'Text',
  
  variants: {
    variant: {
      h1: {
        fontSize: 32,
        fontWeight: '700',
        lineHeight: 40,
        fontFamily: '$heading',
      },
      h2: {
        fontSize: 24,
        fontWeight: '600', 
        lineHeight: 32,
        fontFamily: '$heading',
      },
      h3: {
        fontSize: 20,
        fontWeight: '500',
        lineHeight: 28,
        fontFamily: '$heading',
      },
      body: {
        fontSize: 16,
        fontWeight: '400',
        lineHeight: 24,
        fontFamily: '$body',
      },
      caption: {
        fontSize: 14,
        fontWeight: '400',
        lineHeight: 20,
        fontFamily: '$body',
      },
      button: {
        fontSize: 16,
        fontWeight: '600',
        lineHeight: 24,
        fontFamily: '$body',
      },
    },
    color: {
      primary: {
        color: '$primary',
      },
      secondary: {
        color: '$secondary',
      },
      text: {
        color: '$text',
      },
      textSecondary: {
        color: '$textSecondary',
      },
      textLight: {
        color: '$textLight',
      },
      white: {
        color: '$white',
      },
      success: {
        color: '$success',
      },
      warning: {
        color: '$warning',
      },
      error: {
        color: '$error',
      },
    },
    align: {
      left: {
        textAlign: 'left',
      },
      center: {
        textAlign: 'center',
      },
      right: {
        textAlign: 'right',
      },
    },
    weight: {
      regular: {
        fontWeight: '400',
      },
      medium: {
        fontWeight: '500',
      },
      semibold: {
        fontWeight: '600',
      },
      bold: {
        fontWeight: '700',
      },
    },
  },
  
  defaultVariants: {
    variant: 'body',
    color: 'text',
    align: 'left',
  },
})

export const Text: React.FC<TextProps> = ({
  variant = 'body',
  color = 'text',
  align = 'left',
  weight,
  children,
  ...props
}) => {
  return (
    <StyledText
      variant={variant}
      color={color}
      align={align}
      weight={weight}
      {...props}
    >
      {children}
    </StyledText>
  )
}

// Convenience components for common text variants
export const Heading = ({ level = 1, ...props }: { level?: 1 | 2 | 3 } & Omit<TextProps, 'variant'>) => (
  <Text variant={`h${level}` as 'h1' | 'h2' | 'h3'} {...props} />
)

export const Caption = (props: Omit<TextProps, 'variant'>) => (
  <Text variant="caption" color="textSecondary" {...props} />
)

export const Body = (props: Omit<TextProps, 'variant'>) => (
  <Text variant="body" {...props} />
)

export default Text