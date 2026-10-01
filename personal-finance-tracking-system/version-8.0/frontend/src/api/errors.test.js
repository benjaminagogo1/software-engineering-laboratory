import { describe, expect, it } from 'vitest'

import { ApiError, apiErrorFrom } from './errors'

describe('ApiError', () => {
  it('flags a 401 so the session can be dropped in one place', () => {
    expect(new ApiError(401, 'Not authenticated').isUnauthorized).toBe(true)
    expect(new ApiError(403, 'Invalid CSRF token').isUnauthorized).toBe(false)
  })
})

describe('apiErrorFrom', () => {
  it('uses the sentence a raised HTTPException sent', () => {
    const error = apiErrorFrom(400, { detail: 'Amount must be greater than zero' })

    expect(error.message).toBe('Amount must be greater than zero')
    expect(error.status).toBe(400)
    expect(error.fieldErrors).toEqual({})
  })

  it('flattens a pydantic validation array instead of rendering [object Object]', () => {
    const error = apiErrorFrom(422, {
      detail: [
        {
          loc: ['body', 'amount'],
          msg: 'Input should be a valid number',
          type: 'float_parsing',
        },
      ],
    })

    expect(error.message).toBe('amount: Input should be a valid number')
    expect(error.fieldErrors).toEqual({ amount: 'Input should be a valid number' })
  })

  it('keeps one message per field when several fail at once', () => {
    const error = apiErrorFrom(422, {
      detail: [
        { loc: ['body', 'amount'], msg: 'must be positive' },
        { loc: ['body', 'category'], msg: 'not an allowed value' },
      ],
    })

    expect(error.fieldErrors).toEqual({
      amount: 'must be positive',
      category: 'not an allowed value',
    })
  })

  it('keys a nested field by the field name, not the index', () => {
    const error = apiErrorFrom(422, {
      detail: [{ loc: ['body', 'items', 3, 'name'], msg: 'required' }],
    })

    expect(error.fieldErrors).toEqual({ name: 'required' })
  })

  it('falls back to a generic sentence for a body it does not recognise', () => {
    expect(apiErrorFrom(500, null).message).toMatch(/went wrong/)
    expect(apiErrorFrom(502, '<html>Bad Gateway</html>').message).toMatch(/went wrong/)
    expect(apiErrorFrom(422, { detail: [] }).message).toMatch(/went wrong/)
  })

  it('never puts a raw object into the message', () => {
    const error = apiErrorFrom(422, { detail: [{ loc: [], msg: 'nope' }] })

    expect(error.message).not.toContain('[object Object]')
  })
})
