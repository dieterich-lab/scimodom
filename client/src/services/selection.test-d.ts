import { expectTypeOf } from 'vitest'
import {
  selectionsCache,
  getSelectionsByIds,
  getSelectionsByTaxaId,
  getModificationTypesByRnaType,
  getCtos,
  getCtosByModificationIds,
  getTechnologiesByModificationIdsAndOrganismId,
  getProjectSelections,
  type ProjectSelection,
  type Selection,
  type ModificationType,
  type Cto,
  type Technology
} from '@/services/selection'

expectTypeOf(selectionsCache.getPromise).returns.resolves.toEqualTypeOf<Selection[]>()
expectTypeOf(getSelectionsByIds).returns.resolves.toEqualTypeOf<Selection[]>()
expectTypeOf(getSelectionsByTaxaId).returns.resolves.toEqualTypeOf<Selection[]>()
expectTypeOf(getProjectSelections).returns.resolves.toEqualTypeOf<ProjectSelection[]>()
expectTypeOf(getModificationTypesByRnaType).returns.toEqualTypeOf<ModificationType[]>()
expectTypeOf(getCtos).returns.toEqualTypeOf<Cto[]>()
expectTypeOf(getCtosByModificationIds).returns.toEqualTypeOf<Cto[]>()
expectTypeOf(getTechnologiesByModificationIdsAndOrganismId).returns.toEqualTypeOf<Technology[]>()
expectTypeOf<Selection>().toMatchTypeOf<ProjectSelection>()
