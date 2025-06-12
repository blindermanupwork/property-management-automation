import React, { useState } from 'react'
import { Stack, Pressable, ScrollView } from '@tamagui/core'
import { Lucide } from '@tamagui/lucide-icons'

import { Input } from '../design-system/components/atoms/Input/Input'
import { Text, Caption } from '../design-system/components/atoms/Text/Text'
import { Button } from '../design-system/components/atoms/Button/Button'
import { colors, spacing } from '../design-system/tokens'
import { Property } from '../types'

interface PropertySelectionProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  onSelectionChange: (selectedProperties: string[]) => void
  properties: Property[]
  selectedProperties: string[]
  maxVisible?: number
  loading?: boolean
}

interface PropertyCheckboxProps {
  property: Property
  isSelected: boolean
  onToggle: (propertyId: string) => void
}

const PropertyCheckbox: React.FC<PropertyCheckboxProps> = ({
  property,
  isSelected,
  onToggle
}) => {
  return (
    <Pressable
      onPress={() => onToggle(property.id)}
      style={{
        paddingVertical: spacing.sm,
        paddingHorizontal: spacing.sm,
        borderRadius: spacing.xs,
      }}
    >
      <Stack direction="row" alignItems="center" space="$sm">
        {/* Checkbox - following wireframes.md design */}
        <Stack
          width={20}
          height={20}
          borderRadius="$xs"
          borderWidth={2}
          borderColor={isSelected ? colors.primary : colors.border}
          backgroundColor={isSelected ? colors.primary : 'transparent'}
          alignItems="center"
          justifyContent="center"
        >
          {isSelected && (
            <Lucide.Check size={12} color={colors.white} />
          )}
        </Stack>
        
        {/* Property info */}
        <Stack flex={1}>
          <Text variant="body" weight="medium">
            {property.name}
          </Text>
          <Caption>
            {property.address.city}, {property.address.state}
          </Caption>
        </Stack>
      </Stack>
    </Pressable>
  )
}

export const PropertySelection: React.FC<PropertySelectionProps> = ({
  searchQuery,
  onSearchChange,
  onSelectionChange,
  properties,
  selectedProperties,
  maxVisible = 6,
  loading = false
}) => {
  const [showAll, setShowAll] = useState(false)
  
  const filteredProperties = properties.filter(property =>
    property.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    property.address.city.toLowerCase().includes(searchQuery.toLowerCase()) ||
    property.address.state.toLowerCase().includes(searchQuery.toLowerCase())
  )
  
  const visibleProperties = showAll 
    ? filteredProperties 
    : filteredProperties.slice(0, maxVisible)
  
  const hasMore = filteredProperties.length > maxVisible && !showAll

  const handleToggleProperty = (propertyId: string) => {
    if (selectedProperties.includes(propertyId)) {
      onSelectionChange(selectedProperties.filter(id => id !== propertyId))
    } else {
      onSelectionChange([...selectedProperties, propertyId])
    }
  }

  const handleSelectAll = () => {
    const allIds = filteredProperties.map(p => p.id)
    onSelectionChange(allIds)
  }

  const handleClearAll = () => {
    onSelectionChange([])
  }

  const clearSearchButton = searchQuery.length > 0 ? (
    <Pressable onPress={() => onSearchChange('')}>
      <Lucide.X size={16} color={colors.textSecondary} />
    </Pressable>
  ) : null

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
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Text variant="body" weight="medium">
          🏠 Property Selection
        </Text>
        {selectedProperties.length > 0 && (
          <Caption>
            Selected: {selectedProperties.length} of {filteredProperties.length}
          </Caption>
        )}
      </Stack>

      {/* Property search input - following wireframes.md */}
      <Input
        value={searchQuery}
        onChangeText={onSearchChange}
        placeholder="Search properties..."
        leftIcon={<Lucide.Search size={16} color={colors.textSecondary} />}
        rightIcon={clearSearchButton}
        size="md"
      />

      {/* Results summary */}
      {searchQuery && (
        <Text variant="caption" color="textSecondary">
          {loading 
            ? 'Searching...' 
            : `Search Results (${filteredProperties.length} properties):`
          }
        </Text>
      )}

      {/* Selection controls */}
      {filteredProperties.length > 0 && (
        <Stack direction="row" space="$sm">
          <Button
            variant="ghost"
            size="sm"
            onPress={handleSelectAll}
            disabled={selectedProperties.length === filteredProperties.length}
          >
            Select All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onPress={handleClearAll}
            disabled={selectedProperties.length === 0}
          >
            Clear All
          </Button>
        </Stack>
      )}

      {/* Property list with checkboxes - matching wireframes.md */}
      {filteredProperties.length > 0 ? (
        <Stack>
          <ScrollView maxHeight={240}>
            <Stack space="$xs">
              {visibleProperties.map((property) => (
                <PropertyCheckbox
                  key={property.id}
                  property={property}
                  isSelected={selectedProperties.includes(property.id)}
                  onToggle={handleToggleProperty}
                />
              ))}
            </Stack>
          </ScrollView>
          
          {/* Show more button */}
          {hasMore && (
            <Stack marginTop="$sm" alignItems="center">
              <Button
                variant="ghost"
                size="sm"
                onPress={() => setShowAll(true)}
              >
                <Stack direction="row" alignItems="center" space="$xs">
                  <Text variant="caption" color="primary">
                    Show {filteredProperties.length - maxVisible} more
                  </Text>
                  <Lucide.ChevronDown size={16} color={colors.primary} />
                </Stack>
              </Button>
            </Stack>
          )}
        </Stack>
      ) : (
        <Stack alignItems="center" padding="$lg">
          <Lucide.Home size={24} color={colors.textSecondary} />
          <Text variant="caption" color="textSecondary" align="center" marginTop="$sm">
            {searchQuery 
              ? `No properties found for "${searchQuery}"`
              : 'No properties available'
            }
          </Text>
        </Stack>
      )}
    </Stack>
  )
}

export default PropertySelection