import { expectTypeOf } from 'vitest'
import { type AxiosResponse } from 'axios'
import { HTTP, HTTPAuth, handleRequest } from '@/services/API'

interface A {
  a: number
}

// the response type is declared once, at the HTTP call ...
expectTypeOf(HTTP.get<A>('/x')).toEqualTypeOf<Promise<AxiosResponse<A>>>()
expectTypeOf(HTTP.delete<void>('/x')).toEqualTypeOf<Promise<AxiosResponse<void>>>()
expectTypeOf(HTTPAuth.post<A>('/x', {})).toEqualTypeOf<Promise<AxiosResponse<A>>>()
expectTypeOf(HTTPAuth.put<A>('/x', {})).toEqualTypeOf<Promise<AxiosResponse<A>>>()
expectTypeOf(HTTPAuth.patch<A>('/x', {})).toEqualTypeOf<Promise<AxiosResponse<A>>>()
expectTypeOf(handleRequest(HTTP.get<A>('/x'))).toEqualTypeOf<Promise<A>>()

// ... and a missing declaration is `unknown`, not `any`
expectTypeOf(HTTP.get('/x')).toEqualTypeOf<Promise<AxiosResponse<unknown>>>()
expectTypeOf(HTTPAuth.patch('/x', {})).toEqualTypeOf<Promise<AxiosResponse<unknown>>>()
expectTypeOf(handleRequest(HTTP.get('/x'))).toEqualTypeOf<Promise<unknown>>()

// contradicting declarations
// @ts-expect-error
handleRequest<{ b: string }>(HTTP.get<A>('/x'))
