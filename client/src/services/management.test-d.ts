import { expectTypeOf } from 'vitest'
import {
  postDataset,
  postProject,
  type DatasetPostResponse,
  type ProjectPostResponse
} from '@/services/management'

expectTypeOf(postDataset).returns.resolves.toEqualTypeOf<DatasetPostResponse>()
expectTypeOf(postProject).returns.resolves.toEqualTypeOf<ProjectPostResponse>()
