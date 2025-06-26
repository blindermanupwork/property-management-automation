import React, { useState, useEffect } from 'react'
import { NavigationContainer } from '@react-navigation/native'
import { createStackNavigator } from '@react-navigation/stack'
import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, Alert, TextInput, FlatList } from 'react-native'
import AsyncStorage from '@react-native-async-storage/async-storage'
import ApiService from './services/api'
import PaginatedReservationsList from './components/PaginatedReservationsList'

const Stack = createStackNavigator()

// Authentication Screen
function AuthScreen({ navigation }) {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)

  const handleMagicLink = async () => {
    if (!email.trim()) {
      Alert.alert('Error', 'Please enter your email address')
      return
    }

    try {
      setLoading(true)
      const result = await ApiService.sendMagicLink(email)
      if (result.success) {
        Alert.alert('Magic Link Sent', 'Check your email for the login link.')
        // Save authentication state
        await AsyncStorage.setItem('userAuth', JSON.stringify({ userEmail: email }))
        // In a real app, you'd handle the magic link callback
        // For now, we'll simulate successful authentication
        setTimeout(() => {
          navigation.replace('Main', { userEmail: email })
        }, 2000)
      }
    } catch (error) {
      Alert.alert('Error', error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSkipAuth = async () => {
    try {
      console.log('Skip auth button clicked')
      // Save no-filter state
      await AsyncStorage.setItem('userAuth', JSON.stringify({ userEmail: null }))
      // Direct navigation for web compatibility
      navigation.replace('Main', { userEmail: null })
    } catch (error) {
      console.error('Skip auth error:', error)
      // Fallback navigation
      navigation.navigate('Main', { userEmail: null })
    }
  }

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'white', padding: 20 }}>
      <Text style={{ fontSize: 24, color: 'black', textAlign: 'center', marginBottom: 20 }}>
        Property Management
      </Text>
      <Text style={{ fontSize: 16, color: 'gray', marginBottom: 30, textAlign: 'center' }}>
        Enter your email to see your reservations
      </Text>

      <TextInput
        style={{
          borderWidth: 1,
          borderColor: '#e2e8f0',
          borderRadius: 8,
          padding: 15,
          fontSize: 16,
          width: '100%',
          marginBottom: 20,
          backgroundColor: '#f8fafc'
        }}
        placeholder="Enter your email address"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        autoCorrect={false}
      />

      <TouchableOpacity
        style={{ 
          backgroundColor: loading ? '#94a3b8' : '#0066cc', 
          padding: 15, 
          borderRadius: 8, 
          width: '100%',
          marginBottom: 15
        }}
        onPress={handleMagicLink}
        disabled={loading}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
          {loading ? 'Sending...' : '🔗 Send Magic Link'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={{ 
          backgroundColor: '#666', 
          padding: 15, 
          borderRadius: 8, 
          width: '100%',
          marginBottom: 10
        }}
        onPress={handleSkipAuth}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
          🚀 Skip Authentication (View All)
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={{ 
          backgroundColor: '#22c55e', 
          padding: 15, 
          borderRadius: 8, 
          width: '100%',
          marginBottom: 20
        }}
        onPress={async () => {
          await AsyncStorage.setItem('userAuth', JSON.stringify({ userEmail: null }))
          navigation.replace('Main', { userEmail: null })
        }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
          ⚡ Quick Access (No Filter)
        </Text>
      </TouchableOpacity>

      <Text style={{ fontSize: 12, color: 'gray', textAlign: 'center' }}>
        Only users in the system can see their reservations.{'\n'}
        Skip authentication to view all reservations.
      </Text>
    </View>
  )
}

// Home Screen
function HomeScreen({ route, navigation }) {
  const { userEmail } = route.params || {}
  const [reservations, setReservations] = useState([])
  const [filteredReservations, setFilteredReservations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadReservations()
  }, [])

  useEffect(() => {
    filterReservationsByUser()
  }, [reservations, userEmail])

  const loadReservations = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await ApiService.getReservations()
      setReservations(data)
    } catch (err) {
      console.error('Failed to load reservations:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const filterReservationsByUser = async () => {
    if (!userEmail) {
      // No authentication - show all reservations
      setFilteredReservations(reservations)
      return
    }

    try {
      // Use real data service for user filtering with proper error handling
      const ApiService = (await import('./services/api')).default
      const userReservations = await ApiService.searchProperties('', userEmail)
      setFilteredReservations(userReservations)
      setError(null)
    } catch (err) {
      console.error('User filtering error:', err)
      setError(err.message || 'User not found in system. No reservations available for your email.')
      setFilteredReservations([])
    }
  }

  const handleRefresh = () => {
    loadReservations()
  }

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Logout', 
          onPress: async () => {
            await AsyncStorage.removeItem('userAuth')
            navigation.replace('Auth')
          }
        }
      ]
    )
  }

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'white', padding: 20 }}>
      <Text style={{ fontSize: 24, color: 'black', textAlign: 'center', marginBottom: 10 }}>
        Property Management App
      </Text>
      
      {userEmail ? (
        <View style={{ alignItems: 'center', marginBottom: 20 }}>
          <Text style={{ fontSize: 16, color: 'gray', textAlign: 'center' }}>
            Welcome back!
          </Text>
          <Text style={{ fontSize: 14, color: '#0066cc', textAlign: 'center', marginBottom: 10 }}>
            📧 {userEmail}
          </Text>
          <TouchableOpacity onPress={handleLogout}>
            <Text style={{ fontSize: 12, color: '#dc2626', textAlign: 'center' }}>
              Logout
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <Text style={{ fontSize: 16, color: '#f59e0b', marginBottom: 20, textAlign: 'center' }}>
          🚀 Viewing All Reservations (No Filter)
        </Text>
      )}
      
      {loading ? (
        <View style={{ marginBottom: 30 }}>
          <ActivityIndicator size="large" color="#0066cc" />
          <Text style={{ textAlign: 'center', marginTop: 10, color: 'gray' }}>Loading reservations...</Text>
        </View>
      ) : (
        <>
          <TouchableOpacity 
            style={{ backgroundColor: '#0066cc', padding: 15, borderRadius: 8, marginBottom: 10, minWidth: 200 }}
            onPress={() => navigation.navigate('Reservations', { reservations: filteredReservations, userEmail })}
          >
            <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
              View Reservations ({filteredReservations.length})
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={{ backgroundColor: '#22c55e', padding: 15, borderRadius: 8, marginBottom: 10, minWidth: 200 }}
            onPress={() => navigation.navigate('Search', { reservations: filteredReservations, userEmail })}
          >
            <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
              Search Properties  
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={{ backgroundColor: '#f59e0b', padding: 15, borderRadius: 8, marginBottom: 10, minWidth: 200 }}
            onPress={handleRefresh}
          >
            <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
              🔄 Refresh Data
            </Text>
          </TouchableOpacity>
        </>
      )}
      
      {error && (
        <View style={{ backgroundColor: '#fee2e2', padding: 15, borderRadius: 8, marginTop: 20, maxWidth: 300 }}>
          <Text style={{ color: '#dc2626', textAlign: 'center', fontSize: 14 }}>
            {error}
          </Text>
          {userEmail && (
            <TouchableOpacity 
              style={{ backgroundColor: '#dc2626', padding: 10, borderRadius: 4, marginTop: 10 }}
              onPress={handleLogout}
            >
              <Text style={{ color: 'white', textAlign: 'center', fontSize: 14 }}>
                Try Different Email
              </Text>
            </TouchableOpacity>
          )}
        </View>
      )}
      
      <Text style={{ fontSize: 14, color: 'green', marginTop: 30, textAlign: 'center' }}>
        ✅ {userEmail ? 'User-Filtered Data' : 'All Data'} Active
      </Text>
    </View>
  )
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
          <Text style={{ fontSize: 12, color: '#22c55e', marginBottom: 8 }}>
            ✅ HCP Job: {reservation.hcpJobId}
          </Text>
        )}
        
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <Text style={{ fontSize: 16, fontWeight: 'bold', color: '#22c55e' }}>
            ${reservation.totalCost.toFixed(2)}
          </Text>
          <Text style={{ fontSize: 12, color: '#0066cc' }}>
            Tap to view details →
          </Text>
        </View>
      </TouchableOpacity>
      
      {/* Action Buttons */}
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 }}>
        {!reservation.hcpJobId && onCreateJob && (
          <TouchableOpacity
            style={{ backgroundColor: '#22c55e', padding: 10, borderRadius: 6, flex: 1, marginRight: 5 }}
            onPress={onCreateJob}
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

// Reservations Screen with Enhanced Pagination
function ReservationsScreen({ route, navigation }) {
  const { reservations = [], userEmail } = route.params || {}
  const [loading, setLoading] = useState(false)

  const handleCreateJob = async (reservation) => {
    if (reservation.hcpJobId) {
      Alert.alert('Job Already Exists', 'This reservation already has a job created in HousecallPro.')
      return
    }

    try {
      setLoading(true)
      Alert.alert(
        'Create Job',
        `Create a cleaning job for ${reservation.guest} at ${reservation.property}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Create',
            onPress: async () => {
              try {
                const result = await ApiService.createJob(reservation)
                Alert.alert('Success', 'Job created successfully in HousecallPro!')
                navigation.goBack() // Refresh data
              } catch (error) {
                Alert.alert('Error', `Failed to create job: ${error.message}`)
              }
            }
          }
        ]
      )
    } catch (error) {
      Alert.alert('Error', error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
      {loading && (
        <View style={{ alignItems: 'center', marginTop: 20, marginBottom: 10 }}>
          <ActivityIndicator size="large" color="#0066cc" />
          <Text style={{ color: 'gray', marginTop: 10 }}>Processing job creation...</Text>
        </View>
      )}
      
      <PaginatedReservationsList
        reservations={reservations}
        userEmail={userEmail}
        onReservationPress={(res) => navigation.navigate('ReservationDetail', { reservation: res })}
        onCreateJob={handleCreateJob}
        navigation={navigation}
      />
    </View>
  )
}

// Reservation Detail Screen
function ReservationDetailScreen({ route, navigation }) {
  const { reservation } = route.params
  
  return (
    <View style={{ flex: 1, backgroundColor: 'white' }}>
      <ScrollView style={{ flex: 1, padding: 20 }}>
        <Text style={{ fontSize: 24, fontWeight: 'bold', color: 'black', marginBottom: 20, textAlign: 'center' }}>
          Reservation Details
        </Text>
        
        <View style={{ backgroundColor: '#f8fafc', borderRadius: 8, padding: 15, marginBottom: 20 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold', color: 'black', marginBottom: 10 }}>
            Guest Information
          </Text>
          <Text style={{ fontSize: 16, color: '#666', marginBottom: 5 }}>
            👤 Guest: {reservation.guest}
          </Text>
          <Text style={{ fontSize: 16, color: '#666', marginBottom: 5 }}>
            📍 Property: {reservation.property}
          </Text>
          <Text style={{ fontSize: 16, color: '#666', marginBottom: 5 }}>
            📅 Check-in: {reservation.checkin}
          </Text>
          <Text style={{ fontSize: 16, color: '#666', marginBottom: 5 }}>
            📅 Check-out: {reservation.checkout}
          </Text>
        </View>
        
        <View style={{ backgroundColor: '#f8fafc', borderRadius: 8, padding: 15, marginBottom: 20 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold', color: 'black', marginBottom: 10 }}>
            Job Information
          </Text>
          <Text style={{ fontSize: 16, color: '#666', marginBottom: 5 }}>
            🧹 Service: {reservation.jobType}
          </Text>
          <Text style={{ fontSize: 16, color: '#666', marginBottom: 5 }}>
            📋 Status: {reservation.status}
          </Text>
          <Text style={{ fontSize: 16, color: '#22c55e', fontWeight: 'bold' }}>
            💰 Total Cost: ${reservation.totalCost.toFixed(2)}
          </Text>
        </View>
        
        <TouchableOpacity 
          style={{ backgroundColor: '#666', padding: 15, borderRadius: 8, marginTop: 20 }}
          onPress={() => navigation.goBack()}
        >
          <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
            ← Back to Reservations
          </Text>
        </TouchableOpacity>
        
        <Text style={{ fontSize: 14, color: 'green', marginTop: 20, textAlign: 'center', marginBottom: 20 }}>
          ✅ Reservation Detail Working
        </Text>
      </ScrollView>
    </View>
  )
}

// Search Screen  
function SearchScreen({ route, navigation }) {
  const { reservations = [], userEmail } = route.params || {}
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('checkin') // checkin, checkout, guest, property, status, cost
  const [sortOrder, setSortOrder] = useState('asc') // asc, desc
  const [filterStatus, setFilterStatus] = useState('all') // all, scheduled, in_progress, completed
  const [filteredResults, setFilteredResults] = useState([])

  useEffect(() => {
    applyFiltersAndSort()
  }, [searchQuery, sortBy, sortOrder, filterStatus, reservations])

  const applyFiltersAndSort = () => {
    let results = [...reservations]

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      results = results.filter(reservation =>
        reservation.guest.toLowerCase().includes(query) ||
        reservation.property.toLowerCase().includes(query) ||
        reservation.jobType.toLowerCase().includes(query) ||
        reservation.id.toLowerCase().includes(query) ||
        (reservation.employeeAssigned && reservation.employeeAssigned.toLowerCase().includes(query))
      )
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      results = results.filter(reservation => reservation.status === filterStatus)
    }

    // Apply sorting
    results.sort((a, b) => {
      let aValue, bValue

      switch (sortBy) {
        case 'checkin':
          aValue = new Date(a.checkin)
          bValue = new Date(b.checkin)
          break
        case 'checkout':
          aValue = new Date(a.checkout)
          bValue = new Date(b.checkout)
          break
        case 'guest':
          aValue = a.guest.toLowerCase()
          bValue = b.guest.toLowerCase()
          break
        case 'property':
          aValue = a.property.toLowerCase()
          bValue = b.property.toLowerCase()
          break
        case 'status':
          aValue = a.status
          bValue = b.status
          break
        case 'cost':
          aValue = a.totalCost
          bValue = b.totalCost
          break
        default:
          aValue = a.checkin
          bValue = b.checkin
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    setFilteredResults(results)
  }

  const getSortButtonStyle = (field) => ({
    backgroundColor: sortBy === field ? '#0066cc' : '#e2e8f0',
    padding: 8,
    borderRadius: 4,
    marginHorizontal: 2,
    minWidth: 60
  })

  const getFilterButtonStyle = (status) => ({
    backgroundColor: filterStatus === status ? '#22c55e' : '#e2e8f0',
    padding: 8,
    borderRadius: 4,
    marginHorizontal: 2,
    minWidth: 70
  })

  return (
    <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
      <ScrollView style={{ flex: 1, padding: 15 }}>
        <Text style={{ fontSize: 24, fontWeight: 'bold', color: 'black', marginBottom: 20, textAlign: 'center' }}>
          Search & Filter
        </Text>

        {userEmail && (
          <Text style={{ fontSize: 14, color: '#0066cc', textAlign: 'center', marginBottom: 15 }}>
            📧 Showing results for: {userEmail}
          </Text>
        )}

        {/* Search Input */}
        <TextInput
          style={{
            borderWidth: 1,
            borderColor: '#e2e8f0',
            borderRadius: 8,
            padding: 12,
            fontSize: 16,
            backgroundColor: 'white',
            marginBottom: 15
          }}
          placeholder="Search by guest, property, job type, or employee..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

        {/* Status Filter */}
        <Text style={{ fontSize: 16, fontWeight: 'bold', color: 'black', marginBottom: 10 }}>
          Filter by Status:
        </Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 15 }}>
          <View style={{ flexDirection: 'row' }}>
            {[
              { key: 'all', label: 'All' },
              { key: 'scheduled', label: 'Scheduled' },
              { key: 'in_progress', label: 'In Progress' },
              { key: 'completed', label: 'Completed' }
            ].map(status => (
              <TouchableOpacity
                key={status.key}
                style={getFilterButtonStyle(status.key)}
                onPress={() => setFilterStatus(status.key)}
              >
                <Text style={{ 
                  color: filterStatus === status.key ? 'white' : 'black',
                  textAlign: 'center',
                  fontSize: 12,
                  fontWeight: 'bold'
                }}>
                  {status.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>

        {/* Sort Options */}
        <Text style={{ fontSize: 16, fontWeight: 'bold', color: 'black', marginBottom: 10 }}>
          Sort by:
        </Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 10 }}>
          <View style={{ flexDirection: 'row' }}>
            {[
              { key: 'checkin', label: 'Check-in' },
              { key: 'checkout', label: 'Check-out' },
              { key: 'guest', label: 'Guest' },
              { key: 'property', label: 'Property' },
              { key: 'status', label: 'Status' },
              { key: 'cost', label: 'Cost' }
            ].map(sort => (
              <TouchableOpacity
                key={sort.key}
                style={getSortButtonStyle(sort.key)}
                onPress={() => setSortBy(sort.key)}
              >
                <Text style={{ 
                  color: sortBy === sort.key ? 'white' : 'black',
                  textAlign: 'center',
                  fontSize: 12,
                  fontWeight: 'bold'
                }}>
                  {sort.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>

        {/* Sort Order */}
        <View style={{ flexDirection: 'row', marginBottom: 20 }}>
          <TouchableOpacity
            style={{
              backgroundColor: sortOrder === 'asc' ? '#f59e0b' : '#e2e8f0',
              padding: 10,
              borderRadius: 4,
              marginRight: 10,
              flex: 1
            }}
            onPress={() => setSortOrder('asc')}
          >
            <Text style={{ 
              color: sortOrder === 'asc' ? 'white' : 'black',
              textAlign: 'center',
              fontSize: 14,
              fontWeight: 'bold'
            }}>
              ↑ Ascending
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={{
              backgroundColor: sortOrder === 'desc' ? '#f59e0b' : '#e2e8f0',
              padding: 10,
              borderRadius: 4,
              flex: 1
            }}
            onPress={() => setSortOrder('desc')}
          >
            <Text style={{ 
              color: sortOrder === 'desc' ? 'white' : 'black',
              textAlign: 'center',
              fontSize: 14,
              fontWeight: 'bold'
            }}>
              ↓ Descending
            </Text>
          </TouchableOpacity>
        </View>

        {/* Results */}
        <Text style={{ fontSize: 18, fontWeight: 'bold', color: 'black', marginBottom: 15 }}>
          Results ({filteredResults.length})
        </Text>

        {filteredResults.length === 0 ? (
          <View style={{ alignItems: 'center', marginTop: 50 }}>
            <Text style={{ fontSize: 16, color: 'gray', textAlign: 'center' }}>
              No reservations found matching your criteria
            </Text>
          </View>
        ) : (
          filteredResults.map(reservation => (
            <ReservationCard
              key={reservation.id}
              reservation={reservation}
              onPress={(res) => navigation.navigate('ReservationDetail', { reservation: res })}
            />
          ))
        )}

        <TouchableOpacity 
          style={{ backgroundColor: '#666', padding: 15, borderRadius: 8, marginTop: 20 }}
          onPress={() => navigation.goBack()}
        >
          <Text style={{ color: 'white', textAlign: 'center', fontSize: 16, fontWeight: 'bold' }}>
            ← Back to Home
          </Text>
        </TouchableOpacity>
        
        <Text style={{ fontSize: 14, color: 'green', marginTop: 20, textAlign: 'center', marginBottom: 20 }}>
          ✅ Advanced Search & Filter Active
        </Text>
      </ScrollView>
    </View>
  )
}

// App Component with Authentication Persistence
export default function App() {
  const [initialRoute, setInitialRoute] = useState('Auth')
  const [initialParams, setInitialParams] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkAuthState()
  }, [])

  const checkAuthState = async () => {
    try {
      const savedAuth = await AsyncStorage.getItem('userAuth')
      if (savedAuth) {
        const authData = JSON.parse(savedAuth)
        console.log('🔄 Restored authentication:', authData.userEmail || 'No filter')
        setInitialRoute('Main')
        setInitialParams({ userEmail: authData.userEmail })
      }
    } catch (error) {
      console.error('Failed to restore auth state:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'white' }}>
        <ActivityIndicator size="large" color="#0066cc" />
        <Text style={{ marginTop: 10, color: 'gray' }}>Loading...</Text>
      </View>
    )
  }

  return (
    <NavigationContainer>
      <Stack.Navigator 
        initialRouteName={initialRoute}
        screenOptions={{
          headerBackTitle: 'Back',
          headerTintColor: '#0066cc'
        }}
      >
        <Stack.Screen 
          name="Auth" 
          component={AuthScreen} 
          options={{ title: 'Login', headerShown: false }}
        />
        <Stack.Screen 
          name="Main" 
          component={HomeScreen} 
          options={{ title: 'Property Management' }}
          initialParams={initialParams}
        />
        <Stack.Screen 
          name="Reservations" 
          component={ReservationsScreen}
          options={{ title: 'Reservations' }}
        />
        <Stack.Screen 
          name="ReservationDetail" 
          component={ReservationDetailScreen}
          options={{ title: 'Reservation Details' }}
        />
        <Stack.Screen 
          name="Search" 
          component={SearchScreen}
          options={{ title: 'Search & Filter' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  )
}