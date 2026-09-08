import type {
  GarmentAttributes,
  GarmentSummary,
  Measurements,
  ScoreOutfitResponse,
  ScoreResponse,
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
