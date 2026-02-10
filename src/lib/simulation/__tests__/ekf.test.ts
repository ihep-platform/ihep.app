/**
 * Unit tests for Extended Kalman Filter (EKF)
 *
 * The EKF implements state estimation for a 2D system with state [px, py, vx, vy].
 * Tests verify:
 *   - dynamics model integrates position/velocity correctly with dt = 1/60
 *   - Jacobian F has correct structure for the constant-velocity model
 *   - initEKF creates valid state with proper dimensions and covariance
 *   - ekfStep predict step preserves matrix dimensions
 *   - ekfStep update step corrects state toward measurement
 *   - Covariance decreases with repeated measurements (convergence)
 */

import { describe, it, expect } from 'vitest'
import { dynamics, F_jac, H_meas, Q, R, ekfStep, initEKF } from '../ekf'

const dt = 1 / 60

describe('Extended Kalman Filter', () => {
  describe('dynamics', () => {
    it('should predict next state with zero control input', () => {
      const x = new Float64Array([10, 20, 5, 3])
      const a = [0, 0]

      const x_next = dynamics(x, a)

      // px_next = px + vx*dt + 0.5*ax*dt^2 = 10 + 5/60
      expect(x_next[0]).toBeCloseTo(10 + 5 * dt, 10)
      // py_next = py + vy*dt + 0.5*ay*dt^2 = 20 + 3/60
      expect(x_next[1]).toBeCloseTo(20 + 3 * dt, 10)
      // vx_next = vx + ax*dt = 5
      expect(x_next[2]).toBe(5)
      // vy_next = vy + ay*dt = 3
      expect(x_next[3]).toBe(3)
    })

    it('should integrate acceleration correctly from rest', () => {
      const x = new Float64Array([0, 0, 0, 0])
      const a = [10, 20]

      const x_next = dynamics(x, a)

      // position: 0.5 * a * dt^2
      expect(x_next[0]).toBeCloseTo(0.5 * 10 * dt * dt, 10)
      expect(x_next[1]).toBeCloseTo(0.5 * 20 * dt * dt, 10)
      // velocity: a * dt
      expect(x_next[2]).toBeCloseTo(10 * dt, 10)
      expect(x_next[3]).toBeCloseTo(20 * dt, 10)
    })

    it('should handle negative velocities and accelerations', () => {
      const x = new Float64Array([100, 100, -10, -5])
      const a = [-20, -10]

      const x_next = dynamics(x, a)

      expect(x_next[0]).toBeLessThan(100)
      expect(x_next[1]).toBeLessThan(100)
      expect(x_next[2]).toBeLessThan(-10)
      expect(x_next[3]).toBeLessThan(-5)
    })

    it('should return a Float64Array of length 4', () => {
      const x = new Float64Array([0, 0, 0, 0])
      const result = dynamics(x, [1, 1])
      expect(result).toBeInstanceOf(Float64Array)
      expect(result.length).toBe(4)
    })
  })

  describe('F_jac', () => {
    it('should return correct 4x4 Jacobian structure', () => {
      const F = F_jac()

      expect(F.length).toBe(4)
      expect(F[0].length).toBe(4)

      // The Jacobian for constant-velocity model: I + dt in velocity->position blocks
      expect(F).toEqual([
        [1, 0, dt, 0],
        [0, 1, 0, dt],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
      ])
    })
  })

  describe('Measurement and noise matrices', () => {
    it('should observe position only via H_meas (2x4)', () => {
      expect(H_meas).toEqual([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
      ])
    })

    it('should have 4x4 diagonal process noise Q', () => {
      expect(Q.length).toBe(4)
      expect(Q[0].length).toBe(4)
      expect(Q[0][0]).toBe(2)
      expect(Q[1][1]).toBe(2)
      expect(Q[2][2]).toBe(6)
      expect(Q[3][3]).toBe(6)
    })

    it('should have 2x2 diagonal measurement noise R', () => {
      expect(R.length).toBe(2)
      expect(R[0].length).toBe(2)
      expect(R[0][0]).toBe(30)
      expect(R[1][1]).toBe(30)
    })
  })

  describe('initEKF', () => {
    it('should create valid EKF state with given initial state', () => {
      const x0 = new Float64Array([10, 20, 0, 0])
      const state = initEKF(x0, 100)

      // State vector should match input
      expect(state.x).toBe(x0)
      expect(state.x.length).toBe(4)

      // Covariance should be 4x4 scaled identity
      expect(state.P.length).toBe(4)
      expect(state.P[0].length).toBe(4)
      expect(state.P[0][0]).toBe(100)
      expect(state.P[1][1]).toBe(100)
      expect(state.P[2][2]).toBe(100)
      expect(state.P[3][3]).toBe(100)
      // Off-diagonal should be zero
      expect(state.P[0][1]).toBe(0)
      expect(state.P[1][0]).toBe(0)

      // Innovation should be zero-initialized
      expect(state.innovation.length).toBe(2)
      expect(state.innovation[0]).toBe(0)
      expect(state.innovation[1]).toBe(0)
    })

    it('should use default covariance of 200 when not specified', () => {
      const x0 = new Float64Array([0, 0, 0, 0])
      const state = initEKF(x0)

      expect(state.P[0][0]).toBe(200)
      expect(state.P[1][1]).toBe(200)
      expect(state.P[2][2]).toBe(200)
      expect(state.P[3][3]).toBe(200)
    })
  })

  describe('ekfStep', () => {
    it('should return state with correct dimensions after one step', () => {
      const x0 = new Float64Array([10, 20, 5, 3])
      const state = initEKF(x0, 100)

      const a = [0, 0]
      const z = new Float64Array([10, 20])

      const newState = ekfStep(state, a, z)

      expect(newState.x).toBeInstanceOf(Float64Array)
      expect(newState.x.length).toBe(4)
      expect(Array.isArray(newState.P)).toBe(true)
      expect(newState.P.length).toBe(4)
      expect(newState.P[0].length).toBe(4)
      expect(newState.innovation).toBeInstanceOf(Float64Array)
      expect(newState.innovation.length).toBe(2)
    })

    it('should move estimate toward measurement (update correction)', () => {
      const x0 = new Float64Array([100, 100, 0, 0])
      const state = initEKF(x0, 200)

      const a = [0, 0]
      // Measurement displaced from prior
      const z = new Float64Array([105, 98])

      const newState = ekfStep(state, a, z)

      // State should move toward measurement, not past it
      expect(newState.x[0]).toBeGreaterThan(100)
      expect(newState.x[0]).toBeLessThan(105)
      expect(newState.x[1]).toBeLessThan(100)
      expect(newState.x[1]).toBeGreaterThan(98)

      // Innovation should reflect measurement residual
      expect(Math.abs(newState.innovation[0])).toBeGreaterThan(0)
      expect(Math.abs(newState.innovation[1])).toBeGreaterThan(0)
    })

    it('should preserve matrix dimensions through multiple steps', () => {
      const x0 = new Float64Array([0, 0, 0, 0])
      let state = initEKF(x0, 100)

      for (let i = 0; i < 10; i++) {
        const a = [1, 1]
        const z = new Float64Array([i, i])
        state = ekfStep(state, a, z)

        expect(state.x.length).toBe(4)
        expect(state.P.length).toBe(4)
        expect(state.P[0].length).toBe(4)
        expect(state.P[1].length).toBe(4)
        expect(state.P[2].length).toBe(4)
        expect(state.P[3].length).toBe(4)
      }
    })

    it('should reduce covariance trace with repeated measurements (convergence)', () => {
      const x0 = new Float64Array([0, 0, 0, 0])
      const state = initEKF(x0, 200)

      const initialTrace =
        state.P[0][0] + state.P[1][1] + state.P[2][2] + state.P[3][3]

      let currentState = state
      for (let i = 0; i < 5; i++) {
        const a = [0, 0]
        const z = new Float64Array([1, 1])
        currentState = ekfStep(currentState, a, z)
      }

      const finalTrace =
        currentState.P[0][0] +
        currentState.P[1][1] +
        currentState.P[2][2] +
        currentState.P[3][3]

      // Trace of covariance (total uncertainty) must decrease
      expect(finalTrace).toBeLessThan(initialTrace)
    })

    it('should incorporate control input into prediction', () => {
      const x0 = new Float64Array([0, 0, 0, 0])
      const state = initEKF(x0, 100)

      // Strong acceleration, measurement at origin
      const a = [100, 50]
      const z = new Float64Array([0, 0])

      const newState = ekfStep(state, a, z)

      // Velocity should increase due to acceleration even if measurement pulls back
      expect(newState.x[2]).toBeGreaterThan(0)
      expect(newState.x[3]).toBeGreaterThan(0)
    })

    it('should converge to perfect measurement with high prior uncertainty', () => {
      // With very high prior uncertainty, the filter should trust the measurement heavily
      const x0 = new Float64Array([0, 0, 0, 0])
      const state = initEKF(x0, 1e6) // Very uncertain prior

      const a = [0, 0]
      const z = new Float64Array([50, 75]) // Known position

      const newState = ekfStep(state, a, z)

      // With huge prior uncertainty, state should be very close to measurement
      expect(newState.x[0]).toBeCloseTo(50, 0)
      expect(newState.x[1]).toBeCloseTo(75, 0)
    })
  })
})
