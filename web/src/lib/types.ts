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
  main_concern: string | null
  verdict: Verdict
}

export type Slot = 'top' | 'bottom' | 'dress' | 'outerwear'

export interface GarmentSummary {
  id: string
  label: string
  slot: Slot
}

export interface AttributedReason extends Reason {
  item_ids: string[]
}

export interface OutfitVerdict {
  recommendation: Recommendation
  score: number
  reasons: AttributedReason[]
}

export interface ScoreOutfitResponse {
  balance_points: BalancePoints
  main_concern: string | null
  verdict: OutfitVerdict
}

export interface RecommendedOutfit {
  item_ids: string[]
  labels: string[]
  verdict: OutfitVerdict
}

export interface RecommendOutfitsResponse {
  balance_points: BalancePoints
  main_concern: string | null
  recommendations: RecommendedOutfit[]
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
