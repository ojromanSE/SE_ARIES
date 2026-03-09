import { useState } from 'react'
import { X } from 'lucide-react'
import { propertiesApi } from '../../utils/api'
import type { Property } from '../../types'

interface Props {
  property: Property | null
  onClose: () => void
  onSaved: () => void
}

export default function PropertyForm({ property, onClose, onSaved }: Props) {
  const isEdit = !!property
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState({
    propnum: property?.propnum || '',
    propname: property?.propname || '',
    api_num: property?.api_num || '',
    uwi: property?.uwi || '',
    state: property?.state || '',
    county: property?.county || '',
    field: property?.field || '',
    formation: property?.formation || '',
    basin: property?.basin || '',
    well_type: property?.well_type || 'OIL',
    prop_type: property?.prop_type || 'PRODUCING',
    entity_type: property?.entity_type || 'WELL',
    working_interest: property?.working_interest ?? 1.0,
    net_revenue_interest: property?.net_revenue_interest ?? 1.0,
    royalty_interest: property?.royalty_interest ?? 0.0,
    operator: property?.operator || '',
    first_prod_date: property?.first_prod_date?.slice(0, 10) || '',
    status: property?.status || 'ACTIVE',
    notes: property?.notes || '',
  })

  const set = (field: string, val: string | number) =>
    setForm((f) => ({ ...f, [field]: val }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload = {
        ...form,
        working_interest: Number(form.working_interest),
        net_revenue_interest: Number(form.net_revenue_interest),
        royalty_interest: Number(form.royalty_interest),
        first_prod_date: form.first_prod_date || null,
      }
      if (isEdit) {
        await propertiesApi.update(property!.propnum, payload)
      } else {
        await propertiesApi.create(payload)
      }
      onSaved()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Save failed'
      setError(String(msg))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-border rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-base font-semibold text-white">
            {isEdit ? `Edit Property — ${property!.propnum}` : 'Add New Property'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="bg-red-900/30 border border-red-700 text-red-400 text-sm rounded p-3">{error}</div>
          )}

          {/* Section: Identification */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Property Identification</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">PROPNUM *</label>
                <input className="input-field font-mono" value={form.propnum} onChange={(e) => set('propnum', e.target.value)} required disabled={isEdit} />
              </div>
              <div>
                <label className="label">Property Name</label>
                <input className="input-field" value={form.propname} onChange={(e) => set('propname', e.target.value)} />
              </div>
              <div>
                <label className="label">API Number</label>
                <input className="input-field font-mono" value={form.api_num} onChange={(e) => set('api_num', e.target.value)} placeholder="42-XXX-XXXXX-0000" />
              </div>
              <div>
                <label className="label">UWI</label>
                <input className="input-field font-mono" value={form.uwi} onChange={(e) => set('uwi', e.target.value)} />
              </div>
            </div>
          </div>

          {/* Section: Location */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Location</h3>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="label">State</label>
                <input className="input-field" value={form.state} onChange={(e) => set('state', e.target.value)} placeholder="TX" />
              </div>
              <div>
                <label className="label">County</label>
                <input className="input-field" value={form.county} onChange={(e) => set('county', e.target.value)} />
              </div>
              <div>
                <label className="label">Basin</label>
                <input className="input-field" value={form.basin} onChange={(e) => set('basin', e.target.value)} placeholder="Permian" />
              </div>
              <div>
                <label className="label">Field</label>
                <input className="input-field" value={form.field} onChange={(e) => set('field', e.target.value)} />
              </div>
              <div>
                <label className="label">Formation</label>
                <input className="input-field" value={form.formation} onChange={(e) => set('formation', e.target.value)} />
              </div>
              <div>
                <label className="label">Operator</label>
                <input className="input-field" value={form.operator} onChange={(e) => set('operator', e.target.value)} />
              </div>
            </div>
          </div>

          {/* Section: Classification */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Classification</h3>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="label">Well Type</label>
                <select className="input-field" value={form.well_type} onChange={(e) => set('well_type', e.target.value)}>
                  <option value="OIL">Oil</option>
                  <option value="GAS">Gas</option>
                  <option value="BOTH">Both</option>
                </select>
              </div>
              <div>
                <label className="label">Entity Type</label>
                <select className="input-field" value={form.entity_type} onChange={(e) => set('entity_type', e.target.value)}>
                  <option value="WELL">Well</option>
                  <option value="GROUP">Group</option>
                  <option value="AREA">Area</option>
                </select>
              </div>
              <div>
                <label className="label">Status</label>
                <select className="input-field" value={form.status} onChange={(e) => set('status', e.target.value)}>
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
                  <option value="ABANDONED">Abandoned</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section: Ownership */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Ownership (fractions)</h3>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="label">Working Interest (WI)</label>
                <input type="number" step="0.0001" min="0" max="1" className="input-field" value={form.working_interest}
                  onChange={(e) => set('working_interest', e.target.value)} />
              </div>
              <div>
                <label className="label">Net Revenue Interest (NRI)</label>
                <input type="number" step="0.0001" min="0" max="1" className="input-field" value={form.net_revenue_interest}
                  onChange={(e) => set('net_revenue_interest', e.target.value)} />
              </div>
              <div>
                <label className="label">Royalty Interest</label>
                <input type="number" step="0.0001" min="0" max="1" className="input-field" value={form.royalty_interest}
                  onChange={(e) => set('royalty_interest', e.target.value)} />
              </div>
            </div>
          </div>

          {/* First prod date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">First Production Date</label>
              <input type="date" className="input-field" value={form.first_prod_date} onChange={(e) => set('first_prod_date', e.target.value)} />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="label">Notes</label>
            <textarea className="input-field h-16 resize-none" value={form.notes} onChange={(e) => set('notes', e.target.value)} />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Saving...' : isEdit ? 'Update Property' : 'Create Property'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
