export interface Measurements {
  shoulder: number
  bust: number
  waist: number
  hip: number
  torso: number
  leg: number
  height: number
}

export interface GarmentAttributes {
  techniques: string[]
}

export interface Reason {
  tag: string
  axis: string
  contribution: number
  direction: '+' | '-'
}

export type Recommendation = 'recommended' | 'neutral' | 'avoid' | 'strong_avoid'

export interface Verdict {
  recommendation: Recommendation
  score: number
  reasons: Reason[]
}

export interface BalancePoints {
  shoulder_hip_balance: number
  bust_hip_balance: number
  waist_definition: number
  torso_leg_balance: number
  frame_scale_dev: number
}

export interface ScoreResponse {
  balance_points: BalancePoints
  main_concern: string
  verdict: Verdict
}
