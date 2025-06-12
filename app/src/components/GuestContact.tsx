import React from 'react'
import { Stack, Pressable, Linking, Alert } from '@tamagui/core'
import { Lucide } from '@tamagui/lucide-icons'

import { Text, Caption } from '../design-system/components/atoms/Text/Text'
import { Button } from '../design-system/components/atoms/Button/Button'
import { colors, spacing } from '../design-system/tokens'
import { Guest } from '../types'

interface GuestContactProps {
  guest: Guest
  onCall?: (phone: string) => void
  onEmail?: (email: string) => void
  onSMS?: (phone: string) => void
  compact?: boolean
}

export const GuestContact: React.FC<GuestContactProps> = ({
  guest,
  onCall,
  onEmail,
  onSMS,
  compact = false
}) => {
  const handleCall = async (phone: string) => {
    try {
      if (onCall) {
        onCall(phone)
      } else {
        const phoneUrl = `tel:${phone.replace(/[^\d+]/g, '')}`
        const canOpen = await Linking.canOpenURL(phoneUrl)
        if (canOpen) {
          await Linking.openURL(phoneUrl)
        } else {
          Alert.alert('Error', 'Unable to make phone call')
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Unable to make phone call')
    }
  }

  const handleEmail = async (email: string) => {
    try {
      if (onEmail) {
        onEmail(email)
      } else {
        const emailUrl = `mailto:${email}`
        const canOpen = await Linking.canOpenURL(emailUrl)
        if (canOpen) {
          await Linking.openURL(emailUrl)
        } else {
          Alert.alert('Error', 'Unable to open email client')
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Unable to open email client')
    }
  }

  const handleSMS = async (phone: string) => {
    try {
      if (onSMS) {
        onSMS(phone)
      } else {
        const smsUrl = `sms:${phone.replace(/[^\d+]/g, '')}`
        const canOpen = await Linking.canOpenURL(smsUrl)
        if (canOpen) {
          await Linking.openURL(smsUrl)
        } else {
          Alert.alert('Error', 'Unable to open messaging app')
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Unable to open messaging app')
    }
  }

  const formatPhone = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '')
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`
    }
    return phone
  }

  return (
    <Stack
      backgroundColor="$surface"
      borderRadius="$lg"
      padding="$lg"
      space="$md"
      shadowColor="$shadow"
      shadowOffset={{ width: 0, height: 2 }}
      shadowOpacity={0.1}
      shadowRadius={8}
    >
      {/* Header */}
      <Text variant={compact ? "body" : "h3"} weight="medium">
        Guest Information
      </Text>

      {/* Guest name - prominently displayed */}
      <Stack direction="row" alignItems="center" space="$sm">
        <Lucide.User size={20} color={colors.primary} />
        <Text variant="body" weight="semibold">
          {guest.fullName}
        </Text>
      </Stack>

      {/* Contact information */}
      <Stack space="$sm">
        {/* Email */}
        {guest.email ? (
          <Stack direction="row" alignItems="center" space="$sm">
            <Lucide.Mail size={16} color={colors.textSecondary} />
            <Text variant="caption" color="textSecondary" flex={1}>
              {guest.email}
            </Text>
          </Stack>
        ) : (
          <Stack direction="row" alignItems="center" space="$sm">
            <Lucide.Mail size={16} color={colors.textLight} />
            <Text variant="caption" color="textLight" flex={1}>
              No email provided
            </Text>
          </Stack>
        )}

        {/* Phone */}
        {guest.phone ? (
          <Stack direction="row" alignItems="center" space="$sm">
            <Lucide.Phone size={16} color={colors.textSecondary} />
            <Text variant="caption" color="textSecondary" flex={1}>
              {formatPhone(guest.phone)}
            </Text>
          </Stack>
        ) : (
          <Stack direction="row" alignItems="center" space="$sm">
            <Lucide.Phone size={16} color={colors.textLight} />
            <Text variant="caption" color="textLight" flex={1}>
              No phone provided
            </Text>
          </Stack>
        )}
      </Stack>

      {/* Action buttons - matching wireframes.md */}
      {(guest.phone || guest.email) && (
        <Stack direction="row" space="$sm">
          {guest.phone && (
            <>
              <Button
                variant="outline"
                size="sm"
                onPress={() => handleCall(guest.phone!)}
                flex={1}
              >
                <Stack direction="row" alignItems="center" space="$xs">
                  <Lucide.Phone size={16} color={colors.primary} />
                  <Text variant="caption" color="primary">
                    Call
                  </Text>
                </Stack>
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onPress={() => handleSMS(guest.phone!)}
                flex={1}
              >
                <Stack direction="row" alignItems="center" space="$xs">
                  <Lucide.MessageSquare size={16} color={colors.primary} />
                  <Text variant="caption" color="primary">
                    SMS
                  </Text>
                </Stack>
              </Button>
            </>
          )}
          
          {guest.email && (
            <Button
              variant="outline"
              size="sm"
              onPress={() => handleEmail(guest.email!)}
              flex={1}
            >
              <Stack direction="row" alignItems="center" space="$xs">
                <Lucide.Mail size={16} color={colors.primary} />
                <Text variant="caption" color="primary">
                  Email
                </Text>
              </Stack>
            </Button>
          )}
        </Stack>
      )}

      {/* No contact info state */}
      {!guest.phone && !guest.email && (
        <Stack alignItems="center" padding="$md">
          <Lucide.UserX size={24} color={colors.textSecondary} />
          <Text variant="caption" color="textSecondary" align="center" marginTop="$sm">
            No contact information available
            {'\n'}for this guest
          </Text>
        </Stack>
      )}

      {/* Emergency contact if available */}
      {guest.emergencyContact && (
        <Stack
          backgroundColor="$background"
          borderRadius="$md"
          padding="$sm"
          space="$xs"
        >
          <Text variant="caption" weight="medium" color="textSecondary">
            Emergency Contact
          </Text>
          <Stack direction="row" alignItems="center" space="$sm">
            <Lucide.UserCheck size={14} color={colors.textSecondary} />
            <Text variant="caption" color="textSecondary">
              {guest.emergencyContact.name} ({guest.emergencyContact.relationship})
            </Text>
          </Stack>
          <Stack direction="row" alignItems="center" space="$sm">
            <Lucide.Phone size={14} color={colors.textSecondary} />
            <Text variant="caption" color="textSecondary">
              {formatPhone(guest.emergencyContact.phone)}
            </Text>
            <Pressable 
              onPress={() => handleCall(guest.emergencyContact!.phone)}
              style={{ marginLeft: 'auto' }}
            >
              <Lucide.Phone size={16} color={colors.primary} />
            </Pressable>
          </Stack>
        </Stack>
      )}
    </Stack>
  )
}

export default GuestContact