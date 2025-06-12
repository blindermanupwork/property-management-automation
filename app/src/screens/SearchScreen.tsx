import React, { useState } from 'react'
import { Stack, ScrollView } from '@tamagui/core'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import { Lucide } from '@tamagui/lucide-icons'

import { Text, Heading } from '../design-system/components/atoms/Text/Text'
import { Button } from '../design-system/components/atoms/Button/Button'
import SearchInput from '../components/SearchInput'
import PropertySelection from '../components/PropertySelection'
import { colors, spacing } from '../design-system/tokens'
import { Property, SearchFilters } from '../types'

interface SearchScreenProps {
  onBack: () => void
  onApplyFilters: (filters: SearchFilters) => void
  onClearFilters: () => void
  properties: Property[]
  initialQuery?: string
  initialFilters?: Partial<SearchFilters>
  searchHistory?: string[]
  onSelectSearchHistory?: (search: string) => void
  onClearSearchHistory?: () => void
  loading?: boolean
}

interface DateRangePickerProps {
  startDate?: string
  endDate?: string
  onStartDateChange: (date: string) => void
  onEndDateChange: (date: string) => void
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange
}) => {
  const formatDisplayDate = (dateStr?: string) => {
    if (!dateStr) return 'Select date'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
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
        📅 Date Range
      </Text>
      
      <Stack direction="row" space="$sm">
        <Stack flex={1}>
          <Text variant="caption" color="textSecondary" marginBottom="$xs">
            From
          </Text>
          <Button
            variant="outline"
            size="md"
            onPress={() => {
              // Date picker implementation would go here
              // For now, using placeholder
              const today = new Date().toISOString().split('T')[0]
              onStartDateChange(today)
            }}
          >
            <Stack direction="row" alignItems="center" space="$sm">
              <Text variant="caption" color={startDate ? 'text' : 'textSecondary'}>
                {formatDisplayDate(startDate)}
              </Text>
              <Lucide.Calendar size={16} color={colors.textSecondary} />
            </Stack>
          </Button>
        </Stack>
        
        <Stack flex={1}>
          <Text variant="caption" color="textSecondary" marginBottom="$xs">
            To
          </Text>
          <Button
            variant="outline"
            size="md"
            onPress={() => {
              // Date picker implementation would go here
              // For now, using placeholder
              const nextWeek = new Date()
              nextWeek.setDate(nextWeek.getDate() + 7)
              onEndDateChange(nextWeek.toISOString().split('T')[0])
            }}
          >
            <Stack direction="row" alignItems="center" space="$sm">
              <Text variant="caption" color={endDate ? 'text' : 'textSecondary'}>
                {formatDisplayDate(endDate)}
              </Text>
              <Lucide.Calendar size={16} color={colors.textSecondary} />
            </Stack>
          </Button>
        </Stack>
      </Stack>
    </Stack>
  )
}

interface StatusFilterProps {
  selectedStatuses: string[]
  onStatusChange: (statuses: string[]) => void
}

const StatusFilter: React.FC<StatusFilterProps> = ({
  selectedStatuses,
  onStatusChange
}) => {
  const statusOptions = [
    { value: 'scheduled', label: 'Scheduled', icon: '🔵' },
    { value: 'in_progress', label: 'In Progress', icon: '🟡' },
    { value: 'completed', label: 'Completed', icon: '🟢' },
    { value: 'cancelled', label: 'Cancelled', icon: '🔴' },
  ]

  const toggleStatus = (status: string) => {
    if (selectedStatuses.includes(status)) {
      onStatusChange(selectedStatuses.filter(s => s !== status))
    } else {
      onStatusChange([...selectedStatuses, status])
    }
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
        🏷️ Status
      </Text>
      
      <Stack space="$sm">
        {statusOptions.map((option) => {
          const isSelected = selectedStatuses.includes(option.value)
          return (
            <Button
              key={option.value}
              variant={isSelected ? 'primary' : 'outline'}
              size="sm"
              onPress={() => toggleStatus(option.value)}
            >
              <Stack direction="row" alignItems="center" space="$sm" flex={1}>
                <Text variant="caption">{option.icon}</Text>
                <Text 
                  variant="caption" 
                  color={isSelected ? 'white' : 'text'}
                  weight="medium"
                >
                  {option.label}
                </Text>
                {isSelected && (
                  <Lucide.Check size={16} color={colors.white} />
                )}
              </Stack>
            </Button>
          )
        })}
      </Stack>
    </Stack>
  )
}

interface LocationFilterProps {
  selectedLocations: string[]
  onLocationChange: (locations: string[]) => void
  properties: Property[]
}

