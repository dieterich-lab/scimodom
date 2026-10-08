import { expectTypeOf } from 'vitest'
import { type DetectionMethod, detectionMethodCache } from '@/services/detection-method'

expectTypeOf(detectionMethodCache.getPromise).returns.resolves.toEqualTypeOf<DetectionMethod[]>()
expectTypeOf(detectionMethodCache.getData).returns.resolves.toEqualTypeOf<
  Readonly<DetectionMethod[]>
>()
