import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import type { MonthlyForecast, ProductionRecord } from '../../types'

interface Props {
  data: MonthlyForecast[]
  history?: ProductionRecord[]
}

export default function DeclineCurveChart({ data, history }: Props) {
  // Combine history and forecast
  const historyPoints = (history || []).map(h => ({
    date: h.prod_date.slice(0, 7),
    histOil: h.oil_rate_bopd,
    histGas: h.gas_rate_mcfd / 10, // Scale gas for dual-axis display
    forecastOil: undefined as number | undefined,
    forecastGas: undefined as number | undefined,
    cumOil: h.gross_oil_bbl / 1000,
  }))

  const forecastPoints = data.map(d => ({
    date: d.date.slice(0, 7),
    histOil: undefined as number | undefined,
    histGas: undefined as number | undefined,
    forecastOil: d.oil_rate_bopd,
    forecastGas: d.gas_rate_mcfd / 10,
    cumOil: d.cum_oil_mstb,
  }))

  const chartData = [...historyPoints, ...forecastPoints]

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#9CA3AF', fontSize: 10 }}
          tickLine={false}
          interval={Math.floor(chartData.length / 8)}
        />
        <YAxis
          yAxisId="left"
          tick={{ fill: '#9CA3AF', fontSize: 10 }}
          tickLine={false}
          label={{ value: 'BOPD / MCFD÷10', angle: -90, position: 'insideLeft', fill: '#6B7280', fontSize: 10 }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fill: '#9CA3AF', fontSize: 10 }}
          tickLine={false}
          label={{ value: 'Cum. Oil (MSTB)', angle: 90, position: 'insideRight', fill: '#6B7280', fontSize: 10 }}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '6px' }}
          labelStyle={{ color: '#E5E7EB', fontSize: 11 }}
          itemStyle={{ fontSize: 11 }}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: '#9CA3AF' }} />
        {/* History */}
        <Line yAxisId="left" type="monotone" dataKey="histOil" name="Hist. Oil (BOPD)"
          stroke="#F59E0B" strokeWidth={2} dot={false} connectNulls={false} />
        {/* Forecast */}
        <Line yAxisId="left" type="monotone" dataKey="forecastOil" name="Fcst. Oil (BOPD)"
          stroke="#10B981" strokeWidth={2} dot={false} strokeDasharray="6 2" connectNulls={false} />
        <Line yAxisId="left" type="monotone" dataKey="forecastGas" name="Gas/10 (MCFD)"
          stroke="#3B82F6" strokeWidth={1.5} dot={false} strokeDasharray="3 3" connectNulls={false} />
        {/* Cumulative */}
        <Line yAxisId="right" type="monotone" dataKey="cumOil" name="Cum. Oil (MSTB)"
          stroke="#8B5CF6" strokeWidth={1.5} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
