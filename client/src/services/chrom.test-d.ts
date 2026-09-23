import { expectTypeOf } from 'vitest'
import { type Chrom, getChromsByTaxaId } from '@/services/chrom'

expectTypeOf(getChromsByTaxaId).returns.resolves.toEqualTypeOf<Chrom[]>()
