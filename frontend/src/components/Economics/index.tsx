import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Save, BarChart2, TrendingUp } from 'lucide-react'
import { economicsApi } from '../../utils/api'
import { useStore } from '../../store/useStore'
import { fmt } from '../../utils/format'
import type { EconomicInputs, EconRunResult, MonthlyForecast } from '../../types'
import LoadingSpinner from '../Common/LoadingSpinner'
import CashFlowChart from './CashFlowChart'
import DeclineCurveChart from '../Forecasting/DeclineCurveChart'

export default function EconomicsModule() {
  const { selectedPropnum, selectedScenarioId } = useStore()
  const [result, setResult] = useState<EconRunResult | null>(null)
  const queryClient = useQueryClient()

  const { data: econ, isLoading } = useQuery<EconomicInputs>({
    queryKey: ['economics', selectedPropnum, selectedScenarioId],
    queryFn: async () => (await economicsApi.get(selectedPropnum!, selectedScenarioId!)).data,
    enabled: !!selectedPropnum && !!selectedScenarioId,
  })

  const runMutation = useMutation({
    mutationFn: () => economicsApi.run(selectedPropnum!, selectedScenarioId!),
    onSuccess: (res) => {
      setResult(res.data)
      queryClient.invalidateQueries({ queryKey: ['economics', selectedPropnum, selectedScenarioId] })
    },
  })

  if (!selectedPropnum || !selectedScenarioId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <BarChart2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <div className="text-sm">Select a property and scenario to run economics</div>
          <div className="text-xs mt-1 text-gray-600">Use the Project Manager to select a property, then choose a scenario</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: Inputs */}
      <div className="w-80 border-r border-border overflow-y-auto shrink-0">
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <EconInputsPanel
            propnum={selectedPropnum}
            scenarioId={selectedScenarioId}
            econ={econ}
            onRun={() => runMutation.mutate()}
            running={runMutation.isPending}
          />
        )}
      </div>

      {/* Right: Results */}
      <div className="flex-1 overflow-y-auto p-4">
        {runMutation.isPending && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-400">
              <Play className="w-8 h-8 mx-auto mb-2 animate-pulse text-aries-400" />
              <div className="text-sm">Running economic simulation...</div>
            </div>
          </div>
        )}

        {result && !runMutation.isPending && (
          <EconResults result={result} />
        )}

        {!result && !runMutation.isPending && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center text-gray-500">
              <TrendingUp className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <div className="text-sm">Configure inputs and click Run to generate economic forecast</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function EconInputsPanel({ propnum, scenarioId, econ, onRun, running }: {
  propnum: string
  scenarioId: number
  econ?: EconomicInputs
  onRun: () => void
  running: boolean
}) {
  const [form, setForm] = useState({
    oil_decline_type: econ?.oil_decline_type || 'EXP',
    oil_initial_rate: econ?.oil_initial_rate || '',
    oil_decline_rate: econ?.oil_decline_rate || '',
    oil_b_factor: econ?.oil_b_factor || 0,
    gas_initial_rate: econ?.gas_initial_rate || '',
    gas_decline_rate: econ?.gas_decline_rate || '',
    gas_b_factor: econ?.gas_b_factor || 0,
    ngl_yield: econ?.ngl_yield || 0,
    shrinkage: econ?.shrinkage || 1.0,
    fixed_opex: econ?.fixed_opex || 0,
    variable_oil_opex: econ?.variable_oil_opex || 0,
    capex: econ?.capex || 0,
    abandonment_cost: econ?.abandonment_cost || 0,
    economic_limit_type: econ?.economic_limit_type || 'NET_REVENUE',
    economic_limit_value: econ?.economic_limit_value || 0,
  })

  const qc = useQueryClient()
  const saveMutation = useMutation({
    mutationFn: () => economicsApi.save({
      propnum,
      scenario_id: scenarioId,
      ...form,
      oil_initial_rate: Number(form.oil_initial_rate) || null,
      oil_decline_rate: Number(form.oil_decline_rate) || null,
      gas_initial_rate: Number(form.gas_initial_rate) || null,
      gas_decline_rate: Number(form.gas_decline_rate) || null,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['economics', propnum, scenarioId] }),
  })

  const handleSaveAndRun = async () => {
    await saveMutation.mutateAsync()
    onRun()
  }

  const set = (field: string, val: string | number) => setForm(f => ({ ...f, [field]: val }))

  return (
    <div className="p-4 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Economic Inputs</h3>
        <span className="text-xs text-gray-500 font-mono">{propnum}</span>
      </div>

      {/* Decline Curve — Oil */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Oil Decline Curve</h4>
        <div className="space-y-2">
          <div>
            <label className="label">Decline Type</label>
            <select className="input-field text-xs" value={form.oil_decline_type} onChange={e => set('oil_decline_type', e.target.value)}>
              <option value="EXP">Exponential</option>
              <option value="HYP">Hyperbolic</option>
              <option value="HAR">Harmonic</option>
              <option value="MHYP">Modified Hyperbolic</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="label">Qi (BOPD)</label>
              <input type="number" className="input-field text-xs" placeholder="0" value={form.oil_initial_rate} onChange={e => set('oil_initial_rate', e.target.value)} />
            </div>
            <div>
              <label className="label">Di (/yr)</label>
              <input type="number" step="0.01" className="input-field text-xs" placeholder="0.30" value={form.oil_decline_rate} onChange={e => set('oil_decline_rate', e.target.value)} />
            </div>
          </div>
          {form.oil_decline_type !== 'EXP' && (
            <div>
              <label className="label">b-factor</label>
              <input type="number" step="0.1" min="0" max="2" className="input-field text-xs" value={form.oil_b_factor} onChange={e => set('oil_b_factor', e.target.value)} />
            </div>
          )}
        </div>
      </div>

      {/* Decline Curve — Gas */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Gas Decline Curve</h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">Qi (MCFD)</label>
            <input type="number" className="input-field text-xs" placeholder="0" value={form.gas_initial_rate} onChange={e => set('gas_initial_rate', e.target.value)} />
          </div>
          <div>
            <label className="label">Di (/yr)</label>
            <input type="number" step="0.01" className="input-field text-xs" placeholder="0.30" value={form.gas_decline_rate} onChange={e => set('gas_decline_rate', e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 mt-2">
          <div>
            <label className="label">NGL Yield (BBL/MMCF)</label>
            <input type="number" className="input-field text-xs" value={form.ngl_yield} onChange={e => set('ngl_yield', e.target.value)} />
          </div>
          <div>
            <label className="label">Shrinkage</label>
            <input type="number" step="0.01" min="0" max="1" className="input-field text-xs" value={form.shrinkage} onChange={e => set('shrinkage', e.target.value)} />
          </div>
        </div>
      </div>

      {/* OPEX */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Operating Costs</h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">Fixed OPEX ($/mo)</label>
            <input type="number" className="input-field text-xs" value={form.fixed_opex} onChange={e => set('fixed_opex', e.target.value)} />
          </div>
          <div>
            <label className="label">Var. Oil ($/BBL)</label>
            <input type="number" step="0.01" className="input-field text-xs" value={form.variable_oil_opex} onChange={e => set('variable_oil_opex', e.target.value)} />
          </div>
        </div>
      </div>

      {/* CAPEX */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Capital Costs</h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">CAPEX ($)</label>
            <input type="number" className="input-field text-xs" value={form.capex} onChange={e => set('capex', e.target.value)} />
          </div>
          <div>
            <label className="label">P&A Cost ($)</label>
            <input type="number" className="input-field text-xs" value={form.abandonment_cost} onChange={e => set('abandonment_cost', e.target.value)} />
          </div>
        </div>
      </div>

      {/* Economic limit */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Economic Limit (LOSS)</h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="label">Limit Type</label>
            <select className="input-field text-xs" value={form.economic_limit_type} onChange={e => set('economic_limit_type', e.target.value)}>
              <option value="NET_REVENUE">Net Revenue</option>
              <option value="OIL_RATE">Oil Rate</option>
              <option value="GAS_RATE">Gas Rate</option>
            </select>
          </div>
          <div>
            <label className="label">Limit Value</label>
            <input type="number" className="input-field text-xs" value={form.economic_limit_value} onChange={e => set('economic_limit_value', e.target.value)} />
          </div>
        </div>
      </div>

      {/* Run button */}
      <div className="flex gap-2 pt-2 border-t border-border">
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="btn-secondary flex items-center gap-1.5 text-xs flex-1"
        >
          <Save className="w-3.5 h-3.5" />
          Save
        </button>
        <button
          onClick={handleSaveAndRun}
          disabled={running || saveMutation.isPending}
          className="btn-primary flex items-center gap-1.5 text-xs flex-1"
        >
          <Play className="w-3.5 h-3.5" />
          {running ? 'Running...' : 'Run'}
        </button>
      </div>
    </div>
  )
}

function EconResults({ result }: { result: EconRunResult }) {
  return (
    <div className="space-y-6">
      {/* KPI Summary */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-3">Economic Summary</h3>
        <div className="grid grid-cols-4 gap-3">
          <div className="stat-card">
            <span className="stat-label">NPV10 (MM$)</span>
            <span className={`stat-value ${result.npv10 >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {fmt.millions(result.npv10)}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">NPV15 (MM$)</span>
            <span className={`stat-value ${result.npv15 >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {fmt.millions(result.npv15)}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">IRR</span>
            <span className="stat-value text-aries-300">{fmt.irr(result.irr)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Payout</span>
            <span className="stat-value">{fmt.payout(result.payout_months)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Cum. Oil (MSTB)</span>
            <span className="stat-value text-green-400">{fmt.reserves(result.cum_oil_mstb)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Cum. Gas (MMCF)</span>
            <span className="stat-value text-blue-400">{fmt.reserves(result.cum_gas_mmcf, 'MMCF')}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total Revenue</span>
            <span className="stat-value">{fmt.millions(result.total_revenue)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total OPEX</span>
            <span className="stat-value text-red-400">{fmt.millions(result.total_opex)}</span>
          </div>
        </div>
      </div>

      {/* Decline Curve Chart */}
      <div className="card">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Production Forecast</h4>
        <DeclineCurveChart data={result.monthly_forecast} />
      </div>

      {/* Cash Flow Chart */}
      <div className="card">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Cash Flow</h4>
        <CashFlowChart data={result.monthly_forecast} />
      </div>

      {/* Monthly Table (first 24 months) */}
      <div className="card">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Monthly Detail (first 24 months)</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="table-header">
                <th className="px-2 py-1 text-left">Date</th>
                <th className="px-2 py-1 text-right">Oil (BOPD)</th>
                <th className="px-2 py-1 text-right">Gas (MCFD)</th>
                <th className="px-2 py-1 text-right">Revenue</th>
                <th className="px-2 py-1 text-right">OPEX</th>
                <th className="px-2 py-1 text-right">NCF</th>
                <th className="px-2 py-1 text-right">Cum. NCF</th>
                <th className="px-2 py-1 text-right">Disc. NCF</th>
              </tr>
            </thead>
            <tbody>
              {result.monthly_forecast.slice(0, 24).map((row) => (
                <tr key={row.month} className="border-b border-gray-800 hover:bg-gray-800/30">
                  <td className="px-2 py-1 text-gray-400 font-mono">{row.date.slice(0, 7)}</td>
                  <td className="px-2 py-1 text-right text-gray-300">{row.oil_rate_bopd.toFixed(0)}</td>
                  <td className="px-2 py-1 text-right text-gray-300">{row.gas_rate_mcfd.toFixed(0)}</td>
                  <td className="px-2 py-1 text-right text-green-400">{fmt.currency(row.total_revenue)}</td>
                  <td className="px-2 py-1 text-right text-red-400">{fmt.currency(row.opex)}</td>
                  <td className={`px-2 py-1 text-right font-medium ${row.net_cash_flow >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                    {fmt.currency(row.net_cash_flow)}
                  </td>
                  <td className={`px-2 py-1 text-right ${row.cum_cash_flow >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {fmt.currency(row.cum_cash_flow)}
                  </td>
                  <td className="px-2 py-1 text-right text-gray-400">{fmt.currency(row.discounted_ncf)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
