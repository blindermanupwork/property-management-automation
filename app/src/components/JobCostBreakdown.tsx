import React, { useState } from 'react'
import { Stack, Pressable } from '@tamagui/core'
import { Lucide } from '@tamagui/lucide-icons'

import { Text, Caption } from '../design-system/components/atoms/Text/Text'
import { Button } from '../design-system/components/atoms/Button/Button'
import { colors, spacing } from '../design-system/tokens'
import { JobLineItem } from '../types'

interface JobCostBreakdownProps {
  totalCost: number
  lineItems: JobLineItem[]
  compact?: boolean
  showPlaceholder?: boolean
}

interface LineItemRowProps {
  item: JobLineItem
}

const LineItemRow: React.FC<LineItemRowProps> = ({ item }) => {
  const formatCurrency = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'service':
        return '🧹'
      case 'product':
        return '📦'
      case 'fee':
        return '💵'
      case 'discount':
        return '🏷️'
      default:
        return '•'
    }
  }

  return (
    <Stack direction="row" alignItems="center" justifyContent="space-between" paddingVertical="$xs">
      <Stack direction="row" alignItems="center" space="$sm" flex={1}>
        <Text variant="caption">
          {getCategoryIcon(item.kind)}
        </Text>
        <Stack flex={1}>
          <Text variant="caption" weight="medium">
            {item.name}
          </Text>
          {item.quantity > 1 && (
            <Caption color="textSecondary">
              {item.quantity} × {formatCurrency(item.unitPrice)}
            </Caption>
          )}
        </Stack>
      </Stack>
      <Text variant="caption" weight="medium" color={item.kind === 'discount' ? 'success' : 'text'}>
        {item.kind === 'discount' ? '-' : ''}{formatCurrency(item.total)}
      </Text>
    </Stack>
  )
}

const PlaceholderLineItems: React.FC = () => {
  return (
    <Stack space="$xs">
      <LineItemRow
        item={{
          id: 'placeholder-1',
          name: 'Standard Cleaning',
          quantity: 1,
          unitPrice: 8500,
          total: 8500,
          kind: 'service',
          taxable: true
        }}
      />
      <LineItemRow
        item={{
          id: 'placeholder-2',
          name: 'Deep Clean Kitchen',
          quantity: 1,
          unitPrice: 2500,
          total: 2500,
          kind: 'service',
          taxable: true
        }}
      />
      <LineItemRow
        item={{
          id: 'placeholder-3',
          name: 'Extra Towels',
          quantity: 4,
          unitPrice: 375,
          total: 1500,
          kind: 'product',
          taxable: false
        }}
      />
    </Stack>
  )
}

export const JobCostBreakdown: React.FC<JobCostBreakdownProps> = ({
  totalCost,
  lineItems,
  compact = false,
  showPlaceholder = false
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const formatCurrency = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`
  }

  // Use placeholder data if requested and no real data
  const displayLineItems = showPlaceholder && lineItems.length === 0 
    ? [
        {
          id: 'placeholder-1',
          name: 'Standard Cleaning',
          quantity: 1,
          unitPrice: 8500,
          total: 8500,
          kind: 'service' as const,
          taxable: true
        },
        {
          id: 'placeholder-2', 
          name: 'Deep Clean Kitchen',
          quantity: 1,
          unitPrice: 2500,
          total: 2500,
          kind: 'service' as const,
          taxable: true
        },
        {
          id: 'placeholder-3',
          name: 'Extra Towels',
          quantity: 4,
          unitPrice: 375,
          total: 1500,
          kind: 'product' as const,
          taxable: false
        }
      ]
    : lineItems

  const displayTotal = showPlaceholder && totalCost === 0 
    ? 12500 // $125.00 placeholder
    : totalCost

  const hasItems = displayLineItems.length > 0

  return (
    <Stack
      backgroundColor="$surface"
      borderRadius="$lg"
      padding="$lg"
      space="$sm"
      shadowColor="$shadow"
      shadowOffset={{ width: 0, height: 2 }}
      shadowOpacity={0.1}
      shadowRadius={8}
    >
      {/* Header with total cost - matching wireframes.md */}
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Stack direction="row" alignItems="center" space="$sm">
          <Text variant="h3" weight="medium">
            💰 Job Cost:
          </Text>
          <Text variant="h3" weight="bold" color="primary">
            {formatCurrency(displayTotal)}
          </Text>
        </Stack>
        
        {hasItems && (
          <Pressable onPress={() => setIsExpanded(!isExpanded)}>
            <Stack direction="row" alignItems="center" space="$xs">
              <Text variant="caption" color="primary">
                {isExpanded ? 'Hide' : 'Details'}
              </Text>
              <Lucide.ChevronDown 
                size={16} 
                color={colors.primary}
                style={{
                  transform: [{ rotate: isExpanded ? '180deg' : '0deg' }]
                }}
              />
            </Stack>
          </Pressable>
        )}
      </Stack>

      {/* Line items breakdown - collapsible */}
      {hasItems && isExpanded && (
        <Stack
          backgroundColor="$background"
          borderRadius="$md"
          padding="$md"
          space="$xs"
        >
          {displayLineItems.map((item) => (
            <LineItemRow key={item.id} item={item} />
          ))}
          
          {/* Subtotal if there are multiple items */}
          {displayLineItems.length > 1 && (
            <>
              <Stack
                height={1}
                backgroundColor="$border"
                marginVertical="$xs"
              />
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Text variant="body" weight="medium">
                  Total
                </Text>
                <Text variant="body" weight="bold">
                  {formatCurrency(displayTotal)}
                </Text>
              </Stack>
            </>
          )}
        </Stack>
      )}

      {/* Placeholder state when no data available */}
      {!hasItems && !showPlaceholder && (
        <Stack alignItems="center" padding="$md">
          <Lucide.DollarSign size={24} color={colors.textSecondary} />
          <Text variant="caption" color="textSecondary" align="center" marginTop="$sm">
            Cost breakdown will be available
            {'\n'}once job is created
          </Text>
        </Stack>
      )}

      {/* Placeholder notice */}
      {showPlaceholder && displayLineItems.length > 0 && lineItems.length === 0 && (
        <Caption color="textSecondary" align="center">
          * Sample data - actual costs will appear once job is processed
        </Caption>
      )}
    </Stack>
  )
}

export default JobCostBreakdown