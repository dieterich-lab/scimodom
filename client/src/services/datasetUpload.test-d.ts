import { expectTypeOf } from 'vitest'
import { uploadTemporaryDataset, type UploadedFile } from '@/services/datasetUpload'

expectTypeOf(uploadTemporaryDataset).returns.resolves.toEqualTypeOf<UploadedFile>()
