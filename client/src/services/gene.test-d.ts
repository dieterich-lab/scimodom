import { expectTypeOf } from 'vitest'
import { getGenesForSelectionIds } from '@/services/gene'

expectTypeOf(getGenesForSelectionIds).returns.resolves.toEqualTypeOf<string[]>()
