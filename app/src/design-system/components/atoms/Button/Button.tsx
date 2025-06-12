import React from 'react'
import { Button as TamaguiButton, Text, styled } from '@tamagui/core'
import { colors, typography, borderRadius, spacing } from '../../../tokens'

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onPress?: () => void
  children: React.ReactNode
  fullWidth?: boolean
}

const StyledButton = styled(TamaguiButton, {
  name: 'Button',
  borderRadius: '$md',
  alignItems: 'center',
  justifyContent: 'center',
  flexDirection: 'row',
  borderWidth: 1,
  
  pressStyle: {
    scale: 0.98,
  },
  
  hoverStyle: {
    opacity: 0.9,
  },
  
  focusStyle: {
    borderColor: '$focus',
    borderWidth: 2,
  },
  
  variants: {
    variant: {
      primary: {
        backgroundColor: '$primary',
        borderColor: '$primary',
        color: '$white',
        hoverStyle: {
          backgroundColor: '$primaryLight',
        },
        pressStyle: {
          backgroundColor: '$primaryDark',
          scale: 0.98,
        },
      },
      secondary: {
        backgroundColor: '$secondary',
        borderColor: '$secondary', 
        color: '$white',
        hoverStyle: {
          backgroundColor: '$secondaryLight',
        },
        pressStyle: {
          backgroundColor: '$secondaryDark',
          scale: 0.98,
        },
      },
      outline: {
        backgroundColor: 'transparent',
        borderColor: '$primary',
        color: '$primary',
        hoverStyle: {
          backgroundColor: '$primaryLight',
          opacity: 0.1,
        },
        pressStyle: {
          backgroundColor: '$primaryLight',
          opacity: 0.2,
          scale: 0.98,
        },
      },
      ghost: {
        backgroundColor: 'transparent',
        borderColor: 'transparent',
        color: '$primary',
        hoverStyle: {
          backgroundColor: '$primary',
          opacity: 0.1,
        },
        pressStyle: {
          backgroundColor: '$primary',
          opacity: 0.2,
          scale: 0.98,
        },
      },
    },
    size: {
      sm: {
        paddingHorizontal: '$md',
        paddingVertical: '$sm',
        height: 32,
        borderRadius: '$sm',
      },
      md: {
        paddingHorizontal: '$lg',
        paddingVertical: '$md',
        height: 40,
        borderRadius: '$md',
      },
      lg: {
        paddingHorizontal: '$xl',
        paddingVertical: '$lg', 
        height: 48,
        borderRadius: '$lg',
      },
    },
    disabled: {
      true: {
        opacity: 0.5,
        pointerEvents: 'none',
      },
    },
    fullWidth: {
      true: {
        width: '100%',
      },
    },
  },
  
  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
})

const ButtonText = styled(Text, {
  variants: {
    variant: {
      primary: {
        color: '$white',
      },
      secondary: {
        color: '$white', 
      },
      outline: {
        color: '$primary',
      },
      ghost: {
        color: '$primary',
      },
    },
    size: {
      sm: {
        fontSize: 14,
        fontWeight: '600',
      },
      md: {
        fontSize: 16,
        fontWeight: '600',
      },
      lg: {
        fontSize: 16,
        fontWeight: '600',
      },
    },
  },
})

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onPress,
  children,
  fullWidth = false,
  ...props
}) => {
  return (
    <StyledButton
      variant={variant}
      size={size}
      disabled={disabled || loading}
      fullWidth={fullWidth}
      onPress={onPress}
      {...props}
    >
      {loading ? (
        <ButtonText variant={variant} size={size}>
          Loading...
        </ButtonText>
      ) : (
        <ButtonText variant={variant} size={size}>
          {children}
        </ButtonText>
      )}
    </StyledButton>
  )
}

export default Button