const LocationFilter: React.FC<LocationFilterProps> = ({
  selectedLocations,
  onLocationChange,
  properties
}) => {
  // Extract unique cities from properties
  const locations = Array.from(
    new Set(properties.map(p => `${p.address.city}, ${p.address.state}`))
  ).sort()

  const toggleLocation = (location: string) => {
    if (selectedLocations.includes(location)) {
      onLocationChange(selectedLocations.filter(l => l !== location))
    } else {
      onLocationChange([...selectedLocations, location])
    }
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
        📍 Location
      </Text>
      
      <Stack space="$sm" maxHeight={200}>
        <ScrollView>
          <Stack space="$xs">
            {locations.map((location) => {
              const isSelected = selectedLocations.includes(location)
              return (
                <Button
                  key={location}
                  variant={isSelected ? 'primary' : 'outline'}
                  size="sm"
                  onPress={() => toggleLocation(location)}
                >
                  <Stack direction="row" alignItems="center" space="$sm" flex={1}>
                    <Text 
                      variant="caption" 
                      color={isSelected ? 'white' : 'text'}
                      weight="medium"
                      flex={1}
                      align="left"
                    >
                      {location}
                    </Text>
                    {isSelected && (
                      <Lucide.Check size={16} color={colors.white} />
                    )}
                  </Stack>
                </Button>
              )
            })}
          </Stack>
        </ScrollView>
      </Stack>
    </Stack>
  )
}

export const SearchScreen: React.FC<SearchScreenProps> = ({
  onBack,
  onApplyFilters,
  onClearFilters,
  properties,
  initialQuery = '',
  initialFilters = {},
  searchHistory = [],
  onSelectSearchHistory,
  onClearSearchHistory,
  loading = false
}) => {
  const [searchQuery, setSearchQuery] = useState(initialQuery)
  const [propertyQuery, setPropertyQuery] = useState('')
  const [selectedProperties, setSelectedProperties] = useState<string[]>(
    initialFilters.propertyIds || []
  )
  const [dateRange, setDateRange] = useState({
    start: initialFilters.dateRange?.start,
    end: initialFilters.dateRange?.end
  })
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>(
    initialFilters.jobStatuses || []
  )
  const [selectedLocations, setSelectedLocations] = useState<string[]>(
    initialFilters.locations || []
  )

  const handleApplyFilters = () => {
    const filters: SearchFilters = {
      query: searchQuery,
      propertyIds: selectedProperties,
      dateRange,
      jobStatuses: selectedStatuses as any[],
      reservationStatuses: [],
      locations: selectedLocations,
      employeeIds: []
    }
    onApplyFilters(filters)
  }

  const handleClearAll = () => {
    setSearchQuery('')
    setPropertyQuery('')
    setSelectedProperties([])
    setDateRange({ start: undefined, end: undefined })
    setSelectedStatuses([])
    setSelectedLocations([])
    onClearFilters()
  }

  const hasActiveFilters = 
    searchQuery || 
    selectedProperties.length > 0 || 
    dateRange.start || 
    dateRange.end || 
    selectedStatuses.length > 0 || 
    selectedLocations.length > 0

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
          <Heading level={2}>Search & Filter</Heading>
        </Stack>
        
        <Button variant="ghost" size="sm" onPress={handleApplyFilters}>
          <Lucide.Check size={24} color={colors.primary} />
        </Button>
      </Stack>

      <ScrollView flex={1}>
        <Stack padding="$lg" space="$lg">
          {/* Main search input */}
          <SearchInput
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmit={() => {}}
            placeholder="Search properties, guests..."
            loading={loading}
            recentSearches={searchHistory}
            onSelectHistory={(search) => {
              setSearchQuery(search)
              onSelectSearchHistory?.(search)
            }}
            onClearHistory={onClearSearchHistory}
          />

          {/* Recent searches - matching wireframes.md */}
          {searchHistory.length > 0 && !searchQuery && (
            <Stack space="$sm">
              <Text variant="body" weight="medium">
                Recent Searches:
              </Text>
              <Stack direction="row" flexWrap="wrap" gap="$sm">
                {searchHistory.slice(0, 3).map((search, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onPress={() => setSearchQuery(search)}
                  >
                    <Text variant="caption" color="primary">
                      "{search}"
                    </Text>
                  </Button>
                ))}
              </Stack>
            </Stack>
          )}

          {/* Property selection - matching wireframes.md */}
          <PropertySelection
            searchQuery={propertyQuery}
            onSearchChange={setPropertyQuery}
            onSelectionChange={setSelectedProperties}
            properties={properties}
            selectedProperties={selectedProperties}
            loading={loading}
          />

          {/* Date range filter */}
          <DateRangePicker
            startDate={dateRange.start}
            endDate={dateRange.end}
            onStartDateChange={(date) => setDateRange(prev => ({ ...prev, start: date }))}
            onEndDateChange={(date) => setDateRange(prev => ({ ...prev, end: date }))}
          />

          {/* Status filter */}
          <StatusFilter
            selectedStatuses={selectedStatuses}
            onStatusChange={setSelectedStatuses}
          />

          {/* Location filter */}
          <LocationFilter
            selectedLocations={selectedLocations}
            onLocationChange={setSelectedLocations}
            properties={properties}
          />

          {/* Action buttons - matching wireframes.md */}
          <Stack direction="row" space="$md" marginTop="$lg">
            <Button
              variant="outline"
              onPress={handleClearAll}
              flex={1}
              disabled={!hasActiveFilters}
            >
              Clear All
            </Button>
            <Button
              variant="primary"
              onPress={handleApplyFilters}
              flex={1}
            >
              Apply Filters
            </Button>
          </Stack>
        </Stack>
      </ScrollView>
    </SafeAreaView>
  )
}

export default SearchScreen