import { expectTypeOf } from 'vitest'
import { postTemporaryFile } from '@/services/upload'

expectTypeOf(postTemporaryFile).returns.resolves.toEqualTypeOf<{ file_id: string }>()
