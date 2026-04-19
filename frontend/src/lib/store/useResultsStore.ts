import { create } from "zustand"
import type { ResultData, ModalityKey, FeatureDriver, GenomicVariant, TranscriptomicGene, RadiomicFeature, ClinicalRecord } from "@/app/results/data"

const STORAGE_KEY = "pancriondx_results"

interface ResultsStore {
  results: ResultData | null
  setResults: (r: ResultData) => void
  loadFromStorage: () => void
  clearResults: () => void
}

export const useResultsStore = create<ResultsStore>((set) => ({
  results: null,

  setResults: (r: ResultData) => {
    console.log("[PancrionDX] Saving results to store:", r)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(r))
      console.log("[PancrionDX] Results persisted to localStorage.")
    } catch (e) {
      console.warn("[PancrionDX] localStorage write failed:", e)
    }
    set({ results: r })
  },

  loadFromStorage: () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as ResultData
        console.log("[PancrionDX] Results loaded from localStorage:", parsed)
        set({ results: parsed })
      } else {
        console.log("[PancrionDX] No saved results found in localStorage.")
      }
    } catch (e) {
      console.warn("[PancrionDX] localStorage read failed:", e)
    }
  },

  clearResults: () => {
    localStorage.removeItem(STORAGE_KEY)
    set({ results: null })
    console.log("[PancrionDX] Results cleared.")
  },
}))

// ─── Re-export types used by pipeline for convenience ─────────────────────────
export type { ResultData, ModalityKey, FeatureDriver, GenomicVariant, TranscriptomicGene, RadiomicFeature, ClinicalRecord }
