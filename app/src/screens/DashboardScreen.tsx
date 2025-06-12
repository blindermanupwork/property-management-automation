import React, { useState, useEffect } from 'react'
import { Stack, ScrollView, RefreshControl } from '@tamagui/core'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import { Menu, Bell, User, Filter, Loader2, Home } from '@tamagui/lucide-icons'

import { Text, Heading } from '../design-system/components/atoms/Text/Text'
import { Button } from '../design-system/components/atoms/Button/Button'
import SearchInput from '../components/SearchInput'
import ReservationCard from '../components/ReservationCard'
import { colors, spacing } from '../design-system/tokens'
import { Reservation, SearchFilters } from '../types'

interface DashboardScreenProps {
  onSearch: (filters: SearchFilters) => void
  onReservationPress: (reservationId: string) => void
  onRequestAction: (reservationId: string, action: 'late-checkout' | 'custom-cleaning') => void
  onFilterPress: () => void
  onNotificationsPress: () => void
  onProfilePress: () => void
  reservations: Reservation[]
  loading?: boolean
  refreshing?: boolean
  onRefresh?: () => void
  searchHistory?: string[]
  onSelectSearchHistory?: (search: string) => void
  onClearSearchHistory?: () => void
}

interface FilterTabProps {
  label: string
  isActive: boolean
  onPress: () => void
  count?: number
}

const FilterTab: React.FC<FilterTabProps> = ({ label, isActive, onPress, count }) => (
  <Button
    variant={isActive ? 'primary' : 'ghost'}
    size="sm"
    onPress={onPress}
  >
    <Stack direction="row" alignItems="center" space="$xs">
      <Text 
        variant="caption" 
        color={isActive ? 'white' : 'textSecondary'}
        weight="medium"
      >
        {label}
      </Text>
      {count !== undefined && (
        <Stack
          backgroundColor={isActive ? 'rgba(255,255,255,0.3)' : colors.border}
          borderRadius="$full"
          paddingHorizontal="$xs"
          minWidth={20}
          height={20}
          alignItems="center"
          justifyContent="center"
        >
          <Text 
            variant="caption" 
            color={isActive ? 'white' : 'textSecondary'}
            weight="semibold"
            fontSize={10}
          >
            {count}
          </Text>
        </Stack>
      )}
    </Stack>
  </Button>
)

