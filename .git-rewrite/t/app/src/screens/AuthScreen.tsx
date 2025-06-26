import React, { useState } from 'react'
import { Stack, Image } from '@tamagui/core'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import { KeyboardAvoidingView, Platform } from 'react-native'

import { Button } from '../design-system/components/atoms/Button/Button'
import { Input } from '../design-system/components/atoms/Input/Input'
import { Text, Heading } from '../design-system/components/atoms/Text/Text'
import { colors, spacing } from '../design-system/tokens'

interface AuthScreenProps {
  onMagicLinkSent: (email: string) => void
  isLoading?: boolean
}

export const AuthScreen: React.FC<AuthScreenProps> = ({
  onMagicLinkSent,
  isLoading = false
}) => {
  const [email, setEmail] = useState('')
  const [isEmailSent, setIsEmailSent] = useState(false)
  const [emailError, setEmailError] = useState('')

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSendMagicLink = async () => {
    setEmailError('')
    
    if (!email.trim()) {
      setEmailError('Please enter your email address')
      return
    }
    
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address')
      return
    }
    
    try {
      await onMagicLinkSent(email)
      setIsEmailSent(true)
    } catch (error) {
      setEmailError('Failed to send magic link. Please try again.')
    }
  }

  const handleTryAgain = () => {
    setIsEmailSent(false)
    setEmail('')
    setEmailError('')
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      <StatusBar style="dark" backgroundColor={colors.background} />
      
      <KeyboardAvoidingView 
        style={{ flex: 1 }} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <Stack
          flex={1}
          paddingHorizontal="$xxl"
          paddingVertical="$xl"
          justifyContent="center"
          alignItems="center"
          space="$xl"
        >
          {/* Logo placeholder - following wireframes.md */}
          <Stack
            width={80}
            height={80}
            backgroundColor="$primary"
            borderRadius="$lg"
            alignItems="center"
            justifyContent="center"
            marginBottom="$lg"
          >
            <Text variant="h2" color="white" weight="bold">
              PM
            </Text>
          </Stack>

          {/* Title - matching wireframes.md */}
          <Stack alignItems="center" space="$sm">
            <Heading level={1} align="center" color="text">
              Property Management
            </Heading>
            <Heading level={1} align="center" color="text">
              Portal
            </Heading>
          </Stack>

          {!isEmailSent ? (
            // Email input form - matching wireframes.md layout
            <Stack
              width="100%"
              maxWidth={400}
              backgroundColor="$surface"
              borderRadius="$lg"
              padding="$lg"
              space="$md"
              shadowColor="$shadow"
              shadowOffset={{ width: 0, height: 2 }}
              shadowOpacity={0.1}
              shadowRadius={8}
            >
              <Text variant="body" weight="medium" align="center">
                Enter your email address
              </Text>
              
              <Input
                value={email}
                onChangeText={setEmail}
                placeholder="email@example.com"
                keyboardType="email-address"
                autoCapitalize="none"
                error={emailError}
                size="lg"
              />
              
              <Button
                onPress={handleSendMagicLink}
                loading={isLoading}
                disabled={isLoading}
                size="lg"
                fullWidth
              >
                Send Magic Link
              </Button>
            </Stack>
          ) : (
            // Success state - matching wireframes.md
            <Stack
              width="100%"
              maxWidth={400}
              backgroundColor="$surface"
              borderRadius="$lg"
              padding="$lg"
              space="$md"
              alignItems="center"
              shadowColor="$shadow"
              shadowOffset={{ width: 0, height: 2 }}
              shadowOpacity={0.1}
              shadowRadius={8}
            >
              <Stack
                width={64}
                height={64}
                backgroundColor="$successLight"
                borderRadius="$full"
                alignItems="center"
                justifyContent="center"
                marginBottom="$sm"
              >
                <Text variant="h2" color="success">
                  ✓
                </Text>
              </Stack>
              
              <Text variant="h3" weight="medium" align="center">
                Check your email
              </Text>
              
              <Text variant="body" color="textSecondary" align="center">
                We've sent a secure access link to
              </Text>
              
              <Text variant="body" weight="medium" color="primary" align="center">
                {email}
              </Text>
              
              <Button
                variant="outline"
                onPress={handleTryAgain}
                size="md"
                fullWidth
              >
                Try different email
              </Button>
            </Stack>
          )}

          {/* Security features - matching wireframes.md */}
          <Stack alignItems="center" space="$md" marginTop="$xl">
            <Stack direction="row" alignItems="center" space="$sm">
              <Text variant="h2">✉️</Text>
              <Text variant="caption" color="textSecondary" align="center">
                Check your email for a{'\n'}secure access link
              </Text>
            </Stack>
            
            <Stack direction="row" alignItems="center" space="$sm">
              <Text variant="h2">🔒</Text>
              <Text variant="caption" color="textSecondary" align="center">
                Enterprise-grade security{'\n'}No passwords required
              </Text>
            </Stack>
          </Stack>
        </Stack>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

export default AuthScreen