import type {
  BalanceGarmentResponse,
  GarmentSummary,
  Measurements,
  TechniqueRecommendationsResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function getGarments(): Promise<GarmentSummary[]> {
  const response = await fetch(`${API_BASE}/garments`)
  if (!response.ok) {
    throw new Error(`Garments request failed: ${response.status}`)
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

export async function balanceGarment(
  measurements: Measurements,
  itemId: string,
): Promise<BalanceGarmentResponse> {
  const response = await fetch(`${API_BASE}/balance-garment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ measurements, item_id: itemId }),
  })
  if (!response.ok) {
    throw new Error(`Balance-garment request failed: ${response.status}`)
  }
  return response.json()
}
