import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Plus, Filter, Download, RefreshCw } from 'lucide-react'
import { propertiesApi } from '../../utils/api'
import { useStore } from '../../store/useStore'
import { fmt } from '../../utils/format'
import type { Property, PropertyList } from '../../types'
import PropertyForm from './PropertyForm'
import LoadingSpinner from '../Common/LoadingSpinner'

const WELL_TYPE_BADGES: Record<string, string> = {
  OIL: 'badge-green',
  GAS: 'badge-blue',
  BOTH: 'badge-yellow',
}

const STATUS_BADGES: Record<string, string> = {
  ACTIVE: 'badge-green',
  INACTIVE: 'badge-yellow',
  ABANDONED: 'badge-red',
}

export default function PropertyBrowser() {
  const { setSelectedPropnum, selectedPropnum, setActiveModule } = useStore()
  const [search, setSearch] = useState('')
  const [wellTypeFilter, setWellTypeFilter] = useState('')
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [editProp, setEditProp] = useState<Property | null>(null)

  const { data, isLoading, refetch } = useQuery<PropertyList>({
    queryKey: ['properties', page, search, wellTypeFilter],
    queryFn: async () => {
      const res = await propertiesApi.list({
        page,
        size: 50,
        search: search || undefined,
        well_type: wellTypeFilter || undefined,
      })
      return res.data
    },
  })

  const handleSelectProperty = (prop: Property) => {
    setSelectedPropnum(prop.propnum)
  }

  const handleOpenEconomics = (prop: Property) => {
    setSelectedPropnum(prop.propnum)
    setActiveModule('economics')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-3 border-b border-border bg-gray-900/50">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
          <input
            type="text"
            placeholder="Search by PROPNUM, name, API, field..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="input-field pl-8"
          />
        </div>

        <select
          value={wellTypeFilter}
          onChange={(e) => { setWellTypeFilter(e.target.value); setPage(1) }}
          className="input-field w-32"
        >
          <option value="">All Types</option>
          <option value="OIL">Oil</option>
          <option value="GAS">Gas</option>
          <option value="BOTH">Both</option>
        </select>

        <button
          onClick={() => refetch()}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        <button
          onClick={() => { setEditProp(null); setShowForm(true) }}
          className="btn-primary flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" />
          Add Property
        </button>
      </div>

      {/* Stats row */}
      {data && (
        <div className="px-4 py-2 border-b border-border bg-gray-900/30 flex items-center gap-6 text-xs text-gray-400">
          <span><span className="text-white font-medium">{data.total}</span> properties</span>
          <span>Page {data.page} of {Math.ceil(data.total / data.size)}</span>
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="table-header">
                <th className="px-3 py-2 text-left">PROPNUM</th>
                <th className="px-3 py-2 text-left">Name</th>
                <th className="px-3 py-2 text-left">API #</th>
                <th className="px-3 py-2 text-left">State</th>
                <th className="px-3 py-2 text-left">Field</th>
                <th className="px-3 py-2 text-left">Basin</th>
                <th className="px-3 py-2 text-left">Type</th>
                <th className="px-3 py-2 text-right">WI%</th>
                <th className="px-3 py-2 text-right">NRI%</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">First Prod</th>
                <th className="px-3 py-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((prop) => (
                <tr
                  key={prop.propnum}
                  onClick={() => handleSelectProperty(prop)}
                  className={`table-row text-xs ${selectedPropnum === prop.propnum ? 'bg-aries-900/30 border-l-2 border-l-aries-500' : ''}`}
                >
                  <td className="px-3 py-2 font-mono text-aries-400">{prop.propnum}</td>
                  <td className="px-3 py-2 text-gray-200 max-w-[200px] truncate">{prop.propname || '—'}</td>
                  <td className="px-3 py-2 text-gray-400 font-mono">{prop.api_num || '—'}</td>
                  <td className="px-3 py-2 text-gray-300">{prop.state || '—'}</td>
                  <td className="px-3 py-2 text-gray-300 max-w-[120px] truncate">{prop.field || '—'}</td>
                  <td className="px-3 py-2 text-gray-300">{prop.basin || '—'}</td>
                  <td className="px-3 py-2">
                    <span className={WELL_TYPE_BADGES[prop.well_type] || 'badge-blue'}>
                      {prop.well_type}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right text-gray-300">
                    {fmt.pct(prop.working_interest * 100)}
                  </td>
                  <td className="px-3 py-2 text-right text-gray-300">
                    {fmt.pct(prop.net_revenue_interest * 100)}
                  </td>
                  <td className="px-3 py-2">
                    <span className={STATUS_BADGES[prop.status] || 'badge-yellow'}>
                      {prop.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-gray-400">
                    {prop.first_prod_date ? prop.first_prod_date.slice(0, 10) : '—'}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); setEditProp(prop); setShowForm(true) }}
                        className="text-xs text-gray-400 hover:text-white px-1.5 py-0.5 rounded hover:bg-gray-700"
                      >
                        Edit
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleOpenEconomics(prop) }}
                        className="text-xs text-aries-400 hover:text-aries-300 px-1.5 py-0.5 rounded hover:bg-gray-700"
                      >
                        Econ
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={12} className="text-center py-12 text-gray-500">
                    No properties found. Add your first property to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.total > data.size && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-border text-xs text-gray-400">
          <span>Showing {(page - 1) * data.size + 1}–{Math.min(page * data.size, data.total)} of {data.total}</span>
          <div className="flex gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="btn-secondary py-1 px-3 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={page * data.size >= data.total}
              onClick={() => setPage(p => p + 1)}
              className="btn-secondary py-1 px-3 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Add/Edit form modal */}
      {showForm && (
        <PropertyForm
          property={editProp}
          onClose={() => { setShowForm(false); setEditProp(null) }}
          onSaved={() => { setShowForm(false); setEditProp(null); refetch() }}
        />
      )}
    </div>
  )
}
