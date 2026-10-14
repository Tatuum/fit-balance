export interface Measurements {
  shoulder: number
  bust: number
  waist: number
  hip: number
  torso: number
  leg: number
  height: number
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

export type Slot = 'top' | 'bottom' | 'dress' | 'outerwear'

export interface GarmentSummary {
  id: string
  label: string
  slot: Slot
}

export interface TechniqueExample {
  tag: string
  direction: '+' | '-'
  items: GarmentSummary[]
}

export interface DimensionAdvice {
  axis: string
  label: string
  value: number
  notable: boolean
  pronounced: boolean
  direction: '+' | '-' | null
  recommendations: TechniqueExample[]
}

export interface TechniqueRecommendationsResponse {
  balance_points: BalancePoints
  dimensions: DimensionAdvice[]
}

export interface BalanceGarmentResponse {
  balance_points: BalancePoints
  main_concern: string[]
  item: GarmentSummary
  verdict: Verdict
  suggestions: DimensionAdvice[]
}
