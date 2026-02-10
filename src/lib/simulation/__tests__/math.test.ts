/**
 * Unit tests for mathematical utility functions
 *
 * Tests cover: matEye, matAdd, matSub, matMul, matVec, matT, matInv2, hypot
 * All matrix operations are verified against known analytical results.
 */

import { describe, it, expect } from 'vitest'
import {
  matEye,
  matAdd,
  matSub,
  matMul,
  matVec,
  matT,
  matInv2,
  hypot,
} from '../math'

describe('Math Utilities', () => {
  describe('matEye', () => {
    it('should create identity matrix of given size', () => {
      const I = matEye(3)
      expect(I).toEqual([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
      ])
    })

    it('should create scaled identity matrix', () => {
      const I = matEye(2, 5)
      expect(I).toEqual([
        [5, 0],
        [0, 5],
      ])
    })

    it('should create 1x1 identity', () => {
      const I = matEye(1)
      expect(I).toEqual([[1]])
    })

    it('should have correct dimensions for 4x4', () => {
      const I = matEye(4)
      expect(I.length).toBe(4)
      for (let i = 0; i < 4; i++) {
        expect(I[i].length).toBe(4)
      }
    })

    it('should have zeros off-diagonal', () => {
      const I = matEye(3, 7)
      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
          if (i === j) {
            expect(I[i][j]).toBe(7)
          } else {
            expect(I[i][j]).toBe(0)
          }
        }
      }
    })
  })

  describe('matAdd', () => {
    it('should add two matrices element-wise', () => {
      const A = [
        [1, 2],
        [3, 4],
      ]
      const B = [
        [5, 6],
        [7, 8],
      ]
      const C = matAdd(A, B)
      expect(C).toEqual([
        [6, 8],
        [10, 12],
      ])
    })

    it('should handle zero matrices (additive identity)', () => {
      const A = [
        [1, 2],
        [3, 4],
      ]
      const Z = [
        [0, 0],
        [0, 0],
      ]
      const C = matAdd(A, Z)
      expect(C).toEqual(A)
    })

    it('should be commutative: A + B = B + A', () => {
      const A = [
        [1, 3],
        [5, 7],
      ]
      const B = [
        [2, 4],
        [6, 8],
      ]
      expect(matAdd(A, B)).toEqual(matAdd(B, A))
    })
  })

  describe('matSub', () => {
    it('should subtract two matrices element-wise', () => {
      const A = [
        [5, 6],
        [7, 8],
      ]
      const B = [
        [1, 2],
        [3, 4],
      ]
      const C = matSub(A, B)
      expect(C).toEqual([
        [4, 4],
        [4, 4],
      ])
    })

    it('should return zero matrix when subtracting a matrix from itself', () => {
      const A = [
        [1, 2],
        [3, 4],
      ]
      const C = matSub(A, A)
      expect(C).toEqual([
        [0, 0],
        [0, 0],
      ])
    })
  })

  describe('matMul', () => {
    it('should multiply two 2x2 matrices correctly', () => {
      // A = [[1,2],[3,4]], B = [[2,0],[1,2]]
      // C[0][0] = 1*2 + 2*1 = 4
      // C[0][1] = 1*0 + 2*2 = 4
      // C[1][0] = 3*2 + 4*1 = 10
      // C[1][1] = 3*0 + 4*2 = 8
      const A = [
        [1, 2],
        [3, 4],
      ]
      const B = [
        [2, 0],
        [1, 2],
      ]
      const C = matMul(A, B)
      expect(C).toEqual([
        [4, 4],
        [10, 8],
      ])
    })

    it('should multiply by identity and return original', () => {
      const A = [
        [1, 2],
        [3, 4],
      ]
      const I = matEye(2)
      const C = matMul(A, I)
      expect(C).toEqual(A)
    })

    it('should handle non-square matrices (1x3 times 3x1 = 1x1)', () => {
      const A = [[1, 2, 3]] // 1x3
      const B = [[1], [2], [3]] // 3x1
      const C = matMul(A, B) // 1x1: 1*1 + 2*2 + 3*3 = 14
      expect(C).toEqual([[14]])
    })

    it('should handle non-square matrices (2x3 times 3x2 = 2x2)', () => {
      const A = [
        [1, 0, 2],
        [0, 3, 1],
      ] // 2x3
      const B = [
        [1, 2],
        [3, 0],
        [0, 1],
      ] // 3x2
      // C[0][0] = 1*1 + 0*3 + 2*0 = 1
      // C[0][1] = 1*2 + 0*0 + 2*1 = 4
      // C[1][0] = 0*1 + 3*3 + 1*0 = 9
      // C[1][1] = 0*2 + 3*0 + 1*1 = 1
      const C = matMul(A, B)
      expect(C).toEqual([
        [1, 4],
        [9, 1],
      ])
    })
  })

  describe('matVec', () => {
    it('should multiply matrix by vector', () => {
      const A = [
        [1, 2],
        [3, 4],
      ]
      const x = new Float64Array([2, 3])
      const y = matVec(A, x)

      expect(y.length).toBe(2)
      expect(y[0]).toBe(8) // 1*2 + 2*3
      expect(y[1]).toBe(18) // 3*2 + 4*3
    })

    it('should return zero vector for zero input', () => {
      const A = [
        [1, 2],
        [3, 4],
      ]
      const x = new Float64Array([0, 0])
      const y = matVec(A, x)

      expect(y[0]).toBe(0)
      expect(y[1]).toBe(0)
    })

    it('should return Float64Array', () => {
      const A = [[1, 0], [0, 1]]
      const x = new Float64Array([5, 7])
      const y = matVec(A, x)

      expect(y).toBeInstanceOf(Float64Array)
    })
  })

  describe('matT', () => {
    it('should transpose a 2x3 matrix to 3x2', () => {
      const A = [
        [1, 2, 3],
        [4, 5, 6],
      ]
      const AT = matT(A)
      expect(AT).toEqual([
        [1, 4],
        [2, 5],
        [3, 6],
      ])
    })

    it('should transpose identity to itself', () => {
      const I = matEye(3)
      const IT = matT(I)
      expect(IT).toEqual(I)
    })

    it('should satisfy (A^T)^T = A', () => {
      const A = [
        [1, 2, 3],
        [4, 5, 6],
      ]
      const ATT = matT(matT(A))
      expect(ATT).toEqual(A)
    })

    it('should transpose a square matrix correctly', () => {
      const A = [
        [1, 2],
        [3, 4],
      ]
      const AT = matT(A)
      expect(AT).toEqual([
        [1, 3],
        [2, 4],
      ])
    })
  })

  describe('matInv2', () => {
    it('should invert a 2x2 matrix such that A * A_inv = I', () => {
      const A = [
        [4, 7],
        [2, 6],
      ]
      const Ainv = matInv2(A)

      // Verify A * Ainv = I
      const product = matMul(A, Ainv)

      expect(product[0][0]).toBeCloseTo(1, 10)
      expect(product[0][1]).toBeCloseTo(0, 10)
      expect(product[1][0]).toBeCloseTo(0, 10)
      expect(product[1][1]).toBeCloseTo(1, 10)
    })

    it('should invert identity to identity', () => {
      const I = [
        [1, 0],
        [0, 1],
      ]
      const Iinv = matInv2(I)

      expect(Iinv[0][0]).toBeCloseTo(1, 10)
      expect(Iinv[0][1]).toBeCloseTo(0, 10)
      expect(Iinv[1][0]).toBeCloseTo(0, 10)
      expect(Iinv[1][1]).toBeCloseTo(1, 10)
    })

    it('should handle near-singular matrices without throwing', () => {
      const A = [
        [1, 2],
        [2, 4.00001],
      ] // Nearly singular (det ~ 0.00001)
      const Ainv = matInv2(A)

      expect(Array.isArray(Ainv)).toBe(true)
      expect(Ainv.length).toBe(2)
      expect(Ainv[0].length).toBe(2)
    })

    it('should produce correct determinant-based formula', () => {
      // For A = [[a,b],[c,d]], A^-1 = (1/det) * [[d,-b],[-c,a]]
      const A = [
        [3, 1],
        [5, 2],
      ]
      const det = 3 * 2 - 1 * 5 // = 1
      const Ainv = matInv2(A)

      expect(Ainv[0][0]).toBeCloseTo(2 / det, 10) // d/det
      expect(Ainv[0][1]).toBeCloseTo(-1 / det, 10) // -b/det
      expect(Ainv[1][0]).toBeCloseTo(-5 / det, 10) // -c/det
      expect(Ainv[1][1]).toBeCloseTo(3 / det, 10) // a/det
    })
  })

  describe('hypot', () => {
    it('should compute Euclidean distance for 3-4-5 triangle', () => {
      expect(hypot(3, 4)).toBe(5)
    })

    it('should return 0 for zero inputs', () => {
      expect(hypot(0, 0)).toBe(0)
    })

    it('should handle negative values (symmetric)', () => {
      expect(hypot(-3, -4)).toBe(5)
      expect(hypot(3, -4)).toBe(5)
      expect(hypot(-3, 4)).toBe(5)
    })

    it('should compute sqrt(2) for unit diagonal', () => {
      expect(hypot(1, 1)).toBeCloseTo(Math.SQRT2, 10)
    })
  })
})
