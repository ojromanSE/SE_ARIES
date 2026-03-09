import { useQuery } from '@tanstack/react-query'
import { BarChart2 } from 'lucide-react'
import { economicsApi, productionApi } from '../../utils/api'
import { useStore } from '../../store/useStore'
import type { MonthlyForecast, ProductionRecord } from '../../types'
import LoadingSpinner from '../Common/LoadingSpinner'
import DeclineCurveChart from './DeclineCurveChart'

export default function ForecastingModule() {
  const { selectedPropnum, selectedScenarioId } = useStore()

  const { data: history, isLoading: histLoading } = useQuery<ProductionRecord[]>({
    queryKey: ['production', selectedPropnum],
    queryFn: async () => (await productionApi.get(selectedPropnum!)).data,
    enabled: !!selectedPropnum,
  })

  const { data: forecast, isLoading: fcstLoading } = useQuery<MonthlyForecast[]>({
    queryKey: ['forecast', selectedPropnum, selectedScenarioId],
    queryFn: async () => (await economicsApi.getForecast(selectedPropnum!, selectedScenarioId!)).data,
    enabled: !!selectedPropnum && !!selectedScenarioId,
  })

  if (!selectedPropnum) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <BarChart2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <div className="text-sm">Select a property in the Project Manager</div>
        </div>
      </div>
    )
  }

  if (histLoading || fcstLoading) return <LoadingSpinner />

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">Decline Curve Analysis</h2>
          <div className="text-xs text-gray-500 mt-0.5 font-mono">{selectedPropnum}</div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Production History + Forecast
        </h3>
        <DeclineCurveChart data={forecast || []} history={history || []} />
      </div>

      {/* Production history table */}
      {history && history.length > 0 && (
        <div className="card">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Production History</h3>
          <div className="overflow-x-auto max-h-64">
            <table className="w-full text-xs">
              <thead className="sticky top-0">
                <tr className="table-header">
                  <th className="px-3 py-1.5 text-left">Date</th>
                  <th className="px-3 py-1.5 text-right">Days On</th>
                  <th className="px-3 py-1.5 text-right">Oil (BBL)</th>
                  <th className="px-3 py-1.5 text-right">Gas (MCF)</th>
                  <th className="px-3 py-1.5 text-right">Water (BBL)</th>
                  <th className="px-3 py-1.5 text-right">Oil Rate (BOPD)</th>
                </tr>
              </thead>
              <tbody>
                {[...history].reverse().map((r) => (
                  <tr key={r.id} className="border-b border-gray-800 hover:bg-gray-800/30">
                    <td className="px-3 py-1.5 text-gray-400 font-mono">{r.prod_date.slice(0, 7)}</td>
                    <td className="px-3 py-1.5 text-right text-gray-300">{r.days_on}</td>
                    <td className="px-3 py-1.5 text-right text-green-400">{r.gross_oil_bbl.toFixed(0)}</td>
                    <td className="px-3 py-1.5 text-right text-blue-400">{r.gross_gas_mcf.toFixed(0)}</td>
                    <td className="px-3 py-1.5 text-right text-gray-400">{r.gross_water_bbl.toFixed(0)}</td>
                    <td className="px-3 py-1.5 text-right text-gray-300">{r.oil_rate_bopd.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
