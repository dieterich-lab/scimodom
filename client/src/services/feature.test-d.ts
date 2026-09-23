import { expectTypeOf } from 'vitest'
import { getFeaturesByRnaType } from '@/services/feature'

expectTypeOf(getFeaturesByRnaType).returns.resolves.toEqualTypeOf<string[]>()
