# Property Management App - Wireframes & Visual Design

## Design System Overview

### Color Palette
```
Primary Blue:    #0066CC (Trust, professional)
Secondary Orange:#FF6B35 (Energy, action)
Success Green:   #22C55E (Positive status)
Warning Amber:   #F59E0B (Attention needed)
Error Red:       #EF4444 (Critical issues)
Neutral Gray:    #64748B (Text, borders)
Background:      #F8FAFC (Light background)
Surface:         #FFFFFF (Cards, modals)
```

### Typography Scale
```
H1: 32px/40px - Poppins Bold (Page titles)
H2: 24px/32px - Poppins SemiBold (Section headers)
H3: 20px/28px - Poppins Medium (Card titles)
Body: 16px/24px - Inter Regular (Main content)
Caption: 14px/20px - Inter Regular (Secondary info)
Button: 16px/24px - Inter SemiBold (Actions)
```

### Spacing System
```
xs: 4px   (tiny gaps)
sm: 8px   (small gaps)
md: 16px  (standard spacing)
lg: 24px  (section spacing)
xl: 32px  (large spacing)
xxl: 48px (page margins)
```

---

## Screen Wireframes

### 1. Authentication Screen

```
┌─────────────────────────────────────┐
│ [Logo]                              │
│                                     │
│      Property Management            │
│           Portal                    │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Enter your email address        │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ email@example.com          │ │ │
│ │ └─────────────────────────────┘ │ │
│ │                                 │ │
│ │ [ Send Magic Link ]             │ │
│ └─────────────────────────────────┘ │
│                                     │
│   ✉️  Check your email for a        │
│      secure access link            │
│                                     │
│   🔒  Enterprise-grade security     │
│      No passwords required         │
└─────────────────────────────────────┘
```

### 2. Main Dashboard (List View)

