import { expectTypeOf } from 'vitest'
import { uploadTemporaryDataset, type UploadedFile } from '@/services/dataset-upload'

expectTypeOf(uploadTemporaryDataset).returns.resolves.toEqualTypeOf<UploadedFile>()
