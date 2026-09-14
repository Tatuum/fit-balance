import type {
  GarmentAttributes,
  GarmentSummary,
  Measurements,
  RecommendOutfitsResponse,
  ScoreOutfitResponse,
  ScoreResponse,
  TechniqueRecommendationsResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function scoreGarment(
  measurements: Measurements,
  garment: GarmentAttributes,
): Promise<ScoreResponse> {
  const response = await fetch(`${API_BASE}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ measurements, garment }),
  })
  if (!response.ok) {
    throw new Error(`Score request failed: ${response.status}`)
  }
  return response.json()
}

export async function getGarments(): Promise<GarmentSummary[]> {
  const response = await fetch(`${API_BASE}/garments`)
  if (!response.ok) {
    throw new Error(`Garments request failed: ${response.status}`)
  }
  return response.json()
}

export async function scoreOutfit(
  measurements: Measurements,
  itemIds: string[],
): Promise<ScoreOutfitResponse> {
  const response = await fetch(`${API_BASE}/score-outfit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ measurements, item_ids: itemIds }),
  })
  if (!response.ok) {
    throw new Error(`Score-outfit request failed: ${response.status}`)
  }
  return response.json()
}

export async function recommendOutfits(
  measurements: Measurements,
  limit = 5,
): Promise<RecommendOutfitsResponse> {
  const response = await fetch(`${API_BASE}/recommend-outfits`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ measurements, limit }),
  })
  if (!response.ok) {
    throw new Error(`Recommend-outfits request failed: ${response.status}`)
  }
  return response.json()
}

export async function getTechniqueRecommendations(
  measurements: Measurements,
): Promise<TechniqueRecommendationsResponse> {
  const response = await fetch(`${API_BASE}/technique-recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ measurements }),
  })
  if (!response.ok) {
    throw new Error(`Technique-recommendations request failed: ${response.status}`)
  }
  return response.json()
}
