/**Formatting utilities for petroleum economics data."""

export const fmt = {
  /** Format number as currency */
  currency: (val: number | null | undefined, decimals = 0): string => {
    if (val == null) return '—'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(val)
  },

  /** Format in thousands */
  thousands: (val: number | null | undefined, decimals = 1): string => {
    if (val == null) return '—'
    return `${(val / 1000).toFixed(decimals)}k`
  },

  /** Format in millions */
  millions: (val: number | null | undefined, decimals = 2): string => {
    if (val == null) return '—'
    return `$${(val / 1_000_000).toFixed(decimals)}MM`
  },

  /** Format volume */
  volume: (val: number | null | undefined, unit: string = '', decimals = 1): string => {
    if (val == null) return '—'
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(decimals)}MM ${unit}`
    if (val >= 1_000) return `${(val / 1_000).toFixed(decimals)}M ${unit}`
    return `${val.toFixed(decimals)} ${unit}`
  },

  /** Format percentage */
  pct: (val: number | null | undefined, decimals = 1): string => {
    if (val == null) return '—'
    return `${val.toFixed(decimals)}%`
  },

  /** Format rate */
  rate: (val: number | null | undefined, unit: string = 'BOPD', decimals = 0): string => {
    if (val == null) return '—'
    return `${val.toFixed(decimals)} ${unit}`
  },

  /** Format reserves (MSTB or MMCF) */
  reserves: (val: number | null | undefined, unit: string = 'MSTB', decimals = 1): string => {
    if (val == null) return '—'
    return `${val.toFixed(decimals)} ${unit}`
  },

  /** Payout in months/years */
  payout: (months: number | null | undefined): string => {
    if (months == null) return 'N/A'
    if (months < 24) return `${months.toFixed(0)} mo`
    return `${(months / 12).toFixed(1)} yr`
  },

  /** Format IRR */
  irr: (val: number | null | undefined): string => {
    if (val == null) return 'N/A'
    return `${val.toFixed(1)}%`
  },

  /** Truncate long strings */
  truncate: (str: string | null | undefined, maxLen: number = 30): string => {
    if (!str) return '—'
    return str.length > maxLen ? `${str.slice(0, maxLen)}…` : str
  },
}
