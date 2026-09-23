import { expectTypeOf } from 'vitest'
import { getBioTypes } from '@/services/biotype'

expectTypeOf(getBioTypes).returns.resolves.toEqualTypeOf<string[]>()
