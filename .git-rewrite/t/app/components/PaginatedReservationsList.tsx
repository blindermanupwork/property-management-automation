import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { View, Text, TouchableOpacity, FlatList, ActivityIndicator, TextInput, Alert, Keyboard, Linking } from 'react-native'
import ApiService from '../services/api'

const INITIAL_LOAD = 30   // Enough to fill screen and prevent auto-trigger
const ITEMS_PER_PAGE = 30 // Items to add per load more action

interface Reservation {
  id: string
  guest: string
  property: string
  checkin: string
  checkout: string
  status: string
  jobType: string
  totalCost: number
  employeeAssigned?: string
  hcpJobId?: string
  hcpJobLink?: string
  airtableLink?: string
}

interface Props {
  reservations?: Reservation[]  // Optional - if provided, use these instead of loading
  userEmail?: string | null
  onReservationPress: (reservation: Reservation) => void
  onCreateJob?: (reservation: Reservation) => void
  navigation?: any
}

// Reservation Card Component
function ReservationCard({ reservation, onPress, onCreateJob }) {
  const getStatusColor = (status) => {
    switch(status) {
      case 'scheduled': return '#0066cc'
      case 'in_progress': return '#f59e0b' 
      case 'completed': return '#22c55e'
      default: return '#666'
    }
  }

  return (
    <View
      style={{
        backgroundColor: 'white',
        borderRadius: 8,
        padding: 15,
        marginBottom: 10,
        marginHorizontal: 15,
        borderWidth: 1,
        borderColor: '#e2e8f0',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2
      }}
    >
      <TouchableOpacity onPress={() => onPress(reservation)}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
          <Text style={{ fontSize: 16, fontWeight: 'bold', color: 'black', flex: 1 }}>
            {reservation.guest}
          </Text>
          <View style={{ 
            backgroundColor: getStatusColor(reservation.status), 
            paddingHorizontal: 8, 
            paddingVertical: 4, 
            borderRadius: 4 
          }}>
            <Text style={{ color: 'white', fontSize: 12, fontWeight: 'bold' }}>
              {reservation.status.toUpperCase()}
            </Text>
          </View>
        </View>
        
        <Text style={{ fontSize: 14, color: '#666', marginBottom: 4 }}>
          📍 {reservation.property}
        </Text>
        <Text style={{ fontSize: 14, color: '#666', marginBottom: 4 }}>
          📅 {reservation.checkin} → {reservation.checkout}
        </Text>
        <Text style={{ fontSize: 14, color: '#666', marginBottom: 8 }}>
          🧹 {reservation.jobType}
        </Text>
        
        {reservation.employeeAssigned && (
          <Text style={{ fontSize: 14, color: '#0066cc', marginBottom: 4 }}>
            👤 Assigned: {reservation.employeeAssigned}
          </Text>
        )}
        
        {reservation.hcpJobId && (
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
            <Text style={{ fontSize: 12, color: '#22c55e', flex: 1 }}>
              ✅ HCP Job: {reservation.hcpJobId}
            </Text>
            <TouchableOpacity
              style={{ backgroundColor: '#22c55e', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 }}
              onPress={async () => {
                try {
                  const hcpUrl = `https://pro.housecallpro.com/app/jobs/job_${reservation.hcpJobId}`
                  const canOpen = await Linking.canOpenURL(hcpUrl)
                  if (canOpen) {
                    await Linking.openURL(hcpUrl)
                  } else {
                    Alert.alert('Error', 'Cannot open HousecallPro link')
                  }
                } catch (error) {
                  console.error('Error opening HCP link:', error)
                  Alert.alert('Error', 'Failed to open HousecallPro link')
                }
              }}
            >
              <Text style={{ color: 'white', fontSize: 10, fontWeight: 'bold' }}>
                🔗 Open HCP
              </Text>
            </TouchableOpacity>
          </View>
        )}
        
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <Text style={{ fontSize: 16, fontWeight: 'bold', color: '#22c55e' }}>
            ${reservation.totalCost.toFixed(2)}
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            {(reservation.airtableLink || reservation.id) && (
              <TouchableOpacity
                style={{ backgroundColor: '#f59e0b', paddingHorizontal: 6, paddingVertical: 3, borderRadius: 3, marginRight: 8 }}
                onPress={async () => {
                  try {
                    // Use existing airtableLink if it's a full URL, otherwise construct it
                    let airtableUrl = reservation.airtableLink
                    if (!airtableUrl || !airtableUrl.startsWith('http')) {
                      // Construct URL using the pattern and reservation ID (assuming it's the Airtable record ID)
                      const recordId = reservation.airtableLink || reservation.id
                      airtableUrl = `https://airtable.com/app67yWFv0hKdl6jM/tblaPnk0jxF47xWhL/viwWTLyEy2oYiTqvS/${recordId}`
                    }
                    
                    const canOpen = await Linking.canOpenURL(airtableUrl)
                    if (canOpen) {
                      await Linking.openURL(airtableUrl)
                    } else {
                      Alert.alert('Error', 'Cannot open Airtable link')
                    }
                  } catch (error) {
                    console.error('Error opening Airtable link:', error)
                    Alert.alert('Error', 'Failed to open Airtable link')
                  }
                }}
              >
                <Text style={{ color: 'white', fontSize: 9, fontWeight: 'bold' }}>
                  📊 Airtable
                </Text>
              </TouchableOpacity>
            )}
            <Text style={{ fontSize: 12, color: '#0066cc' }}>
              Tap to view details →
            </Text>
          </View>
        </View>
      </TouchableOpacity>
      
      {/* Action Buttons */}
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 }}>
        {!reservation.hcpJobId && onCreateJob && (
          <TouchableOpacity
            style={{ backgroundColor: '#22c55e', padding: 10, borderRadius: 6, flex: 1, marginRight: 5 }}
            onPress={() => onCreateJob(reservation)}
          >
            <Text style={{ color: 'white', textAlign: 'center', fontSize: 12, fontWeight: 'bold' }}>
              📋 Create Job
            </Text>
          </TouchableOpacity>
        )}
        
        {reservation.hcpJobId && (
          <TouchableOpacity
            style={{ backgroundColor: '#f59e0b', padding: 10, borderRadius: 6, flex: 1, marginRight: 5 }}
            onPress={() => Alert.alert('Schedule Update', 'Schedule update functionality will be implemented.')}
          >
            <Text style={{ color: 'white', textAlign: 'center', fontSize: 12, fontWeight: 'bold' }}>
              📅 Update Schedule
            </Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity
          style={{ backgroundColor: '#8b5cf6', padding: 10, borderRadius: 6, flex: 1, marginLeft: 5 }}
          onPress={() => Alert.alert('Request', 'Request functionality (late checkout, custom cleaning) will be implemented.')}
        >
          <Text style={{ color: 'white', textAlign: 'center', fontSize: 12, fontWeight: 'bold' }}>
            📝 Request
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  )
}

