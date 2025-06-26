import { expectTypeOf } from 'vitest'
import {
  getBamFilesByDatasetId,
  deleteBamFile,
  getBamFileDownLoadURL,
  type BamFile
} from '@/services/bamfile'
import { type DialogStateStore } from '@/stores/DialogState'

expectTypeOf(getBamFilesByDatasetId).returns.resolves.toEqualTypeOf<BamFile[]>()
expectTypeOf(deleteBamFile).returns.resolves.toEqualTypeOf<void>()
expectTypeOf(getBamFileDownLoadURL).returns.toEqualTypeOf<string>()
