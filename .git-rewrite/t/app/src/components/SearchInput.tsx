import React, { useState, useEffect } from 'react'
import { Stack, Pressable, ScrollView } from '@tamagui/core'
import { Lucide } from '@tamagui/lucide-icons'

import { Input } from '../design-system/components/atoms/Input/Input'
import { Text, Caption } from '../design-system/components/atoms/Text/Text'
import { colors, spacing } from '../design-system/tokens'

interface SearchInputProps {
  value: string
  onChangeText: (text: string) => void
  onSubmit: () => void
  placeholder?: string
  loading?: boolean
  showHistory?: boolean
  recentSearches?: string[]
  onSelectHistory?: (search: string) => void
  onClearHistory?: () => void
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChangeText,
  onSubmit,
  placeholder = "Search properties, guests...",
  loading = false,
  showHistory = true,
  recentSearches = [],
  onSelectHistory,
  onClearHistory
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [isFocused, setIsFocused] = useState(false)

  // Show suggestions when focused and have recent searches
  useEffect(() => {
    setShowSuggestions(isFocused && showHistory && recentSearches.length > 0)
  }, [isFocused, showHistory, recentSearches.length])

  const handleFocus = () => {
    setIsFocused(true)
  }

  const handleBlur = () => {
    // Delay to allow tapping on suggestions
    setTimeout(() => setIsFocused(false), 200)
  }

  const handleSelectHistory = (search: string) => {
    onChangeText(search)
    setShowSuggestions(false)
    onSelectHistory?.(search)
  }

  const searchIcon = loading ? (
    <Lucide.Loader2 size={20} color={colors.textSecondary} />
  ) : (
    <Lucide.Search size={20} color={colors.textSecondary} />
  )

  const clearButton = value.length > 0 ? (
    <Pressable onPress={() => onChangeText('')}>
      <Lucide.X size={20} color={colors.textSecondary} />
    </Pressable>
  ) : null

  return (
    <Stack width="100%" position="relative">
      {/* Main search input - following wireframes.md */}
      <Input
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        leftIcon={searchIcon}
        rightIcon={clearButton}
        onSubmitEditing={onSubmit}
        onFocus={handleFocus}
        onBlur={handleBlur}
        size="lg"
        style={{
          borderRadius: 24, // Full rounded from wireframes
          backgroundColor: colors.background,
          paddingHorizontal: spacing.lg,
        }}
      />

      {/* Recent searches dropdown - matching wireframes.md */}
      {showSuggestions && (
        <Stack
          position="absolute"
          top={48}
          left={0}
          right={0}
          backgroundColor="$surface"
          borderRadius="$md"
          shadowColor="$shadow"
          shadowOffset={{ width: 0, height: 4 }}
          shadowOpacity={0.15}
          shadowRadius={12}
          zIndex={1000}
          maxHeight={200}
        >
          <Stack padding="$md">
            <Stack direction="row" justifyContent="space-between" alignItems="center" marginBottom="$sm">
              <Text variant="caption" weight="medium" color="textSecondary">
                Recent Searches
              </Text>
              {onClearHistory && (
                <Pressable onPress={onClearHistory}>
                  <Text variant="caption" color="primary">
                    Clear
                  </Text>
                </Pressable>
              )}
            </Stack>
            
            <ScrollView maxHeight={120}>
              <Stack space="$xs">
                {recentSearches.map((search, index) => (
                  <Pressable
                    key={index}
                    onPress={() => handleSelectHistory(search)}
                    style={{
                      paddingVertical: spacing.sm,
                      paddingHorizontal: spacing.sm,
                      borderRadius: spacing.xs,
                    }}
                  >
                    <Stack direction="row" alignItems="center" space="$sm">
                      <Lucide.Clock size={16} color={colors.textSecondary} />
                      <Text variant="body" color="text" flex={1}>
                        {search}
                      </Text>
                      <Lucide.ArrowUpLeft size={16} color={colors.textSecondary} />
                    </Stack>
                  </Pressable>
                ))}
              </Stack>
            </ScrollView>
          </Stack>
        </Stack>
      )}
    </Stack>
  )
}

export default SearchInput