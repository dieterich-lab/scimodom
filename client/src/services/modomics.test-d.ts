import { expectTypeOf } from 'vitest'
import { type Modomics, modomicsCache } from '@/services/modomics'

expectTypeOf(modomicsCache.getPromise).returns.resolves.toEqualTypeOf<Modomics[]>()
expectTypeOf(modomicsCache.getData).returns.resolves.toEqualTypeOf<Readonly<Modomics[]>>()
