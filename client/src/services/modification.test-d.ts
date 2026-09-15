import { expectTypeOf } from 'vitest'

import {
  getModifications,
  getTargetSites,
  getGenomicContext,
  getSiteWiseInfo,
  type ModificationResponse,
  type SiteWiseInfo
} from '@/services/modification'
import { type Bed6Record } from '@/utils/bed6'

expectTypeOf(getModifications).returns.resolves.toEqualTypeOf<ModificationResponse>()

expectTypeOf(getTargetSites).returns.resolves.toEqualTypeOf<Bed6Record[]>()

expectTypeOf(getGenomicContext).returns.resolves.toEqualTypeOf<string>()

expectTypeOf(getSiteWiseInfo).returns.resolves.toEqualTypeOf<SiteWiseInfo[]>()
