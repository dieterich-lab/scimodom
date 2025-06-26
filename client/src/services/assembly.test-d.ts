import { expectTypeOf } from 'vitest'
import { type Assembly, getAssembliesByTaxaId } from '@/services/assembly'

expectTypeOf(getAssembliesByTaxaId).returns.resolves.toEqualTypeOf<Assembly[]>()
