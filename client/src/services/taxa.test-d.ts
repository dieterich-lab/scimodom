import { expectTypeOf } from 'vitest'
import { type Taxa, taxaCache } from '@/services/taxa'

expectTypeOf(taxaCache.getPromise).returns.resolves.toEqualTypeOf<Taxa[]>()
expectTypeOf(taxaCache.getData).returns.resolves.toEqualTypeOf<Readonly<Taxa[]>>()
