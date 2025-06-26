import React, { useState } from 'react'
import { Stack, ScrollView } from '@tamagui/core'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import { Lucide } from '@tamagui/lucide-icons'

import { Text, Heading, Caption } from '../design-system/components/atoms/Text/Text'
import { Button } from '../design-system/components/atoms/Button/Button'
import GuestContact from '../components/GuestContact'
import JobCostBreakdown from '../components/JobCostBreakdown'
import { colors, spacing } from '../design-system/tokens'
import { Reservation, JOB_STATUS_CONFIGS } from '../types'

interface ReservationDetailScreenProps {
  reservation: Reservation
  onBack: () => void
  onRequestAction: (action: 'late-checkout' | 'custom-cleaning') => void
  onEditReservation?: () => void
  loading?: boolean
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
      paddingHorizontal="$md"
      paddingVertical="$sm"
      borderRadius="$full"
    >
      <Text variant="body" color="white" weight="semibold">
        {config.label}
      </Text>
    </Stack>
  )
}

const PropertyInfo: React.FC<{ reservation: Reservation }> = ({ reservation }) => {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
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
      <Text variant="body" weight="medium">
        Reservation Details
      </Text>
      
      <Stack space="$sm">
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Text variant="caption" color="textSecondary">Check-in:</Text>
          <Text variant="caption" weight="medium">
            {formatDate(reservation.checkIn)} {formatTime(reservation.checkIn)}
          </Text>
        </Stack>
        
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Text variant="caption" color="textSecondary">Check-out:</Text>
          <Text variant="caption" weight="medium">
            {formatDate(reservation.checkOut)} {formatTime(reservation.checkOut)}
          </Text>
        </Stack>
        
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Text variant="caption" color="textSecondary">Duration:</Text>
          <Text variant="caption" weight="medium">
            {reservation.duration} night{reservation.duration !== 1 ? 's' : ''}
          </Text>
        </Stack>
        
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Text variant="caption" color="textSecondary">Guests:</Text>
          <Text variant="caption" weight="medium">
            {reservation.numberOfGuests.adults} adult{reservation.numberOfGuests.adults !== 1 ? 's' : ''}
            {reservation.numberOfGuests.children > 0 && (
              `, ${reservation.numberOfGuests.children} child${reservation.numberOfGuests.children !== 1 ? 'ren' : ''}`
            )}
          </Text>
        </Stack>
      </Stack>
    </Stack>
  )
}

const JobProgress: React.FC<{ 
  job: Reservation['job']
  employee?: { name: string; phone?: string }
}> = ({ job, employee }) => {
  if (!job) return null

  const steps = [
    { key: 'created', label: 'Job Created', icon: 'plus-circle' },
    { key: 'assigned', label: 'Employee Assigned', icon: 'user-check' },
    { key: 'on_my_way', label: 'On My Way', icon: 'car' },
    { key: 'started', label: 'Started', icon: 'play-circle' },
    { key: 'completed', label: 'Completed', icon: 'check-circle' },
  ]

  const getCurrentStepIndex = (status: string) => {
    const stepMap: Record<string, number> = {
      'unscheduled': 0,
      'scheduled': 1,
      'in_progress': 3,
      'completed': 4,
    }
    return stepMap[status] ?? 0
  }

  const currentStepIndex = getCurrentStepIndex(job.workStatus)

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return null
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
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
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Text variant="body" weight="medium">
          🧹 Cleaning Status
        </Text>
        <StatusBadge status={job.workStatus} />
      </Stack>
      
      {employee && (
        <Stack
          backgroundColor="$background"
          borderRadius="$md"
          padding="$md"
          space="$sm"
        >
          <Text variant="caption" weight="medium" color="textSecondary">
            Assigned Employee
          </Text>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" space="$sm">
              <Lucide.User size={16} color={colors.textSecondary} />
              <Text variant="body" weight="medium">
                {employee.name}
              </Text>
            </Stack>
            {employee.phone && (
              <Stack direction="row" alignItems="center" space="$xs">
                <Lucide.Phone size={16} color={colors.textSecondary} />
                <Text variant="caption" color="textSecondary">
                  {employee.phone}
                </Text>
              </Stack>
            )}
          </Stack>
        </Stack>
      )}
      
      {/* Progress timeline */}
      <Stack space="$md">
        {steps.map((step, index) => {
          const isCompleted = index < currentStepIndex || (index === currentStepIndex && job.workStatus === 'completed')
          const isCurrent = index === currentStepIndex && job.workStatus !== 'completed'
          const timestamp = job.workTimestamps?.[step.key as keyof typeof job.workTimestamps]
          
          return (
            <Stack key={step.key} direction="row" alignItems="center" space="$sm">
              <Stack
                width={32}
                height={32}
                borderRadius="$full"
                backgroundColor={
                  isCompleted 
                    ? colors.success 
                    : isCurrent 
                      ? colors.primary 
                      : colors.border
                }
                alignItems="center"
                justifyContent="center"
              >
                <Lucide.CheckCircle 
                  size={16} 
                  color={
                    isCompleted || isCurrent 
                      ? colors.white 
                      : colors.textSecondary
                  } 
                />
              </Stack>
              
              <Stack flex={1}>
                <Text 
                  variant="body" 
                  weight={isCurrent ? 'semibold' : 'regular'}
                  color={
                    isCompleted 
                      ? 'success' 
                      : isCurrent 
                        ? 'primary' 
                        : 'textSecondary'
                  }
                >
                  {step.label}
                </Text>
                {timestamp && (
                  <Caption color="textSecondary">
                    {formatTime(timestamp)}
                  </Caption>
                )}
              </Stack>
            </Stack>
          )
        })}
      </Stack>
    </Stack>
  )
}

