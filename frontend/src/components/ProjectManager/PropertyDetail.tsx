import { useQuery } from '@tanstack/react-query'
import { X, Activity, MapPin, DollarSign, BarChart2 } from 'lucide-react'
import { propertiesApi, productionApi } from '../../utils/api'
import { useStore } from '../../store/useStore'
import { fmt } from '../../utils/format'
import type { Property, ProductionRecord } from '../../types'
import LoadingSpinner from '../Common/LoadingSpinner'

export default function PropertyDetail({ propnum }: { propnum: string }) {
  const { setSelectedPropnum, setActiveModule } = useStore()

  const { data: prop, isLoading } = useQuery<Property>({
    queryKey: ['property', propnum],
    queryFn: async () => (await propertiesApi.get(propnum)).data,
  })

  const { data: production } = useQuery<ProductionRecord[]>({
    queryKey: ['production', propnum],
    queryFn: async () => (await productionApi.get(propnum)).data,
  })

  if (isLoading) return <LoadingSpinner size="sm" />
  if (!prop) return null

  // Recent 12 months for display
  const recent = production?.slice(-12).reverse() || []
  const latestOil = recent[0]?.oil_rate_bopd || 0
  const latestGas = recent[0]?.gas_rate_mcfd || 0

  return (
    <div className="p-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-xs text-gray-500 font-mono">{prop.propnum}</div>
          <h2 className="text-sm font-semibold text-white mt-0.5">{prop.propname || 'Unnamed Property'}</h2>
          <div className="text-xs text-gray-400 mt-0.5">{[prop.field, prop.county, prop.state].filter(Boolean).join(', ')}</div>
        </div>
        <button
          onClick={() => setSelectedPropnum(null)}
          className="text-gray-500 hover:text-white p-1"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="stat-card">
          <span className="stat-label">Oil Rate</span>
          <span className="stat-value text-lg">{fmt.rate(latestOil, 'BOPD')}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Gas Rate</span>
          <span className="stat-value text-lg">{fmt.rate(latestGas, 'MCFD')}</span>
        </div>
      </div>

      {/* Details */}
      <div className="space-y-4">
        {/* Identification */}
        <Section icon={Activity} title="Identification">
          <Row label="API #" value={prop.api_num || '—'} mono />
          <Row label="UWI" value={prop.uwi || '—'} mono />
          <Row label="Well Type" value={prop.well_type} />
          <Row label="Entity Type" value={prop.entity_type} />
          <Row label="Status" value={prop.status} />
        </Section>

        {/* Location */}
        <Section icon={MapPin} title="Location">
          <Row label="Basin" value={prop.basin || '—'} />
          <Row label="Field" value={prop.field || '—'} />
          <Row label="Formation" value={prop.formation || '—'} />
          <Row label="County/State" value={[prop.county, prop.state].filter(Boolean).join(', ') || '—'} />
          <Row label="Operator" value={prop.operator || '—'} />
        </Section>

        {/* Ownership */}
        <Section icon={DollarSign} title="Ownership">
          <Row label="Working Interest" value={fmt.pct(prop.working_interest * 100)} />
          <Row label="Net Revenue Int." value={fmt.pct(prop.net_revenue_interest * 100)} />
          <Row label="Royalty" value={fmt.pct(prop.royalty_interest * 100)} />
        </Section>

        {/* Recent Production */}
        {recent.length > 0 && (
          <Section icon={BarChart2} title="Recent Production">
            <div className="mt-1 space-y-1">
              {recent.slice(0, 6).map((r) => (
                <div key={r.id} className="flex justify-between text-xs">
                  <span className="text-gray-500">{r.prod_date.slice(0, 7)}</span>
                  <span className="text-gray-300">{fmt.rate(r.oil_rate_bopd, 'BOPD', 0)}</span>
                  <span className="text-gray-400">{fmt.rate(r.gas_rate_mcfd, 'MCF/D', 0)}</span>
                </div>
              ))}
            </div>
          </Section>
        )}
      </div>

      {/* Actions */}
      <div className="mt-4 space-y-2">
        <button
          onClick={() => setActiveModule('forecasting')}
          className="w-full btn-secondary text-xs"
        >
          Open in Forecasting
        </button>
        <button
          onClick={() => setActiveModule('economics')}
          className="w-full btn-primary text-xs"
        >
          Open in Economics
        </button>
      </div>
    </div>
  )
}

function Section({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <Icon className="w-3.5 h-3.5 text-gray-500" />
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</span>
      </div>
      <div className="space-y-1 pl-1">{children}</div>
    </div>
  )
}

function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between items-baseline text-xs">
      <span className="text-gray-500 shrink-0 mr-2">{label}</span>
      <span className={`text-gray-300 text-right truncate max-w-[140px] ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}
