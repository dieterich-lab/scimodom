import { expectTypeOf } from 'vitest'
import { type DetectionMethod, detectionMethodCache } from '@/services/detectionMethod'

expectTypeOf(detectionMethodCache.getPromise).returns.resolves.toEqualTypeOf<DetectionMethod[]>()
expectTypeOf(detectionMethodCache.getData).returns.resolves.toEqualTypeOf<
  Readonly<DetectionMethod[]>
>()