export const DashboardScreen: React.FC<DashboardScreenProps> = ({
  onSearch,
  onReservationPress,
  onRequestAction,
  onFilterPress,
  onNotificationsPress,
  onProfilePress,
  reservations,
  loading = false,
  refreshing = false,
  onRefresh,
  searchHistory = [],
  onSelectSearchHistory,
  onClearSearchHistory
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'scheduled' | 'done'>('all')

  // Filter reservations based on active filter
  const filteredReservations = reservations.filter(reservation => {
    switch (activeFilter) {
      case 'active':
        return reservation.status === 'confirmed' || reservation.status === 'checked_in'
      case 'scheduled':
        return reservation.job?.workStatus === 'scheduled' || reservation.job?.workStatus === 'in_progress'
      case 'done':
        return reservation.job?.workStatus === 'completed' || reservation.status === 'checked_out'
      default:
        return true
    }
  })

  // Search within filtered reservations
  const searchResults = searchQuery.trim() 
    ? filteredReservations.filter(reservation =>
        reservation.property.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        reservation.guest.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        reservation.property.address.city.toLowerCase().includes(searchQuery.toLowerCase()) ||
        reservation.property.address.state.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : filteredReservations

  // Calculate counts for filter tabs
  const filterCounts = {
    all: reservations.length,
    active: reservations.filter(r => r.status === 'confirmed' || r.status === 'checked_in').length,
    scheduled: reservations.filter(r => r.job?.workStatus === 'scheduled' || r.job?.workStatus === 'in_progress').length,
    done: reservations.filter(r => r.job?.workStatus === 'completed' || r.status === 'checked_out').length,
  }

  const handleSearch = () => {
    const filters: SearchFilters = {
      query: searchQuery,
      propertyIds: [],
      dateRange: {},
      jobStatuses: [],
      reservationStatuses: [],
      locations: [],
      employeeIds: []
    }
    onSearch(filters)
  }

  const handleSearchHistorySelect = (search: string) => {
    setSearchQuery(search)
    onSelectSearchHistory?.(search)
  }

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
        {/* Hamburger menu and title */}
        <Stack direction="row" alignItems="center" space="$md" flex={1}>
          <Button variant="ghost" size="sm" onPress={() => {}}>
            <Menu size={24} color={colors.text} />
          </Button>
          <Heading level={2}>Properties & Jobs</Heading>
        </Stack>
        
        {/* Notifications and profile */}
        <Stack direction="row" alignItems="center" space="$sm">
          <Button variant="ghost" size="sm" onPress={onNotificationsPress}>
            <Bell size={24} color={colors.text} />
          </Button>
          <Button variant="ghost" size="sm" onPress={onProfilePress}>
            <User size={24} color={colors.text} />
          </Button>
        </Stack>
      </Stack>

      <ScrollView
        flex={1}
        refreshControl={
          onRefresh ? (
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.primary}
            />
          ) : undefined
        }
      >
        <Stack padding="$lg" space="$lg">
          {/* Search input - matching wireframes.md */}
          <Stack direction="row" alignItems="center" space="$sm">
            <Stack flex={1}>
              <SearchInput
                value={searchQuery}
                onChangeText={setSearchQuery}
                onSubmit={handleSearch}
                placeholder="Search properties..."
                loading={loading}
                recentSearches={searchHistory}
                onSelectHistory={handleSearchHistorySelect}
                onClearHistory={onClearSearchHistory}
              />
            </Stack>
            <Button variant="outline" size="md" onPress={onFilterPress}>
              <Filter size={20} color={colors.primary} />
            </Button>
          </Stack>

          {/* Filter tabs - matching wireframes.md */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <Stack direction="row" space="$sm" paddingHorizontal="$xs">
              <FilterTab
                label="All"
                isActive={activeFilter === 'all'}
                onPress={() => setActiveFilter('all')}
                count={filterCounts.all}
              />
              <FilterTab
                label="Active"
                isActive={activeFilter === 'active'}
                onPress={() => setActiveFilter('active')}
                count={filterCounts.active}
              />
              <FilterTab
                label="Scheduled"
                isActive={activeFilter === 'scheduled'}
                onPress={() => setActiveFilter('scheduled')}
                count={filterCounts.scheduled}
              />
              <FilterTab
                label="Done"
                isActive={activeFilter === 'done'}
                onPress={() => setActiveFilter('done')}
                count={filterCounts.done}
              />
            </Stack>
          </ScrollView>

          {/* Results count */}
          {searchQuery && (
            <Text variant="caption" color="textSecondary">
              {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
            </Text>
          )}

          {/* Reservation list */}
          {loading && reservations.length === 0 ? (
            <Stack alignItems="center" paddingVertical="$xxl">
              <Loader2 size={32} color={colors.primary} />
              <Text variant="body" color="textSecondary" marginTop="$md">
                Loading reservations...
              </Text>
            </Stack>
          ) : searchResults.length > 0 ? (
            <Stack space="$md">
              {searchResults.map((reservation) => (
                <ReservationCard
                  key={reservation.id}
                  reservation={reservation}
                  onPress={() => onReservationPress(reservation.id)}
                  onRequestAction={(action) => onRequestAction(reservation.id, action)}
                  variant="default"
                />
              ))}
            </Stack>
          ) : (
            <Stack alignItems="center" paddingVertical="$xxl">
              <Home size={48} color={colors.textSecondary} />
              <Heading level={3} color="textSecondary" marginTop="$md">
                {searchQuery ? 'No results found' : 'No reservations'}
              </Heading>
              <Text variant="body" color="textSecondary" align="center" marginTop="$sm">
                {searchQuery 
                  ? `Try adjusting your search terms or filters`
                  : 'Reservations will appear here when available'
                }
              </Text>
              {searchQuery && (
                <Button
                  variant="outline"
                  size="sm"
                  onPress={() => setSearchQuery('')}
                  marginTop="$md"
                >
                  Clear search
                </Button>
              )}
            </Stack>
          )}
        </Stack>
      </ScrollView>
    </SafeAreaView>
  )
}

export default DashboardScreen