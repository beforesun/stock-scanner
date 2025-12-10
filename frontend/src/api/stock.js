import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)

    if (error.response) {
      // 请求已发出，但服务器响应状态码不在 2xx 范围内
      ElMessage.error(error.response.data?.detail || '请求失败')
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      ElMessage.error('网络错误，请检查连接')
    } else {
      // 在设置请求时发生了一些事情
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

// 周末扫描相关API
export const getWeekendScan = async () => {
  return api.get('/weekend-scan/latest')
}

export const triggerWeekendScan = async () => {
  return api.post('/weekend-scan/trigger')
}

export const getWeekendScanHistory = async (page = 1, size = 20) => {
  return api.get(`/weekend-scan/history?page=${page}&size=${size}`)
}

// 日筛选池相关API
export const getDailyPool = async () => {
  return api.get('/daily-pool/latest')
}

export const triggerDailyScan = async () => {
  return api.post('/daily-pool/trigger')
}

// 交易信号相关API
export const getSignals = async (status = 'PENDING') => {
  return api.get(`/signals/latest?status=${status}`)
}

export const getSignalDetail = async (signalId) => {
  return api.get(`/signals/${signalId}`)
}

export const updateSignalStatus = async (signalId, status, note = '') => {
  return api.put(`/signals/${signalId}/status`, {
    status,
    note
  })
}

// 个股数据相关API
export const getStockDetail = async (code) => {
  return api.get(`/stocks/${code}`)
}

export const getStockKlines = async (code, type = 'daily', days = 60) => {
  return api.get(`/stocks/${code}/klines?type=${type}&days=${days}`)
}

// 系统状态API
export const getSystemStatus = async () => {
  return api.get('/system/status')
}