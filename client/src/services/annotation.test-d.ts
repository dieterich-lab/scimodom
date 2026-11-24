import { expectTypeOf } from 'vitest'
import { type Annotation, annotationCache, getEnsemblBrowseUrl } from '@/services/annotation'

expectTypeOf(annotationCache.getData).returns.resolves.toEqualTypeOf<readonly Annotation[]>()
expectTypeOf(getEnsemblBrowseUrl).returns.resolves.toEqualTypeOf<string | null>()
