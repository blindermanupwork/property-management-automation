import React, { useState } from 'react'
import { Input as TamaguiInput, Stack, styled } from '@tamagui/core'
import { Text } from '../Text/Text'
import { colors, spacing, borderRadius } from '../../../tokens'

export interface InputProps {
  value?: string
  onChangeText?: (text: string) => void
  placeholder?: string
  label?: string
  error?: string
  state?: 'default' | 'focus' | 'error' | 'success'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  secureTextEntry?: boolean
  keyboardType?: 'default' | 'email-address' | 'numeric' | 'phone-pad'
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters'
  multiline?: boolean
  numberOfLines?: number
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const StyledInput = styled(TamaguiInput, {
  name: 'Input',
  borderWidth: 1,
  borderRadius: '$md',
  backgroundColor: '$surface',
  color: '$text',
  fontSize: 16,
  fontFamily: '$body',
  
  focusStyle: {
    borderColor: '$primary',
    borderWidth: 2,
  },
  
  variants: {
    state: {
      default: {
        borderColor: '$border',
      },
      focus: {
        borderColor: '$primary',
        borderWidth: 2,
      },
      error: {
        borderColor: '$error',
        borderWidth: 2,
      },
      success: {
        borderColor: '$success',
        borderWidth: 2,
      },
    },
    size: {
      sm: {
        fontSize: 14,
        paddingVertical: '$sm',
        paddingHorizontal: '$sm',
        height: 32,
      },
      md: {
        fontSize: 16,
        paddingVertical: '$md',
        paddingHorizontal: '$md',
        height: 40,
      },
      lg: {
        fontSize: 16,
        paddingVertical: '$lg',
        paddingHorizontal: '$lg',
        height: 48,
      },
    },
    disabled: {
      true: {
        opacity: 0.5,
        backgroundColor: '$backgroundLight',
      },
    },
    hasLeftIcon: {
      true: {
        paddingLeft: 40,
      },
    },
    hasRightIcon: {
      true: {
        paddingRight: 40,
      },
    },
  },
  
  defaultVariants: {
    state: 'default',
    size: 'md',
  },
})

const InputContainer = styled(Stack, {
  position: 'relative',
  width: '100%',
})

const IconContainer = styled(Stack, {
  position: 'absolute',
  top: 0,
  bottom: 0,
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 1,
  
  variants: {
    position: {
      left: {
        left: 12,
      },
      right: {
        right: 12,
      },
    },
  },
})

export const Input: React.FC<InputProps> = ({
  value,
  onChangeText,
  placeholder,
  label,
  error,
  state = 'default',
  size = 'md',
  disabled = false,
  secureTextEntry = false,
  keyboardType = 'default',
  autoCapitalize = 'sentences',
  multiline = false,
  numberOfLines = 1,
  leftIcon,
  rightIcon,
  ...props
}) => {
  const [isFocused, setIsFocused] = useState(false)
  
  const inputState = error ? 'error' : isFocused ? 'focus' : state
  
  return (
    <Stack space="$sm" width="100%">
      {label && (
        <Text variant="caption" weight="medium" color="text">
          {label}
        </Text>
      )}
      
      <InputContainer>
        {leftIcon && (
          <IconContainer position="left">
            {leftIcon}
          </IconContainer>
        )}
        
        <StyledInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          state={inputState}
          size={size}
          disabled={disabled}
          secureTextEntry={secureTextEntry}
          keyboardType={keyboardType}
          autoCapitalize={autoCapitalize}
          multiline={multiline}
          numberOfLines={numberOfLines}
          hasLeftIcon={!!leftIcon}
          hasRightIcon={!!rightIcon}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />
        
        {rightIcon && (
          <IconContainer position="right">
            {rightIcon}
          </IconContainer>
        )}
      </InputContainer>
      
      {error && (
        <Text variant="caption" color="error">
          {error}
        </Text>
      )}
    </Stack>
  )
}

export default Input