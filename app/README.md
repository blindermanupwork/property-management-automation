# Property Management Mobile App

A comprehensive React Native application for property management automation, built with Expo and Tamagui.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Expo CLI (`npm install -g @expo/cli`)

### Installation & Run

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run on specific platform
npm run ios     # iOS simulator
npm run android # Android emulator  
npm run web     # Web browser
```

## 📱 App Features

### MUST HAVE (✅ Implemented)
- ✅ Magic Link Authentication
- ✅ View Reservations List
- ✅ View Job Status Tracking  
- ✅ Search & Filter with Property Selection
- ✅ Real-time Data Sync (Mock)
- ✅ Guest Contact Information
- ✅ Employee/Cleaner Details
- ✅ Job Cost & Service Details
- ✅ Account Profile View
- ✅ Responsive Design (Mobile/Web)

### SHOULD HAVE (✅ Implemented)
- ✅ Request Late Checkout
- ✅ Request Custom Cleaning Time
- ✅ Detailed Reservation View
- ✅ Search History
- 🔄 Calendar/Timeline View (Planned)
- 🔄 Photo Upload Functionality (Planned)

## 🏗️ Project Structure

```
src/
├── design-system/           # Reusable design components
│   ├── components/atoms/    # Basic UI components (Button, Text, Input)
│   └── tokens/             # Design tokens (colors, typography)
├── screens/                # Main app screens
│   ├── AuthScreen.tsx      # Magic link authentication
│   ├── DashboardScreen.tsx # Main reservation list
│   ├── SearchScreen.tsx    # Advanced search & filters
│   └── ReservationDetailScreen.tsx # Detailed view
├── components/             # Feature-specific components
│   ├── ReservationCard.tsx # Reservation list item
│   ├── SearchInput.tsx     # Search with history
│   ├── PropertySelection.tsx # Property picker
│   ├── GuestContact.tsx    # Guest contact info
│   └── JobCostBreakdown.tsx # Cost details
├── services/               # API and data services
│   └── mockData.ts         # Development mock data
└── types/                  # TypeScript definitions
```

## 🛠️ Technology Stack

- **Framework**: React Native + Expo
- **UI Library**: Tamagui (Universal design system)
- **Navigation**: React Navigation 6
- **State Management**: React Hooks + Context
- **Language**: TypeScript
- **Design Pattern**: Atomic Design
- **Development**: Mock API with realistic data

## 🔗 Integration Status

This app integrates with existing property management systems via READ-ONLY connections:
- ✅ Mock API layer implemented
- ✅ Real-time sync simulation 
- ✅ TypeScript interfaces matching existing data structure
- 🔄 Production API integration (planned)
- 🔄 WebSocket connections (planned)

## 📋 Development Notes

- **READ-ONLY Integration**: App safely reads from existing production systems without modifications
- **Mock Data**: Uses realistic mock data for development and testing
- **Universal Code**: Single codebase for iOS, Android, and Web
- **Design System**: Follows wireframes.md specifications exactly
- **Safe Development**: All new code isolated in `/app/` directory

## 🎨 Design System

The app uses a comprehensive design system with:
- **Color Palette**: Primary (#0066CC), Secondary (#FF6B35), Success (#22C55E)
- **Typography**: Poppins headings, Inter body text
- **Components**: Atomic design pattern with variants and sizes
- **Responsive**: Adapts to mobile, tablet, and web viewports
- **Dark Mode**: Ready (tokens defined, components support theme switching)

## 📖 Documentation

- **[APP_PLAN.md](./APP_PLAN.md)** - Complete development plan and architecture
- **[WIREFRAMES.md](./WIREFRAMES.md)** - Visual design specifications
- **[CLAUDE.md](./CLAUDE.md)** - Development constraints and guidelines

## 🚀 Next Steps

1. **Try it now**: Run `npm start` to see the working app
2. **Mobile testing**: Use Expo Go app on your device
3. **Authentication**: Test magic link flow with any email
4. **Features**: Explore reservations, search, and filtering
5. **Integration**: Connect to production APIs when ready

The app is fully functional with mock data and ready for production integration!