export default function PaginatedReservationsList({ reservations: providedReservations, userEmail, onReservationPress, onCreateJob }: Props) {
  const [allReservations, setAllReservations] = useState<Reservation[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadedItemsCount, setLoadedItemsCount] = useState(INITIAL_LOAD)
  
  // Filter states
  const [selectedDateRange, setSelectedDateRange] = useState('all') // 'today', '7days', '30days', '60days', 'eoy', 'custom', 'all'
  const [customDateStart, setCustomDateStart] = useState('')
  const [customDateEnd, setCustomDateEnd] = useState('')
  const [selectedProperties, setSelectedProperties] = useState<string[]>([])
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)
  
  // Refs for state persistence, debouncing, and maintaining focus
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const searchInputRef = useRef<TextInput>(null)
  const currentInputValueRef = useRef('') // Track current input value without causing re-renders
  const persistedStateRef = useRef({
    loadedItemsCount: INITIAL_LOAD,
    searchQuery: '',
    selectedDateRange: 'all',
    selectedProperties: [] as string[],
    selectedStatuses: [] as string[]
  })

  // Date range calculation helpers
  const getDateRangeFilter = useCallback((range: string) => {
    const today = new Date()
    const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate())
    
    switch (range) {
      case 'today':
        return {
          start: startOfToday,
          end: new Date(startOfToday.getTime() + 24 * 60 * 60 * 1000 - 1)
        }
      case '7days':
        return {
          start: startOfToday,
          end: new Date(startOfToday.getTime() + 7 * 24 * 60 * 60 * 1000 - 1)
        }
      case '30days':
        return {
          start: startOfToday,
          end: new Date(startOfToday.getTime() + 30 * 24 * 60 * 60 * 1000 - 1)
        }
      case '60days':
        return {
          start: startOfToday,
          end: new Date(startOfToday.getTime() + 60 * 24 * 60 * 60 * 1000 - 1)
        }
      case 'eoy':
        return {
          start: startOfToday,
          end: new Date(today.getFullYear(), 11, 31, 23, 59, 59)
        }
      case 'custom':
        return {
          start: customDateStart ? new Date(customDateStart) : null,
          end: customDateEnd ? new Date(customDateEnd) : null
        }
      default:
        return { start: null, end: null }
    }
  }, [customDateStart, customDateEnd])

  // Extract unique properties and statuses
  const uniqueProperties = useMemo(() => {
    const properties = new Set<string>()
    allReservations.forEach(res => {
      if (res.property) properties.add(res.property)
    })
    return Array.from(properties).sort()
  }, [allReservations])

  const uniqueStatuses = useMemo(() => {
    const statuses = new Set<string>()
    allReservations.forEach(res => {
      if (res.status) statuses.add(res.status)
    })
    return Array.from(statuses).sort()
  }, [allReservations])

  // Debounced search function
  const debouncedSearch = useCallback((query: string) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      setSearchQuery(query)
      // Reset pagination when search changes
      if (query !== persistedStateRef.current.searchQuery) {
        setLoadedItemsCount(INITIAL_LOAD)
        persistedStateRef.current.loadedItemsCount = INITIAL_LOAD
      }
      persistedStateRef.current.searchQuery = query
    }, 300) // 300ms debounce
  }, [])

  // Handle search input change without causing re-renders that lose focus
  const handleSearchChange = useCallback((query: string) => {
    // Store current input value in ref (no re-render)
    currentInputValueRef.current = query
    
    // Debounce the actual search state update
    debouncedSearch(query)
  }, [debouncedSearch])

  useEffect(() => {
    if (providedReservations) {
      // Use provided reservations (faster, no API call needed)
      console.log(`✅ Using provided ${providedReservations.length} reservations for pagination`)
      setAllReservations(providedReservations)
      setLoading(false)
      
      // Restore persisted state if available
      setLoadedItemsCount(persistedStateRef.current.loadedItemsCount)
      setSearchQuery(persistedStateRef.current.searchQuery)
      currentInputValueRef.current = persistedStateRef.current.searchQuery
    } else {
      // Load from API
      loadAllReservations()
    }
  }, [providedReservations])

  const loadAllReservations = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔄 Loading ALL reservations for smart filtering...')
      
      let data: Reservation[]
      if (userEmail) {
        // Load user-specific reservations
        data = await ApiService.searchProperties('', userEmail)
      } else {
        // Load all reservations
        data = await ApiService.getReservations()
      }
      
      console.log(`✅ Loaded ${data.length} reservations total`)
      setAllReservations(data)
      setLoadedItemsCount(INITIAL_LOAD) // Reset to initial load
      setHasTriggeredInitial(false) // Reset trigger guard
      
    } catch (err) {
      console.error('Failed to load reservations:', err)
      setError(err.message || 'Failed to load reservations')
      setAllReservations([])
    } finally {
      setLoading(false)
    }
  }

  // Comprehensive filtering including search, date range, properties, and status
  const filteredReservations = useMemo(() => {
    let filtered = [...allReservations]

    // Apply search query filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(reservation =>
        reservation.guest.toLowerCase().includes(query) ||
        reservation.property.toLowerCase().includes(query) ||
        reservation.jobType.toLowerCase().includes(query) ||
        reservation.id.toLowerCase().includes(query) ||
        reservation.reservationUID?.toLowerCase().includes(query) ||
        reservation.entrySource?.toLowerCase().includes(query) ||
        (reservation.employeeAssigned && reservation.employeeAssigned.toLowerCase().includes(query))
      )
    }

    // Apply date range filter
    if (selectedDateRange !== 'all') {
      const dateFilter = getDateRangeFilter(selectedDateRange)
      if (dateFilter.start || dateFilter.end) {
        filtered = filtered.filter(reservation => {
          // Parse reservation dates (assuming checkInDate and checkOutDate exist)
          const checkIn = reservation.checkInDate ? new Date(reservation.checkInDate) : null
          const checkOut = reservation.checkOutDate ? new Date(reservation.checkOutDate) : null
          const jobDate = reservation.scheduledDate ? new Date(reservation.scheduledDate) : null
          
          // Use job date primarily, fallback to check-in date
          const relevantDate = jobDate || checkIn
          if (!relevantDate) return false

          if (dateFilter.start && relevantDate < dateFilter.start) return false
          if (dateFilter.end && relevantDate > dateFilter.end) return false
          return true
        })
      }
    }

    // Apply property filter
    if (selectedProperties.length > 0) {
      filtered = filtered.filter(reservation =>
        selectedProperties.includes(reservation.property)
      )
    }

    // Apply status filter
    if (selectedStatuses.length > 0) {
      filtered = filtered.filter(reservation =>
        selectedStatuses.includes(reservation.status)
      )
    }

    return filtered
  }, [allReservations, searchQuery, selectedDateRange, selectedProperties, selectedStatuses, getDateRangeFilter])

  // Paginated data for display (only show loaded items count)
  const displayedReservations = useMemo(() => {
    return filteredReservations.slice(0, loadedItemsCount)
  }, [filteredReservations, loadedItemsCount])

  const handleLoadMore = useCallback(() => {
    // Only load more if:
    // 1. Not already loading
    // 2. There are more items to load
    if (loadingMore || displayedReservations.length >= filteredReservations.length) {
      return
    }

    console.log(`🔄 Manual load more... Currently showing ${displayedReservations.length} of ${filteredReservations.length}`)
    
    setLoadingMore(true)
    // Simulate brief loading delay for smooth UX
    setTimeout(() => {
      const newCount = loadedItemsCount + ITEMS_PER_PAGE
      setLoadedItemsCount(newCount)
      persistedStateRef.current.loadedItemsCount = newCount // Persist the count
      setLoadingMore(false)
      console.log(`✅ Manual load: ${ITEMS_PER_PAGE} more items (30 additional reservations)`)
    }, 500)
  }, [loadingMore, displayedReservations.length, filteredReservations.length, loadedItemsCount])

  const clearSearch = useCallback(() => {
    // Clear search but keep keyboard open and focused
    setSearchQuery('')
    setLoadedItemsCount(INITIAL_LOAD)
    
    // Update refs
    currentInputValueRef.current = ''
    persistedStateRef.current.searchQuery = ''
    persistedStateRef.current.loadedItemsCount = INITIAL_LOAD
    
    // Clear any pending debounce
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    
    // Clear the input manually and maintain focus
    if (searchInputRef.current) {
      searchInputRef.current.clear()
      // Use requestAnimationFrame for better focus timing
      requestAnimationFrame(() => {
        searchInputRef.current?.focus()
      })
    }
  }, [])

  const renderItem = ({ item }: { item: Reservation }) => (
    <ReservationCard
      reservation={item}
      onPress={onReservationPress}
      onCreateJob={onCreateJob}
    />
  )

  const renderFooter = () => {
    if (!loadingMore) {
      // Show load more button if there are more items
      if (displayedReservations.length < filteredReservations.length) {
        return (
          <View style={{ padding: 20, alignItems: 'center' }}>
            <TouchableOpacity
              style={{
                backgroundColor: '#0066cc',
                paddingHorizontal: 30,
                paddingVertical: 15,
                borderRadius: 8,
                minWidth: 200
              }}
              onPress={handleLoadMore}
            >
              <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
                📥 Load 30 More ({filteredReservations.length - displayedReservations.length} remaining)
              </Text>
            </TouchableOpacity>
            <Text style={{ color: 'gray', fontSize: 12, marginTop: 10 }}>
              Showing {displayedReservations.length} of {filteredReservations.length} reservations
            </Text>
          </View>
        )
      } else if (displayedReservations.length > 0) {
        return (
          <View style={{ padding: 20, alignItems: 'center' }}>
            <Text style={{ color: 'gray', fontSize: 14, textAlign: 'center' }}>
              ✅ All {filteredReservations.length} reservations loaded
            </Text>
          </View>
        )
      }
      return null
    }

    return (
      <View style={{ padding: 20, alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#0066cc" />
        <Text style={{ color: 'gray', marginTop: 10, fontSize: 16 }}>📥 Loading more reservations...</Text>
      </View>
    )
  }

  const renderHeader = () => (
    <View style={{ paddingHorizontal: 16, paddingTop: 20, backgroundColor: '#f8fafc' }}>
      {/* Main Title - Bigger and Unified */}
      <View style={{ marginBottom: 24 }}>
        <Text style={{ fontSize: 28, fontWeight: 'bold', color: '#1e293b', marginBottom: 8 }}>
          Property Reservations
        </Text>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ fontSize: 16, color: '#64748b' }}>
            {filteredReservations.length} reservations • Showing {displayedReservations.length}
          </Text>
          <TouchableOpacity
            onPress={() => setShowFilters(!showFilters)}
            style={{
              backgroundColor: showFilters ? '#0066cc' : '#e2e8f0',
              paddingHorizontal: 16,
              paddingVertical: 10,
              borderRadius: 8,
              flexDirection: 'row',
              alignItems: 'center'
            }}
          >
            <Text style={{ 
              color: showFilters ? 'white' : '#475569', 
              fontSize: 16, 
              fontWeight: '600',
              marginRight: 6
            }}>
              {showFilters ? 'Hide' : 'Show'} Filters
            </Text>
            <Text style={{ color: showFilters ? 'white' : '#475569', fontSize: 16 }}>
              {showFilters ? '🔽' : '🔧'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Enhanced Search Input */}
      <View style={{ position: 'relative', marginBottom: showFilters ? 20 : 15 }}>
        <TextInput
          ref={searchInputRef}
          style={{
            borderWidth: 2,
            borderColor: searchQuery ? '#0066cc' : '#e2e8f0',
            borderRadius: 12,
            paddingHorizontal: 18,
            paddingVertical: 16,
            paddingRight: searchQuery ? 54 : 18,
            fontSize: 18,
            backgroundColor: 'white',
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.1,
            shadowRadius: 4,
            elevation: 2
          }}
          placeholder="🔍 Search reservations, guests, properties..."
          placeholderTextColor="#94a3b8"
          defaultValue={persistedStateRef.current.searchQuery}
          onChangeText={handleSearchChange}
          autoCapitalize="none"
          autoCorrect={false}
          blurOnSubmit={false}
          returnKeyType="search"
          clearButtonMode="never"
          selectTextOnFocus={false}
        />
        
        {/* Clear Search Button */}
        {searchQuery.length > 0 && (
          <TouchableOpacity
            style={{
              position: 'absolute',
              right: 12,
              top: '50%',
              transform: [{ translateY: -12 }],
              backgroundColor: '#64748b',
              width: 24,
              height: 24,
              borderRadius: 12,
              justifyContent: 'center',
              alignItems: 'center',
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 1 },
              shadowOpacity: 0.2,
              shadowRadius: 2,
              elevation: 2
            }}
            onPress={clearSearch}
            activeOpacity={0.8}
          >
            <View style={{
              width: 10,
              height: 10,
              justifyContent: 'center',
              alignItems: 'center'
            }}>
              <View style={{
                position: 'absolute',
                width: 12,
                height: 1.5,
                backgroundColor: 'white',
                transform: [{ rotate: '45deg' }]
              }} />
              <View style={{
                position: 'absolute',
                width: 12,
                height: 1.5,
                backgroundColor: 'white',
                transform: [{ rotate: '-45deg' }]
              }} />
            </View>
          </TouchableOpacity>
        )}
      </View>

      {/* Comprehensive Filters Panel */}
      {showFilters && (
        <View style={{ 
          backgroundColor: 'white', 
          borderRadius: 16, 
          padding: 20, 
          marginBottom: 20,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.1,
          shadowRadius: 8,
          elevation: 4
        }}>
          {/* Date Range Filters */}
          <View style={{ marginBottom: 20 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#1e293b', marginBottom: 12 }}>
              📅 Date Range
            </Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
              {[
                { key: 'all', label: 'All Time' },
                { key: 'today', label: 'Today' },
                { key: '7days', label: 'Next 7 Days' },
                { key: '30days', label: 'Next 30 Days' },
                { key: '60days', label: 'Next 60 Days' },
                { key: 'eoy', label: 'End of Year' }
              ].map(range => (
                <TouchableOpacity
                  key={range.key}
                  onPress={() => setSelectedDateRange(range.key)}
                  style={{
                    backgroundColor: selectedDateRange === range.key ? '#0066cc' : '#f1f5f9',
                    paddingHorizontal: 16,
                    paddingVertical: 10,
                    borderRadius: 8,
                    borderWidth: 1,
                    borderColor: selectedDateRange === range.key ? '#0066cc' : '#e2e8f0'
                  }}
                >
                  <Text style={{
                    color: selectedDateRange === range.key ? 'white' : '#475569',
                    fontSize: 16,
                    fontWeight: '600'
                  }}>
                    {range.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Property Filter */}
          <View style={{ marginBottom: 20 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#1e293b', marginBottom: 12 }}>
              🏠 Properties ({selectedProperties.length}/{uniqueProperties.length})
            </Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
              {uniqueProperties.slice(0, 6).map(property => (
                <TouchableOpacity
                  key={property}
                  onPress={() => {
                    if (selectedProperties.includes(property)) {
                      setSelectedProperties(prev => prev.filter(p => p !== property))
                    } else {
                      setSelectedProperties(prev => [...prev, property])
                    }
                  }}
                  style={{
                    backgroundColor: selectedProperties.includes(property) ? '#22c55e' : '#f1f5f9',
                    paddingHorizontal: 14,
                    paddingVertical: 8,
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: selectedProperties.includes(property) ? '#22c55e' : '#e2e8f0'
                  }}
                >
                  <Text style={{
                    color: selectedProperties.includes(property) ? 'white' : '#475569',
                    fontSize: 14,
                    fontWeight: '600'
                  }}>
                    {property.length > 20 ? property.substring(0, 20) + '...' : property}
                  </Text>
                </TouchableOpacity>
              ))}
              {uniqueProperties.length > 6 && (
                <TouchableOpacity
                  style={{
                    backgroundColor: '#f97316',
                    paddingHorizontal: 14,
                    paddingVertical: 8,
                    borderRadius: 6
                  }}
                >
                  <Text style={{ color: 'white', fontSize: 14, fontWeight: '600' }}>
                    +{uniqueProperties.length - 6} more
                  </Text>
                </TouchableOpacity>
              )}
            </View>
            {selectedProperties.length > 0 && (
              <TouchableOpacity
                onPress={() => setSelectedProperties([])}
                style={{ marginTop: 8 }}
              >
                <Text style={{ color: '#ef4444', fontSize: 14, fontWeight: '600' }}>
                  Clear All Properties
                </Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Status Filter */}
          <View>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#1e293b', marginBottom: 12 }}>
              📊 Status ({selectedStatuses.length}/{uniqueStatuses.length})
            </Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
              {uniqueStatuses.map(status => (
                <TouchableOpacity
                  key={status}
                  onPress={() => {
                    if (selectedStatuses.includes(status)) {
                      setSelectedStatuses(prev => prev.filter(s => s !== status))
                    } else {
                      setSelectedStatuses(prev => [...prev, status])
                    }
                  }}
                  style={{
                    backgroundColor: selectedStatuses.includes(status) ? '#8b5cf6' : '#f1f5f9',
                    paddingHorizontal: 14,
                    paddingVertical: 8,
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: selectedStatuses.includes(status) ? '#8b5cf6' : '#e2e8f0'
                  }}
                >
                  <Text style={{
                    color: selectedStatuses.includes(status) ? 'white' : '#475569',
                    fontSize: 14,
                    fontWeight: '600'
                  }}>
                    {status}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            {selectedStatuses.length > 0 && (
              <TouchableOpacity
                onPress={() => setSelectedStatuses([])}
                style={{ marginTop: 8 }}
              >
                <Text style={{ color: '#ef4444', fontSize: 14, fontWeight: '600' }}>
                  Clear All Statuses
                </Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      )}

      {userEmail && (
        <View style={{ 
          backgroundColor: '#eff6ff', 
          padding: 12, 
          borderRadius: 8, 
          marginBottom: 15,
          borderLeftWidth: 4,
          borderLeftColor: '#0066cc'
        }}>
          <Text style={{ fontSize: 14, color: '#0066cc', fontWeight: 'bold' }}>
            📧 Filtered for: {userEmail}
          </Text>
        </View>
      )}
    </View>
  )

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8fafc' }}>
        <ActivityIndicator size="large" color="#0066cc" />
        <Text style={{ color: 'gray', marginTop: 10, fontSize: 16 }}>
          Loading reservations...
        </Text>
        <Text style={{ color: 'gray', marginTop: 5, fontSize: 14 }}>
          Fetching all data for smart filtering
        </Text>
      </View>
    )
  }

  if (error) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8fafc', padding: 20 }}>
        <Text style={{ fontSize: 18, color: '#ef4444', textAlign: 'center', marginBottom: 15 }}>
          ❌ Error Loading Data
        </Text>
        <Text style={{ fontSize: 14, color: '#666', textAlign: 'center', marginBottom: 20 }}>
          {error}
        </Text>
        <TouchableOpacity
          style={{ backgroundColor: '#0066cc', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 8 }}
          onPress={loadAllReservations}
        >
          <Text style={{ color: 'white', fontSize: 16, fontWeight: 'bold' }}>
            🔄 Retry
          </Text>
        </TouchableOpacity>
      </View>
    )
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
      <FlatList
        data={displayedReservations}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={renderHeader}
        ListFooterComponent={renderFooter}
        removeClippedSubviews={true}
        maxToRenderPerBatch={20}
        windowSize={10}
        initialNumToRender={INITIAL_LOAD}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="on-drag"
        getItemLayout={(data, index) => ({
          length: 200, // Approximate item height
          offset: 200 * index,
          index,
        })}
        ListEmptyComponent={() => (
          <View style={{ padding: 40, alignItems: 'center' }}>
            <Text style={{ fontSize: 18, color: 'gray', textAlign: 'center' }}>
              {searchQuery ? '🔍 No reservations found' : '📋 No reservations available'}
            </Text>
            {searchQuery && (
              <TouchableOpacity
                style={{ marginTop: 15, backgroundColor: '#ef4444', paddingHorizontal: 15, paddingVertical: 8, borderRadius: 6 }}
                onPress={clearSearch}
              >
                <Text style={{ color: 'white', fontSize: 14, fontWeight: 'bold' }}>
                  ✕ Clear Search
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      />
    </View>
  )
}