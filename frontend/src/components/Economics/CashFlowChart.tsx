import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import type { MonthlyForecast } from '../../types'

interface Props {
  data: MonthlyForecast[]
}

export default function CashFlowChart({ data }: Props) {
  const chartData = data.map(d => ({
    date: d.date.slice(0, 7),
    revenue: Math.round(d.total_revenue / 1000),
    opex: -Math.round(d.opex / 1000),
    ncf: Math.round(d.net_cash_flow / 1000),
    cumNcf: Math.round(d.cum_cash_flow / 1000),
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="date" tick={{ fill: '#9CA3AF', fontSize: 10 }} tickLine={false}
          interval={Math.floor(chartData.length / 8)} />
        <YAxis yAxisId="left" tick={{ fill: '#9CA3AF', fontSize: 10 }} tickLine={false}
          tickFormatter={(v) => `$${v}k`} />
        <YAxis yAxisId="right" orientation="right" tick={{ fill: '#9CA3AF', fontSize: 10 }} tickLine={false}
          tickFormatter={(v) => `$${v}k`} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '6px' }}
          labelStyle={{ color: '#E5E7EB', fontSize: 11 }}
          itemStyle={{ fontSize: 11 }}
          formatter={(v: number) => [`$${v}k`, '']}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: '#9CA3AF' }} />
        <ReferenceLine yAxisId="left" y={0} stroke="#6B7280" />
        <Bar yAxisId="left" dataKey="revenue" name="Revenue" fill="#059669" opacity={0.8} radius={[2, 2, 0, 0]} />
        <Bar yAxisId="left" dataKey="opex" name="OPEX" fill="#DC2626" opacity={0.8} radius={[2, 2, 0, 0]} />
        <Line yAxisId="right" type="monotone" dataKey="cumNcf" name="Cum. NCF" stroke="#60A5FA"
          strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
