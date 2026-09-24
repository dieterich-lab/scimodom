import { expectTypeOf } from 'vitest'
import {
  uploadTemporaryDataset,
  type UploadedFile,
  type UploadResponse
} from '@/services/datasetUpload'

expectTypeOf(uploadTemporaryDataset).returns.resolves.toEqualTypeOf<UploadedFile>()
expectTypeOf<UploadedFile>().toEqualTypeOf<{ id: string; name: string }>()
expectTypeOf<UploadResponse>().toEqualTypeOf<{ file_id: string }>()
