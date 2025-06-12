import React, { useState } from 'react'
import { Stack, Pressable } from '@tamagui/core'
import { Lucide } from '@tamagui/lucide-icons'

import { Button } from '../design-system/components/atoms/Button/Button'
import { Text, Heading, Caption } from '../design-system/components/atoms/Text/Text'
import { colors, spacing, shadows } from '../design-system/tokens'
import { Reservation, JOB_STATUS_CONFIGS } from '../types'

interface ReservationCardProps {
  reservation: Reservation
  onPress: () => void
  onRequestAction: (action: 'late-checkout' | 'custom-cleaning') => void
  variant?: 'default' | 'compact' | 'detailed'
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config = JOB_STATUS_CONFIGS[status as keyof typeof JOB_STATUS_CONFIGS] || {
    label: status,
    color: colors.textSecondary,
    textColor: colors.white
  }

  return (
    <Stack
      backgroundColor={config.color}
      paddingHorizontal="$sm"
      paddingVertical="$xs"
      borderRadius="$full"
    >
      <Text variant="caption" color="white" weight="semibold">
        {config.label}
      </Text>
    </Stack>
  )
}

const PropertyInfo: React.FC<{ 
  property: Reservation['property']
  checkIn: string
  checkOut: string
  guestName: string
}> = ({ property, checkIn, checkOut, guestName }) => {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
    })
  }

  const formatDateRange = (checkIn: string, checkOut: string) => {
    return `${formatDate(checkIn)}-${formatDate(checkOut)}`
  }

  return (
    <Stack space="$xs">
      {/* Property name and guest */}
      <Stack direction="row" alignItems="center" space="$sm">
        <Lucide.Home size={16} color={colors.textSecondary} />
        <Text variant="body" weight="medium" flex={1}>
          {property.name}
        </Text>
      </Stack>
      
      {/* Guest name */}
      <Stack direction="row" alignItems="center" space="$sm">
        <Lucide.User size={16} color={colors.textSecondary} />
        <Text variant="caption" color="textSecondary">
          {guestName}
        </Text>
      </Stack>
      
      {/* Dates and location */}
      <Stack direction="row" alignItems="center" space="$sm">
        <Lucide.Calendar size={16} color={colors.textSecondary} />
        <Text variant="caption" color="textSecondary">
          {formatDateRange(checkIn, checkOut)}
        </Text>
        <Text variant="caption" color="textSecondary">
          • 📍 {property.address.city}, {property.address.state}
        </Text>
      </Stack>
    </Stack>
  )
}

const JobProgress: React.FC<{ 
  job?: Reservation['job']
  employee?: string
}> = ({ job, employee }) => {
  if (!job) return null

  return (
    <Stack space="$sm">
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Text variant="body" weight="medium">
          🧹 Cleaning Status
        </Text>
        <StatusBadge status={job.workStatus} />
      </Stack>
      
      {employee && (
        <Stack direction="row" alignItems="center" space="$sm">
          <Lucide.User size={16} color={colors.textSecondary} />
          <Text variant="caption" color="textSecondary">
            {employee}
          </Text>
          <Text variant="caption" color="textSecondary">
            📱 (555) 123-4567
          </Text>
        </Stack>
      )}
      
      {/* Simple progress timeline */}
      <Stack direction="row" alignItems="center" space="$xs">
        {['created', 'assigned', 'on_my_way', 'started', 'completed'].map((step, index) => {
          const isCompleted = job.workTimestamps?.[step as keyof typeof job.workTimestamps]
          const isCurrent = getCurrentStep(job.workStatus) === index
          
          return (
            <React.Fragment key={step}>
              <Stack
                width={8}
                height={8}
                borderRadius="$full"
                backgroundColor={
                  isCompleted 
                    ? colors.success 
                    : isCurrent 
                      ? colors.primary 
                      : colors.border
                }
              />
              {index < 4 && (
                <Stack
                  width={16}
                  height={2}
                  backgroundColor={
                    isCompleted 
                      ? colors.success 
                      : colors.border
                  }
                />
              )}
            </React.Fragment>
          )
        })}
      </Stack>
    </Stack>
  )
}

// Helper function to determine current step
const getCurrentStep = (status: string): number => {
  const stepMap: Record<string, number> = {
    'unscheduled': 0,
    'scheduled': 1,
    'in_progress': 3,
    'completed': 4,
  }
  return stepMap[status] ?? 0
}

export const ReservationCard: React.FC<ReservationCardProps> = ({
  reservation,
  onPress,
  onRequestAction,
  variant = 'default'
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  
  return (
    <Pressable
      onPress={onPress}
      style={{
        marginBottom: spacing.md,
      }}
    >
      <Stack
        backgroundColor="$surface"
        borderRadius="$lg"
        padding="$lg"
        space="$md"
        shadowColor="$shadow"
        shadowOffset={{ width: 0, height: 2 }}
        shadowOpacity={0.1}
        shadowRadius={8}
        pressStyle={{ scale: 0.98 }}
      >
        {/* Header with property name and status */}
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Stack flex={1} marginRight="$sm">
            <Heading level={3}>
              {reservation.property.name}
            </Heading>
            <Caption>
              {reservation.guest.fullName}
            </Caption>
          </Stack>
          
          {reservation.job && (
            <StatusBadge status={reservation.job.workStatus} />
          )}
        </Stack>
        
        {/* Property and reservation info */}
        <PropertyInfo
          property={reservation.property}
          checkIn={reservation.checkIn}
          checkOut={reservation.checkOut}
          guestName={reservation.guest.fullName}
        />
        
        {/* Job progress (expanded view) */}
        {reservation.job && (variant === 'detailed' || isExpanded) && (
          <JobProgress 
            job={reservation.job}
            employee={reservation.job.assignedEmployees?.[0]?.fullName}
          />
        )}
        
        {/* Expand/collapse button for default variant */}
        {variant === 'default' && reservation.job && (
          <Button
            variant="ghost"
            size="sm"
            onPress={() => setIsExpanded(!isExpanded)}
          >
            <Stack direction="row" alignItems="center" space="$xs">
              <Text variant="caption" color="primary">
                {isExpanded ? 'Show Less' : 'Show More'}
              </Text>
              <Lucide.ChevronDown 
                size={16} 
                color={colors.primary}
                style={{
                  transform: [{ rotate: isExpanded ? '180deg' : '0deg' }]
                }}
              />
            </Stack>
          </Button>
        )}
        
        {/* Action buttons - matching wireframes.md */}
        <Stack 
          direction="row" 
          space="$sm"
          borderTopWidth={1}
          borderTopColor="$border"
          paddingTop="$md"
        >
          <Button
            variant="outline"
            size="sm"
            onPress={() => onRequestAction('late-checkout')}
            flex={1}
          >
            <Stack direction="row" alignItems="center" space="$xs">
              <Text variant="caption" color="primary">
                Late Checkout
              </Text>
            </Stack>
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onPress={() => onRequestAction('custom-cleaning')}
            flex={1}
          >
            <Stack direction="row" alignItems="center" space="$xs">
              <Text variant="caption" color="primary">
                Custom Clean
              </Text>
            </Stack>
          </Button>
        </Stack>
      </Stack>
    </Pressable>
  )
}

export default ReservationCard