```
┌─────────────────────────────────────┐
│ ☰  Properties & Jobs          🔔 👤 │
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔍 Search properties...     [⚙️] │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [All] [Active] [Scheduled] [Done]   │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🏠 Sunset Villa Scottsdale      │ │
│ │ 👤 Smith, John                  │ │
│ │ 📅 Jun 10-12 • 📍 Phoenix, AZ  │ │
│ │ ┌─────────────┐ [Late Checkout] │ │
│ │ │🟢 Completed │ [Custom Clean]  │ │
│ │ └─────────────┘                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🏠 Desert Oasis Tempe           │ │
│ │ 👤 Johnson, Sarah               │ │
│ │ 📅 Jun 12-15 • 📍 Tempe, AZ    │ │
│ │ ┌─────────────┐ [Late Checkout] │ │
│ │ │🟡 In Progress│ [Custom Clean]  │ │
│ │ └─────────────┘                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🏠 Mountain View Paradise       │ │
│ │ 👤 Davis, Mike                  │ │
│ │ 📅 Jun 15-18 • 📍 Flagstaff    │ │
│ │ ┌─────────────┐ [Late Checkout] │ │
│ │ │🔵 Scheduled │ [Custom Clean]  │ │
│ │ └─────────────┘                 │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 3. Detailed Property View

```
┌─────────────────────────────────────┐
│ ←  Sunset Villa Scottsdale     ⋮   │
├─────────────────────────────────────┤
│                                     │
│ 🏠 Sunset Villa Scottsdale          │
│ 📍 26208 N 43rd St, Phoenix, AZ     │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Guest Information               │ │
│ │ 👤 Smith, John                  │ │
│ │ 📧 john.smith@email.com         │ │ 
│ │ 📱 (555) 123-4567               │ │
│ │ [📞 Call] [📧 Email] [💬 SMS]    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Reservation Details             │ │
│ │ Check-in:  Jun 10, 2025 4:00 PM│ │
│ │ Check-out: Jun 12, 2025 11:00 AM│ │
│ │ Duration:  2 nights             │ │
│ │ Guests:    4 adults, 2 children │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 💰 Job Cost: $125.00            │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ • Standard Cleaning  $85.00 │ │ │
│ │ │ • Deep Clean Kitchen $25.00 │ │ │
│ │ │ • Extra Towels (4)   $15.00 │ │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🧹 Cleaning Status              │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ ✅ Job Created              │ │ │
│ │ │ ✅ Employee Assigned        │ │ │
│ │ │ ✅ On My Way (10:30 AM)     │ │ │
│ │ │ ✅ Started (11:15 AM)       │ │ │
│ │ │ ✅ Completed (2:45 PM)      │ │ │
│ │ └─────────────────────────────┘ │ │
│ │ 👷 Maria Rodriguez              │ │
│ │ 📱 (555) 123-4567               │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────┬───────────────┐ │
│ │ [Request Late   │ [Custom       │ │
│ │  Checkout]      │  Clean Time]  │ │
│ └─────────────────┴───────────────┘ │
└─────────────────────────────────────┘
```

### 4. Search & Filter Interface

```
┌─────────────────────────────────────┐
│ ← Search & Filter              [✓]  │
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔍 Search properties, guests... │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Recent Searches:                    │
│ • "mevawala"                        │
│ • "Smith guest"                     │
│ • "June 15"                         │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🏠 Property Selection           │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ 🔍 mevawala              [×] │ │ │
│ │ └─────────────────────────────┘ │ │
│ │ Search Results (10 properties): │ │
│ │ ☑️ Mevawala Villa Phoenix       │ │
│ │ ☑️ Mevawala Estate Scottsdale   │ │
│ │ ☐ Mevawala House Tempe          │ │
│ │ ☐ Mevawala Condo Paradise Valley│ │
│ │ ☐ Mevawala Resort Casa Grande   │ │
│ │ ☐ Mevawala Retreat Flagstaff    │ │
│ │ ... (show more)                 │ │
│ │ Selected: 2 of 10               │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📅 Date Range                   │ │
│ │ From: [Jun 10, 2025     ▼]     │ │
│ │ To:   [Jun 20, 2025     ▼]     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🏷️ Status                       │ │
│ │ ☑️ Scheduled                    │ │
│ │ ☑️ In Progress                  │ │
│ │ ☑️ Completed                    │ │
│ │ ☐ Cancelled                     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📍 Location                     │ │
│ │ ☑️ Phoenix                      │ │
│ │ ☑️ Scottsdale                   │ │
│ │ ☐ Tempe                         │ │
│ │ ☐ Flagstaff                     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Clear All]          [Apply Filter] │
└─────────────────────────────────────┘
```

### 5. Request Form (Late Checkout)

```
┌─────────────────────────────────────┐
│ ← Request Late Checkout        [✓]  │
├─────────────────────────────────────┤
│                                     │
│ 🏠 Sunset Villa Scottsdale          │
│ 👤 Smith, John                      │
│ 📅 Current checkout: Jun 12, 11:00 AM│
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🕐 Requested Checkout Time      │ │
│ │ ┌─────────────┬─────────────────┐ │ │
│ │ │ Jun 12, 2025│ 3:00 PM    ▼   │ │ │
│ │ └─────────────┴─────────────────┘ │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📝 Reason (Optional)            │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ Flight delay - need extra   │ │ │
│ │ │ time to pack and get to     │ │ │
│ │ │ airport...                  │ │ │
│ │ │                             │ │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ ⚠️ Impact Information           │ │
│ │ • May affect next guest arrival │ │
│ │ • Additional cleaning time      │ │
│ │ • Subject to approval           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Cancel]           [Submit Request] │
└─────────────────────────────────────┘
```

### 6. Account Profile

```
┌─────────────────────────────────────┐
│ ← Account Profile              ⚙️   │
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │
│ │         [👤]                    │ │
│ │     John Manager                │ │
│ │  john@propertygroup.com         │ │
│ │    Member since 2023            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📋 Account Information          │ │
│ │ Name:     John Manager          │ │
│ │ Email:    john@propertygroup.com│ │
│ │ Phone:    (555) 987-6543        │ │
│ │ Role:     Property Manager      │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ [Request Changes]           │ │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🏠 Managed Properties (24)      │ │
│ │ • Phoenix Metro Area (18)       │ │
│ │ • Scottsdale (4)                │ │
│ │ • Flagstaff (2)                 │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ [View All Properties]       │ │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔔 Notification Preferences    │ │
│ │ ☑️ Job status updates           │ │
│ │ ☑️ Guest requests               │ │
│ │ ☑️ System maintenance           │ │
│ │ ☐ Marketing updates             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Sign Out]                          │
└─────────────────────────────────────┘
```

---

## Component Specifications

### Status Badge Component
```typescript
interface StatusBadgeProps {
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  size?: 'sm' | 'md' | 'lg'
}

