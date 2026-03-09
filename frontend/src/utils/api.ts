import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aries_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 (redirect to login)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('aries_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// ---- Properties ----
export const propertiesApi = {
  list: (params?: Record<string, unknown>) => api.get('/properties/', { params }),
  get: (propnum: string) => api.get(`/properties/${propnum}`),
  create: (data: unknown) => api.post('/properties/', data),
  update: (propnum: string, data: unknown) => api.put(`/properties/${propnum}`, data),
  delete: (propnum: string) => api.delete(`/properties/${propnum}`),
  bulkImport: (data: unknown[]) => api.post('/properties/bulk-import', data),
}

// ---- Projects ----
export const projectsApi = {
  list: () => api.get('/projects/'),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (data: unknown) => api.post('/projects/', data),
  update: (id: number, data: unknown) => api.put(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
  getProperties: (id: number) => api.get(`/projects/${id}/properties`),
  addProperty: (id: number, propnum: string, weight: number = 1) =>
    api.post(`/projects/${id}/properties/${propnum}?weight_factor=${weight}`),
  removeProperty: (id: number, propnum: string) =>
    api.delete(`/projects/${id}/properties/${propnum}`),
}

// ---- Scenarios ----
export const scenariosApi = {
  list: (projectId: number) => api.get(`/projects/${projectId}/scenarios`),
  create: (projectId: number, data: unknown) => api.post(`/projects/${projectId}/scenarios`, data),
  update: (id: number, data: unknown) => api.put(`/projects/scenarios/${id}`, data),
  delete: (id: number) => api.delete(`/projects/scenarios/${id}`),
}

// ---- Economics ----
export const economicsApi = {
  get: (propnum: string, scenarioId: number) => api.get(`/economics/${propnum}/${scenarioId}`),
  save: (data: unknown) => api.post('/economics/', data),
  update: (propnum: string, scenarioId: number, data: unknown) =>
    api.put(`/economics/${propnum}/${scenarioId}`, data),
  run: (propnum: string, scenarioId: number) =>
    api.post(`/economics/${propnum}/${scenarioId}/run`),
  getForecast: (propnum: string, scenarioId: number) =>
    api.get(`/economics/${propnum}/${scenarioId}/forecast`),
}

// ---- Production ----
export const productionApi = {
  get: (propnum: string, params?: Record<string, unknown>) =>
    api.get(`/production/${propnum}`, { params }),
  add: (data: unknown) => api.post('/production/', data),
}

// ---- Auth ----
export const authApi = {
  login: (username: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  me: () => api.get('/auth/me'),
  register: (data: unknown) => api.post('/auth/register', data),
}
