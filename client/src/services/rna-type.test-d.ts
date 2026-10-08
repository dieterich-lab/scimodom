import { expectTypeOf } from 'vitest'
import { rnaTypeCache, type RnaType } from '@/services/rna-type'

expectTypeOf(rnaTypeCache.getPromise).returns.resolves.toEqualTypeOf<RnaType[]>()
expectTypeOf(rnaTypeCache.getData).returns.resolves.toEqualTypeOf<Readonly<RnaType[]>>()
