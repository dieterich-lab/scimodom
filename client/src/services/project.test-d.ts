import { expectTypeOf } from 'vitest'
import {
  allProjectsCache,
  allProjectsByIdCache,
  myProjectsCache,
  myProjectsByIdCache,
  type Project
} from '@/services/project'

expectTypeOf(allProjectsCache.getPromise).returns.resolves.toEqualTypeOf<Project[]>()
expectTypeOf(myProjectsCache.getPromise).returns.resolves.toEqualTypeOf<Project[]>()
expectTypeOf(allProjectsByIdCache.getData).returns.resolves.toEqualTypeOf<
  Readonly<Map<string, Project>>
>()
expectTypeOf(myProjectsByIdCache.getData).returns.resolves.toEqualTypeOf<
  Readonly<Map<string, Project>>
>()
