import type { GarmentSummary, Slot } from './types'

export const SLOTS: Slot[] = ['top', 'bottom', 'dress', 'outerwear']

export function groupBySlot(items: GarmentSummary[]): Record<Slot, GarmentSummary[]> {
  const grouped: Record<Slot, GarmentSummary[]> = { top: [], bottom: [], dress: [], outerwear: [] }
  for (const item of items) {
    grouped[item.slot].push(item)
  }
  return grouped
}
