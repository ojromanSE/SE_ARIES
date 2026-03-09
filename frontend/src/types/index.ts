// ARIES data types — mirror the backend schemas

export interface Property {
  propnum: string
  propname: string | null
  api_num: string | null
  uwi: string | null
  state: string | null
  county: string | null
  field: string | null
  formation: string | null
  basin: string | null
  latitude: number | null
  longitude: number | null
  well_type: string
  prop_type: string
  entity_type: string
  working_interest: number
  net_revenue_interest: number
  royalty_interest: number
  overriding_royalty: number
  operator: string | null
  spud_date: string | null
  completion_date: string | null
  first_prod_date: string | null
  currency: string
  volume_unit: string
  status: string
  is_active: boolean
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

export interface PropertyList {
  items: Property[]
  total: number
  page: number
  size: number
}

export interface Project {
  id: number
  project_name: string
  project_code: string | null
  description: string | null
  project_type: string
  parent_project_id: number | null
  default_scenario: string | null
  consolidation_method: string
  default_discount_rate: number
  econ_start_date: string | null
  is_active: boolean
  is_locked: boolean
  created_at: string | null
}

export interface Scenario {
  id: number
  project_id: number
  scenario_name: string
  scenario_code: string | null
  description: string | null
  scenario_type: string
  oil_price: number | null
  gas_price: number | null
  ngl_price: number | null
  discount_rate: number
  tax_rate: number
  chance_of_success: number
  apply_economic_limit: boolean
  econ_start_date: string | null
  max_life_years: number
  is_base_case: boolean
  is_active: boolean
}

export interface EconomicInputs {
  id: number
  propnum: string
  scenario_id: number
  oil_decline_type: string
  oil_initial_rate: number | null
  oil_decline_rate: number | null
  oil_b_factor: number
  gas_decline_type: string
  gas_initial_rate: number | null
  gas_decline_rate: number | null
  gas_b_factor: number
  ngl_yield: number
  shrinkage: number
  btu_factor: number
  fixed_opex: number
  variable_oil_opex: number
  variable_gas_opex: number
  overhead: number
  capex: number
  abandonment_cost: number
  economic_limit_type: string
  economic_limit_value: number
  npv10: number | null
  npv15: number | null
  irr: number | null
  payout_months: number | null
  cum_oil_mstb: number | null
  cum_gas_mmcf: number | null
  run_status: string
}

export interface EconRunResult {
  propnum: string
  scenario_id: number
  npv10: number
  npv15: number
  irr: number | null
  payout_months: number | null
  total_capex: number
  total_opex: number
  total_revenue: number
  cum_oil_mstb: number
  cum_gas_mmcf: number
  cum_ngl_mstb: number
  monthly_forecast: MonthlyForecast[]
}

export interface MonthlyForecast {
  month: number
  date: string
  oil_rate_bopd: number
  gas_rate_mcfd: number
  gross_oil_bbl: number
  gross_gas_mcf: number
  total_revenue: number
  opex: number
  net_cash_flow: number
  cum_cash_flow: number
  discounted_ncf: number
  cum_oil_mstb: number
  cum_gas_mmcf: number
}

export interface ProductionRecord {
  id: number
  propnum: string
  prod_date: string
  prod_year: number
  prod_month: number
  days_on: number
  gross_oil_bbl: number
  gross_gas_mcf: number
  gross_ngl_bbl: number
  gross_water_bbl: number
  oil_rate_bopd: number
  gas_rate_mcfd: number
}
