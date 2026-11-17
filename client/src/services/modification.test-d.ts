import { expectTypeOf } from 'vitest'

import {
  getSitesCount,
  getModifications,
  getTargetSites,
  getGenomicContext,
  getSiteWiseInfo,
  type ModificationResponse,
  type SiteWiseInfo,
  type SiteCountResponse
} from '@/services/modification'
import { type Bed6Record } from '@/utils/bed6'

expectTypeOf(getSitesCount).returns.resolves.toEqualTypeOf<SiteCountResponse>()
expectTypeOf(getModifications).returns.resolves.toEqualTypeOf<ModificationResponse>()
expectTypeOf(getTargetSites).returns.resolves.toEqualTypeOf<Bed6Record[]>()
expectTypeOf(getGenomicContext).returns.resolves.toEqualTypeOf<string>()
expectTypeOf(getSiteWiseInfo).returns.resolves.toEqualTypeOf<SiteWiseInfo[]>()