export const ReservationDetailScreen: React.FC<ReservationDetailScreenProps> = ({
  reservation,
  onBack,
  onRequestAction,
  onEditReservation,
  loading = false
}) => {
  const [showMoreActions, setShowMoreActions] = useState(false)

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      <StatusBar style="dark" backgroundColor={colors.background} />
      
      {/* Header - matching wireframes.md */}
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        paddingHorizontal="$lg"
        paddingVertical="$md"
        backgroundColor="$surface"
        borderBottomWidth={1}
        borderBottomColor="$border"
      >
        <Stack direction="row" alignItems="center" space="$md" flex={1}>
          <Button variant="ghost" size="sm" onPress={onBack}>
            <Lucide.ArrowLeft size={24} color={colors.text} />
          </Button>
          <Stack flex={1}>
            <Heading level={2} numberOfLines={1}>
              {reservation.property.name}
            </Heading>
          </Stack>
        </Stack>
        
        <Button variant="ghost" size="sm" onPress={() => setShowMoreActions(!showMoreActions)}>
          <Lucide.MoreVertical size={24} color={colors.text} />
        </Button>
      </Stack>

      <ScrollView flex={1}>
        <Stack padding="$lg" space="$lg">
          {/* Property header info */}
          <Stack alignItems="center" space="$md">
            <Heading level={1} align="center">
              🏠 {reservation.property.name}
            </Heading>
            <Text variant="body" color="textSecondary" align="center">
              📍 {reservation.property.address.fullAddress}
            </Text>
          </Stack>

          {/* Guest contact information */}
          <GuestContact guest={reservation.guest} />

          {/* Reservation details */}
          <PropertyInfo reservation={reservation} />

          {/* Job cost breakdown - with placeholder data */}
          <JobCostBreakdown
            totalCost={reservation.job?.totalPrice || 0}
            lineItems={reservation.job?.lineItems || []}
            showPlaceholder={!reservation.job?.lineItems?.length}
          />

          {/* Job progress */}
          {reservation.job && (
            <JobProgress 
              job={reservation.job}
              employee={
                reservation.job.assignedEmployees?.[0] 
                  ? {
                      name: reservation.job.assignedEmployees[0].fullName,
                      phone: reservation.job.assignedEmployees[0].phone
                    }
                  : undefined
              }
            />
          )}

          {/* Special requests / service instructions */}
          {(reservation.serviceInstructions || reservation.specialRequests?.length) && (
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
              <Text variant="body" weight="medium">
                📝 Special Instructions
              </Text>
              
              {reservation.serviceInstructions && (
                <Stack
                  backgroundColor="$background"
                  borderRadius="$md"
                  padding="$md"
                >
                  <Text variant="body">
                    {reservation.serviceInstructions}
                  </Text>
                </Stack>
              )}
              
              {reservation.specialRequests?.map((request, index) => (
                <Stack key={index} direction="row" alignItems="center" space="$sm">
                  <Text variant="caption">•</Text>
                  <Text variant="caption" color="textSecondary" flex={1}>
                    {request}
                  </Text>
                </Stack>
              ))}
            </Stack>
          )}

          {/* Action buttons - matching wireframes.md */}
          <Stack direction="row" space="$md">
            <Button
              variant="outline"
              onPress={() => onRequestAction('late-checkout')}
              flex={1}
              disabled={loading}
            >
              <Stack direction="row" alignItems="center" space="$sm">
                <Lucide.Clock size={16} color={colors.primary} />
                <Text variant="body" color="primary">
                  Request Late Checkout
                </Text>
              </Stack>
            </Button>
            
            <Button
              variant="outline"
              onPress={() => onRequestAction('custom-cleaning')}
              flex={1}
              disabled={loading}
            >
              <Stack direction="row" alignItems="center" space="$sm">
                <Lucide.Calendar size={16} color={colors.primary} />
                <Text variant="body" color="primary">
                  Custom Clean Time
                </Text>
              </Stack>
            </Button>
          </Stack>
        </Stack>
      </ScrollView>
    </SafeAreaView>
  )
}

export default ReservationDetailScreen