// Visual specifications:
scheduled: Blue background (#0066CC), white text
in_progress: Orange background (#FF6B35), white text  
completed: Green background (#22C55E), white text
cancelled: Gray background (#64748B), white text

// Sizes:
sm: 12px padding, 12px font
md: 16px padding, 14px font  
lg: 20px padding, 16px font
```

### Reservation Card Component
```typescript
interface ReservationCardProps {
  reservation: {
    id: string
    propertyName: string
    guestName: string
    checkIn: string
    checkOut: string
    address: string
    job?: {
      status: JobStatus
      assignedEmployee?: string
      scheduledStart?: string
    }
  }
  onPress: () => void
  onRequestAction: (action: 'late-checkout' | 'custom-cleaning') => void
}

// Visual specifications:
- White background with subtle shadow
- 16px border radius
- 16px internal padding
- Pressable with scale animation (0.98)
- Divider line between content and actions
- Action buttons: outline style, 8px vertical padding
```

### Search Input Component
```typescript
interface SearchInputProps {
  value: string
  onChangeText: (text: string) => void
  onSubmit: () => void
  placeholder?: string
  loading?: boolean
  showHistory?: boolean
  recentSearches?: string[]
}

// Visual specifications:
- Full-width input with rounded corners (24px)
- Light gray background (#F1F5F9)
- Search icon on the right
- Loading spinner when searching
- Dropdown with recent searches
- Debounced input (300ms)
```

### Property Selection Component
```typescript
interface PropertySelectionProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  onSelectionChange: (selectedProperties: string[]) => void
  properties: Array<{
    id: string
    name: string
    location: string
  }>
  selectedProperties: string[]
  maxVisible?: number
}

// Visual specifications:
- Dedicated search input for property filtering
- Scrollable list of properties with checkboxes
- Selected count indicator (e.g., "Selected: 2 of 10")
- "Show more" link for long lists
- Clear search button (×) when active
- Immediate checkbox state updates
- Property names as unique identifiers
```

### Request Form Component
```typescript
interface RequestFormProps {
  type: 'late-checkout' | 'custom-cleaning'
  property: Property
  guest: Guest
  currentSchedule: Schedule
  onSubmit: (data: RequestData) => void
  onCancel: () => void
}

// Visual specifications:
- Modal overlay with slide-up animation
- Property/guest info header (non-editable)
- Form fields with proper validation
- Impact warning section (yellow background)
- Primary submit button, secondary cancel
- Form validation with inline errors
```

### Job Cost Component
```typescript
interface JobCostProps {
  totalCost: number
  lineItems: Array<{
    id: string
    name: string
    quantity: number
    unitPrice: number
    total: number
    category: 'service' | 'product' | 'fee'
  }>
  compact?: boolean
}

// Visual specifications:
- Prominent total cost display with currency formatting
- Collapsible line item breakdown
- Icons for different item categories (🧹 service, 📦 product, 💵 fee)
- Quantity and unit price details
- Uses placeholder data when real data not available
- Clear visual hierarchy with total emphasized
```

### Guest Contact Component
```typescript
interface GuestContactProps {
  guest: {
    name: string
    email?: string
    phone?: string
  }
  onCall?: (phone: string) => void
  onEmail?: (email: string) => void
  onSMS?: (phone: string) => void
}

// Visual specifications:
- Guest name prominently displayed
- Contact info with appropriate icons
- Action buttons for call, email, SMS
- Disabled state when contact info unavailable
- Placeholder text for missing contact data
- Integration with device contact capabilities
```

### Employee Details Component  
```typescript
interface EmployeeDetailsProps {
  employee: {
    id: string
    name: string
    phone?: string
    role: string
  }
  showContact?: boolean
}

// Visual specifications:
- Employee name with role indicator
- Contact information when available
- Profile icon or avatar placeholder
- Call button for direct contact
- Placeholder when employee not assigned
- Status indicator (available, busy, offline)
```

---

## Responsive Design Breakpoints

### Mobile First Approach
```css
/* Mobile (default) */
/* 320px - 768px */
.container {
  padding: 16px;
  margin: 0;
}

/* Tablet */
@media (min-width: 768px) {
  .container {
    padding: 24px;
    max-width: 768px;
    margin: 0 auto;
  }
}

/* Desktop/Web */
@media (min-width: 1024px) {
  .container {
    padding: 32px;
    max-width: 1200px;
    margin: 0 auto;
  }
  
  /* Two-column layout */
  .main-content {
    display: flex;
    gap: 32px;
  }
  
  .sidebar {
    width: 300px;
  }
  
  .content {
    flex: 1;
  }
}
```

### Platform-Specific Adaptations

#### iOS Specific
- Native navigation bar styling
- iOS-style loading indicators
- Haptic feedback for interactions
- Safe area handling for notched devices

#### Android Specific  
- Material Design ripple effects
- Android-style navigation patterns
- System back button handling
- Status bar color coordination

#### Web Specific
- Keyboard navigation support
- Mouse hover states
- Responsive grid layouts
- Browser history integration

---

## Animation Specifications

### Micro-interactions
```typescript
// Button press animation
const buttonPressAnimation = {
  scale: 0.98,
  duration: 150,
  easing: 'easeInOut'
}

// Card selection animation
const cardSelectAnimation = {
  shadowOpacity: 0.2,
  shadowRadius: 12,
  duration: 200
}

// Status change animation
const statusChangeAnimation = {
  backgroundColor: newColor,
  duration: 300,
  easing: 'easeOut'
}

// Loading state animation
const loadingAnimation = {
  opacity: [1, 0.5, 1],
  duration: 1500,
  repeat: -1
}
```

### Page Transitions
```typescript
// Stack navigation transitions
const slideTransition = {
  headerShown: true,
  cardStyleInterpolator: CardStyleInterpolators.forHorizontalIOS,
  transitionSpec: {
    open: TransitionSpecs.TransitionIOSSpec,
    close: TransitionSpecs.TransitionIOSSpec,
  }
}

// Modal presentations
const modalTransition = {
  presentation: 'modal',
  cardStyleInterpolator: CardStyleInterpolators.forVerticalIOS
}
```

---

## Accessibility Specifications

### Screen Reader Support
```typescript
// Semantic labels for all interactive elements
<Button
  accessibilityLabel="Request late checkout for Sunset Villa"
  accessibilityHint="Opens form to request extended checkout time"
  accessibilityRole="button"
>
  Request Late Checkout
</Button>

// Status announcements
<Text
  accessibilityLabel={`Job status is ${status}`}
  accessibilityLiveRegion="polite"
>
  {status}
</Text>
```

### Keyboard Navigation
- Tab order follows logical flow
- Focus indicators clearly visible
- All interactive elements keyboard accessible
- Escape key closes modals/dropdowns

### Color Contrast
- All text meets WCAG AA standards (4.5:1 ratio)
- Interactive elements have 3:1 contrast
- Status colors distinguishable for colorblind users
- High contrast mode support

---

## Performance Specifications

### Loading Benchmarks
- Initial app load: <3 seconds
- Search results: <1 second
- Screen transitions: <300ms
- Image loading: Progressive with placeholders

### Memory Management
- Lazy loading for large lists
- Image caching with size limits
- Background task cleanup
- Memory leak prevention

### Offline Capabilities
- Cache recent reservations (last 30 days)
- Queue requests when offline
- Sync when connection restored
- Offline indicators throughout app

This design system provides a comprehensive foundation for building a scalable, accessible, and performant property management application that works seamlessly across all platforms while maintaining consistency with modern design standards.