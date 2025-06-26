import { createTamagui } from '@tamagui/core'
import { config } from '@tamagui/config/v3'

// Create a simple, working Tamagui configuration
const tamaguiConfig = createTamagui(config)

export default tamaguiConfig

export type Conf = typeof tamaguiConfig

declare module '@tamagui/core' {
  interface TamaguiCustomConfig extends Conf {}
}