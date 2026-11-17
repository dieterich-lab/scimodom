import { expectTypeOf } from 'vitest'
import {
  allDatasetsCache,
  allDatasetsByIdCache,
  myDatasetsCache,
  myDatasetsByIdCache,
  getDatasetsByTaxaId,
  getDatasetCount,
  type Dataset,
  type DatasetCountResponse
} from '@/services/dataset'

expectTypeOf(allDatasetsCache.getPromise).returns.resolves.toEqualTypeOf<Dataset[]>()
expectTypeOf(myDatasetsCache.getPromise).returns.resolves.toEqualTypeOf<Dataset[]>()
expectTypeOf(getDatasetsByTaxaId).returns.resolves.toEqualTypeOf<Readonly<Dataset[]>>()
expectTypeOf(allDatasetsByIdCache.getData).returns.resolves.toEqualTypeOf<
  Readonly<Map<string, Dataset>>
>()
expectTypeOf(myDatasetsByIdCache.getData).returns.resolves.toEqualTypeOf<
  Readonly<Map<string, Dataset>>
>()
expectTypeOf(getDatasetCount).returns.resolves.toEqualTypeOf<DatasetCountResponse>()
