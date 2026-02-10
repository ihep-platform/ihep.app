/**
 * Integration tests for the complete control system
 * Tests EKF + CBF + Controller working together
 */

import { describe, it, expect } from 'vitest'
import { initEKF, ekfStep } from '../ekf'
import { cbfAdjust, isSafe } from '../cbf'
import type { RobotState, Obstacle } from '../types'
import { hypot } from '../math'

describe('Integration Tests', () => {
  describe('EKF + Dynamics Integration', () => {
    it('should track true state with perfect measurements', () => {
      const trueState: RobotState = {
        p: { x: 50, y: 50 },
        v: { x: 10, y: 5 },
      }

      let ekfState = initEKF(
        new Float64Array([55, 48, 8, 6]), // Slightly wrong
        100
      )

      const a = [1, 1]

      for (let i = 0; i < 20; i++) {
        trueState.p.x += trueState.v.x * (1 / 60) + 0.5 * a[0] * (1 / 60) ** 2
        trueState.p.y += trueState.v.y * (1 / 60) + 0.5 * a[1] * (1 / 60) ** 2
        trueState.v.x += a[0] * (1 / 60)
        trueState.v.y += a[1] * (1 / 60)

        const z = new Float64Array([trueState.p.x, trueState.p.y])
        ekfState = ekfStep(ekfState, a, z)
      }

      expect(Math.abs(ekfState.x[0] - trueState.p.x)).toBeLessThan(1)
      expect(Math.abs(ekfState.x[1] - trueState.p.y)).toBeLessThan(1)
    })

    it('should handle noisy measurements', () => {
      const trueState: RobotState = {
        p: { x: 100, y: 100 },
        v: { x: 0, y: 0 },
      }

      let ekfState = initEKF(
        new Float64Array([100, 100, 0, 0]),
        200
      )

      const a = [0, 0]

      for (let i = 0; i < 30; i++) {
        const noise = 5
        const z = new Float64Array([
          trueState.p.x + (Math.random() - 0.5) * noise,
          trueState.p.y + (Math.random() - 0.5) * noise,
        ])

        ekfState = ekfStep(ekfState, a, z)
      }

      expect(Math.abs(ekfState.x[0] - trueState.p.x)).toBeLessThan(10)
      expect(Math.abs(ekfState.x[1] - trueState.p.y)).toBeLessThan(10)
    })
  })

  describe('CBF + Control Integration', () => {
    it('should maintain safety while reaching target', () => {
      const obstacle: Obstacle = {
        c: { x: 150, y: 100 },
        r: 30,
      }

      const target = { x: 250, y: 100 }
      const eps = 20

      let state: RobotState = {
        p: { x: 50, y: 100 },
        v: { x: 0, y: 0 },
      }

      const dt = 1 / 60
      const maxSteps = 800
      let safetyViolations = 0
      let minSafeDist = Infinity

      for (let i = 0; i < maxSteps; i++) {
        const dx = target.x - state.p.x
        const dy = target.y - state.p.y
        const dist = hypot(dx, dy)

        if (dist < 5) break

        const speed = 35
        const a_nom = [
          (dx / dist) * speed - 1.2 * state.v.x,
          (dy / dist) * speed - 1.2 * state.v.y,
        ]

        const cbfResult = cbfAdjust(a_nom, state, obstacle, eps, 4.5)

        state.p.x += state.v.x * dt + 0.5 * cbfResult.a[0] * dt * dt
        state.p.y += state.v.y * dt + 0.5 * cbfResult.a[1] * dt * dt
        state.v.x += cbfResult.a[0] * dt
        state.v.y += cbfResult.a[1] * dt

        const safeDist =
          hypot(state.p.x - obstacle.c.x, state.p.y - obstacle.c.y) -
          obstacle.r
        minSafeDist = Math.min(minSafeDist, safeDist)

        if (safeDist < eps * 0.45) {
          safetyViolations++
        }
      }

      expect(safetyViolations).toBeLessThan(5)
      expect(minSafeDist).toBeGreaterThan(eps * 0.4)
    })
  })

  describe('Full System Integration (EKF + CBF + Control)', () => {
    it('should control robot with state estimation and safety', () => {
      let trueState: RobotState = {
        p: { x: 50, y: 50 },
        v: { x: 0, y: 0 },
      }

      let ekfState = initEKF(
        new Float64Array([52, 48, 0, 0]),
        150
      )

      const obstacle: Obstacle = {
        c: { x: 150, y: 75 },
        r: 25,
      }

      const target = { x: 250, y: 100 }
      const eps = 20
      const dt = 1 / 60

      let safetyViolations = 0

      for (let i = 0; i < 1000; i++) {
        const dx = target.x - ekfState.x[0]
        const dy = target.y - ekfState.x[1]
        const dist = hypot(dx, dy)

        if (dist < 10) break

        const speed = 30
        const a_nom = [
          (dx / dist) * speed - 1.8 * ekfState.x[2],
          (dy / dist) * speed - 1.8 * ekfState.x[3],
        ]

        const cbfResult = cbfAdjust(a_nom, trueState, obstacle, eps, 4.5)

        trueState.p.x +=
          trueState.v.x * dt + 0.5 * cbfResult.a[0] * dt * dt
        trueState.p.y +=
          trueState.v.y * dt + 0.5 * cbfResult.a[1] * dt * dt
        trueState.v.x += cbfResult.a[0] * dt
        trueState.v.y += cbfResult.a[1] * dt

        const safeDist =
          hypot(trueState.p.x - obstacle.c.x, trueState.p.y - obstacle.c.y) -
          obstacle.r

        if (safeDist < eps * 0.4) {
          safetyViolations++
        }

        const noise = 3
        const z = new Float64Array([
          trueState.p.x + (Math.random() - 0.5) * noise,
          trueState.p.y + (Math.random() - 0.5) * noise,
        ])

        ekfState = ekfStep(ekfState, cbfResult.a, z)
      }

      expect(safetyViolations).toBeLessThan(10)

      const finalDist = hypot(
        trueState.p.x - target.x,
        trueState.p.y - target.y
      )
      const initialDist = hypot(50 - target.x, 50 - target.y)
      expect(finalDist).toBeLessThan(initialDist * 0.75)

      expect(Math.abs(ekfState.x[0] - trueState.p.x)).toBeLessThan(25)
      expect(Math.abs(ekfState.x[1] - trueState.p.y)).toBeLessThan(25)
    })
  })

  describe('Performance characteristics', () => {
    it('should complete 1000-step simulation in under 1 second', () => {
      const startTime = Date.now()

      let state: RobotState = {
        p: { x: 0, y: 0 },
        v: { x: 0, y: 0 },
      }

      let ekfState = initEKF(new Float64Array([0, 0, 0, 0]), 100)

      const obstacle: Obstacle = {
        c: { x: 100, y: 100 },
        r: 30,
      }

      for (let i = 0; i < 1000; i++) {
        const a_nom = [10, 10]
        const cbfResult = cbfAdjust(a_nom, state, obstacle, 15)

        const dt = 1 / 60
        state.p.x += state.v.x * dt + 0.5 * cbfResult.a[0] * dt * dt
        state.p.y += state.v.y * dt + 0.5 * cbfResult.a[1] * dt * dt
        state.v.x += cbfResult.a[0] * dt
        state.v.y += cbfResult.a[1] * dt

        const z = new Float64Array([state.p.x, state.p.y])
        ekfState = ekfStep(ekfState, cbfResult.a, z)
      }

      const elapsedTime = Date.now() - startTime

      expect(elapsedTime).toBeLessThan(1000)
    })
  })
})
