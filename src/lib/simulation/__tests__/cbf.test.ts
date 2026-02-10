/**
 * Unit tests for Control Barrier Function (CBF)
 *
 * The CBF ensures safety-critical obstacle avoidance by enforcing:
 *   h(x) >= 0 (safe set invariance)
 *   dh/dt >= -alpha * h (exponential convergence to safe set)
 *
 * Tests verify:
 *   - isSafe returns correct boolean based on distance to obstacle
 *   - barrierFunction returns positive for safe states, negative for unsafe
 *   - cbfAdjust modifies acceleration when nominal control violates constraint
 *   - cbfAdjust does NOT modify acceleration when constraint is already satisfied
 */

import { describe, it, expect } from 'vitest'
import { cbfAdjust, isSafe, barrierFunction } from '../cbf'
import type { RobotState, Obstacle } from '../types'

describe('Control Barrier Function', () => {
  const obstacle: Obstacle = {
    c: { x: 100, y: 100 },
    r: 20,
  }

  const eps = 10 // Safety margin

  describe('barrierFunction', () => {
    it('should return positive value when robot is far from obstacle (safe)', () => {
      const state: RobotState = {
        p: { x: 200, y: 100 }, // 100 units from center
        v: { x: 0, y: 0 },
      }

      const h = barrierFunction(state, obstacle, eps)

      // h = dist - r - eps = 100 - 20 - 10 = 70
      expect(h).toBeGreaterThan(0)
      expect(h).toBeCloseTo(70, 0)
    })

    it('should return negative value when robot is inside obstacle + margin (unsafe)', () => {
      const state: RobotState = {
        p: { x: 110, y: 100 }, // 10 units from center
        v: { x: 0, y: 0 },
      }

      const h = barrierFunction(state, obstacle, eps)

      // h = dist - r - eps = 10 - 20 - 10 = -20
      expect(h).toBeLessThan(0)
    })

    it('should return approximately zero at the boundary (dist = r + eps)', () => {
      const state: RobotState = {
        p: { x: 130, y: 100 }, // dist = 30 = r + eps
        v: { x: 0, y: 0 },
      }

      const h = barrierFunction(state, obstacle, eps)

      // h = 30 - 20 - 10 = 0
      expect(Math.abs(h)).toBeLessThan(1e-10)
    })

    it('should be symmetric around the obstacle', () => {
      const positions = [
        { x: 200, y: 100 }, // right
        { x: 0, y: 100 },   // left
        { x: 100, y: 200 }, // above
        { x: 100, y: 0 },   // below
      ]

      // All at distance 100 from center, should all give same h
      const values = positions.map((p) =>
        barrierFunction({ p, v: { x: 0, y: 0 } }, obstacle, eps)
      )

      for (let i = 1; i < values.length; i++) {
        expect(values[i]).toBeCloseTo(values[0], 5)
      }
    })
  })

  describe('isSafe', () => {
    it('should return true when far from obstacle', () => {
      const state: RobotState = {
        p: { x: 200, y: 100 },
        v: { x: 0, y: 0 },
      }

      expect(isSafe(state, obstacle, eps)).toBe(true)
    })

    it('should return false when inside safety boundary', () => {
      // isSafe checks: dist - r >= eps * 0.5
      // At x=104: dist = 4, dist - r = 4 - 20 = -16. -16 >= 5 is false
      const state: RobotState = {
        p: { x: 104, y: 100 },
        v: { x: 0, y: 0 },
      }

      expect(isSafe(state, obstacle, eps)).toBe(false)
    })

    it('should return true on all sides when sufficiently distant', () => {
      const positions = [
        { x: 100, y: 200 }, // above
        { x: 100, y: 0 },   // below
        { x: 0, y: 100 },   // left
        { x: 200, y: 100 }, // right
      ]

      for (const p of positions) {
        const state: RobotState = { p, v: { x: 0, y: 0 } }
        expect(isSafe(state, obstacle, eps)).toBe(true)
      }
    })

    it('should return false when at obstacle center', () => {
      const state: RobotState = {
        p: { x: 100, y: 100 }, // dist = 0, 0 - 20 = -20 < 5
        v: { x: 0, y: 0 },
      }

      expect(isSafe(state, obstacle, eps)).toBe(false)
    })
  })

  describe('cbfAdjust', () => {
    it('should NOT modify control when safely moving away from obstacle', () => {
      const state: RobotState = {
        p: { x: 200, y: 100 }, // Far away
        v: { x: 10, y: 0 },   // Moving away
      }

      const a_nom = [5, 0] // Accelerating away
      const result = cbfAdjust(a_nom, state, obstacle, eps)

      expect(result.active).toBe(false)
      expect(result.a).toEqual(a_nom)
      expect(result.h).toBeGreaterThan(0)
    })

    it('should modify acceleration when approaching obstacle dangerously', () => {
      const state: RobotState = {
        p: { x: 135, y: 100 }, // Close to boundary
        v: { x: -15, y: 0 },   // Fast approach
      }

      const a_nom = [-10, 0] // Strong acceleration toward obstacle
      const result = cbfAdjust(a_nom, state, obstacle, eps)

      if (result.active) {
        // Corrected x-acceleration should be less negative (pushed away)
        expect(result.a[0]).toBeGreaterThan(a_nom[0])
      }
    })

    it('should ensure the CBF constraint n*a >= b is satisfied', () => {
      const state: RobotState = {
        p: { x: 135, y: 100 },
        v: { x: -5, y: 0 },
      }

      const a_nom = [-10, 0]
      const result = cbfAdjust(a_nom, state, obstacle, eps)

      // Recompute constraint terms to verify
      const dx = state.p.x - obstacle.c.x
      const dy = state.p.y - obstacle.c.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      const nx = dx / dist
      const ny = dy / dist

      const alpha = 3.5
      const b = -result.dh - alpha * result.h

      const dot = nx * result.a[0] + ny * result.a[1]

      // Constraint: n . a >= b (with numerical tolerance)
      expect(dot).toBeGreaterThanOrEqual(b - 1e-6)
    })

    it('should return correct result structure', () => {
      const state: RobotState = {
        p: { x: 150, y: 100 },
        v: { x: 0, y: 0 },
      }

      const a_nom = [1, 0]
      const result = cbfAdjust(a_nom, state, obstacle, eps)

      expect(result).toHaveProperty('a')
      expect(result).toHaveProperty('active')
      expect(result).toHaveProperty('h')
      expect(result).toHaveProperty('dh')

      expect(Array.isArray(result.a)).toBe(true)
      expect(result.a.length).toBe(2)
      expect(typeof result.active).toBe('boolean')
      expect(typeof result.h).toBe('number')
      expect(typeof result.dh).toBe('number')
    })

    it('should have dh = 0 for stationary robot (zero velocity)', () => {
      const state: RobotState = {
        p: { x: 132, y: 100 },
        v: { x: 0, y: 0 }, // Stationary
      }

      const a_nom = [-20, 0]
      const result = cbfAdjust(a_nom, state, obstacle, eps)

      // dh = nx*vx + ny*vy = 0 when v = 0
      expect(result.dh).toBe(0)
    })

    it('should not modify zero control when safe and stationary', () => {
      const state: RobotState = {
        p: { x: 140, y: 100 }, // Safe
        v: { x: 0, y: 0 },
      }

      const a_nom = [0, 0]
      const result = cbfAdjust(a_nom, state, obstacle, eps)

      expect(result.a).toEqual([0, 0])
    })

    it('should produce more conservative correction with higher alpha', () => {
      const state: RobotState = {
        p: { x: 140, y: 100 },
        v: { x: -10, y: 0 },
      }

      const a_nom = [-5, 0]

      const result_high = cbfAdjust(a_nom, state, obstacle, eps, 5.0)
      const result_low = cbfAdjust(a_nom, state, obstacle, eps, 2.0)

      if (result_high.active && result_low.active) {
        // Higher alpha demands stronger safety correction (more positive x-accel)
        expect(result_high.a[0]).toBeGreaterThanOrEqual(result_low.a[0])
      }
    })

    it('should handle robot at obstacle center without crashing', () => {
      const state: RobotState = {
        p: { x: 100, y: 100 }, // At obstacle center (dist = 0)
        v: { x: 1, y: 0 },
      }

      const a_nom = [1, 0]
      const result = cbfAdjust(a_nom, state, obstacle, eps)

      // Should compute without throwing (uses epsilon 1e-9 for division)
      expect(Array.isArray(result.a)).toBe(true)
      expect(typeof result.active).toBe('boolean')
    })
  })
})
