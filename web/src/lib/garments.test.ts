import { describe, expect, it } from 'vitest'
import { groupBySlot } from './garments'
import type { GarmentSummary } from './types'

describe('groupBySlot', () => {
  it('returns all-empty groups for an empty input', () => {
    expect(groupBySlot([])).toEqual({ top: [], bottom: [], dress: [], outerwear: [] })
  })

  it('groups mixed-slot items into their respective slot', () => {
    const items: GarmentSummary[] = [
      { id: 'a', label: 'Oversized top', slot: 'top' },
      { id: 'b', label: 'Slim trousers', slot: 'bottom' },
      { id: 'c', label: 'Belted blouse', slot: 'top' },
      { id: 'd', label: 'Sheath dress', slot: 'dress' },
    ]
    const grouped = groupBySlot(items)
    expect(grouped.top.map((i) => i.id)).toEqual(['a', 'c'])
    expect(grouped.bottom.map((i) => i.id)).toEqual(['b'])
    expect(grouped.dress.map((i) => i.id)).toEqual(['d'])
    expect(grouped.outerwear).toEqual([])
  })

  it('preserves input order within a slot', () => {
    const items: GarmentSummary[] = [
      { id: 'second', label: 'Second', slot: 'top' },
      { id: 'first', label: 'First', slot: 'top' },
    ]
    expect(groupBySlot(items).top.map((i) => i.id)).toEqual(['second', 'first'])
  })
})
