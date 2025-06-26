import { expectTypeOf } from 'vitest'
import {
  selectionsCache,
  getCtosByModificationIds,
  getTechnologiesByModificationIdsAndOrganismId,
  getSelectionsByIds,
  getSelectionsByTaxaId,
  getTechnologiesByIds,
  getModificationTypesByRnaName,
  type Selection,
  type ModificationType,
  type Cto,
  type Technology
} from '@/services/selection'

expectTypeOf(selectionsCache.getPromise).returns.resolves.toEqualTypeOf<Selection[]>()
expectTypeOf(getCtosByModificationIds).returns.resolves.toEqualTypeOf<Cto[]>()
expectTypeOf(getTechnologiesByModificationIdsAndOrganismId).returns.resolves.toEqualTypeOf<
  Technology[]
>()
expectTypeOf(getSelectionsByIds).returns.resolves.toEqualTypeOf<Selection[]>()
expectTypeOf(getSelectionsByTaxaId).returns.resolves.toEqualTypeOf<Selection[]>()
expectTypeOf(getTechnologiesByIds).returns.resolves.toEqualTypeOf<Technology[]>()
expectTypeOf(getModificationTypesByRnaName).returns.resolves.toEqualTypeOf<ModificationType[]>()
