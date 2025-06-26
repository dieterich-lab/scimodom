import { expectTypeOf } from 'vitest'
import {
  login,
  changePassword,
  resetPassword,
  registerUser,
  requestPasswordReset
} from '@/services/user'

expectTypeOf(login).returns.resolves.toEqualTypeOf<void>()
expectTypeOf(changePassword).returns.resolves.toEqualTypeOf<void>()
expectTypeOf(resetPassword).returns.resolves.toEqualTypeOf<void>()
expectTypeOf(registerUser).returns.resolves.toEqualTypeOf<void>()
expectTypeOf(requestPasswordReset).returns.resolves.toEqualTypeOf<void>()
