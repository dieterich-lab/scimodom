import { expectTypeOf } from 'vitest'
import {
  subtract,
  intersect,
  closest,
  type SubtractRecord,
  type IntersectRecord,
  type ClosestRecord
} from '@/services/comparison'

expectTypeOf(subtract).returns.resolves.toEqualTypeOf<SubtractRecord[]>()
expectTypeOf(intersect).returns.resolves.toEqualTypeOf<IntersectRecord[]>()
expectTypeOf(closest).returns.resolves.toEqualTypeOf<ClosestRecord[]>()
