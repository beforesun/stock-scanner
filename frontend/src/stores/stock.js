import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getWeekendScan,
  getDailyPool,
  getSignals,
  getSystemStatus
} from '@/api/stock'

export const useStockStore = defineStore('stock', () => {
  // 周末扫描结果
  const weekendScanResults = ref({
    scanDate: '',
    totalCount: 0,
    passedCount: 0,
    results: []
  })

  // 日筛选池结果
  const dailyPoolResults = ref({
    scanDate: '',
    totalCount: 0,
    poolCount: 0,
    results: []
  })

  // 交易信号
  const tradeSignals = ref({
    signalDate: '',
    totalSignals: 0,
    signals: []
  })

  // 系统状态
  const systemStatus = ref({
    status: 'unknown',
    lastWeekendScan: null,
    lastDailyScan: null,
    nextScan: null,
    databaseStatus: 'unknown',
    redisStatus: 'unknown'
  })

  // 加载状态
  const loading = ref(false)

  // 获取周末扫描结果
  const fetchWeekendScan = async () => {
    loading.value = true
    try {
      const data = await getWeekendScan()
      weekendScanResults.value = {
        scanDate: data.scan_date,
        totalCount: data.total_count,
        passedCount: data.passed_count,
        results: data.results
      }
    } catch (error) {
      console.error('Failed to fetch weekend scan:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取日筛选池
  const fetchDailyPool = async () => {
    loading.value = true
    try {
      const data = await getDailyPool()
      dailyPoolResults.value = {
        scanDate: data.scan_date,
        totalCount: data.total_count,
        poolCount: data.pool_count,
        results: data.results
      }
    } catch (error) {
      console.error('Failed to fetch daily pool:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取交易信号
  const fetchSignals = async (status = 'PENDING') => {
    loading.value = true
    try {
      const data = await getSignals(status)
      if (data) {
        tradeSignals.value = {
          signalDate: data.signal_date,
          totalSignals: data.total_signals,
          signals: data.signals
        }
      } else {
        tradeSignals.value = {
          signalDate: '',
          totalSignals: 0,
          signals: []
        }
      }
    } catch (error) {
      console.error('Failed to fetch signals:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取系统状态
  const fetchSystemStatus = async () => {
    try {
      const data = await getSystemStatus()
      systemStatus.value = data
    } catch (error) {
      console.error('Failed to fetch system status:', error)
    }
  }

  // 更新信号状态
  const updateSignalStatus = (signalId, status) => {
    const signal = tradeSignals.value.signals.find(s => s.id === signalId)
    if (signal) {
      signal.status = status
    }
  }

  return {
    // 状态
    weekendScanResults,
    dailyPoolResults,
    tradeSignals,
    systemStatus,
    loading,

    // 方法
    fetchWeekendScan,
    fetchDailyPool,
    fetchSignals,
    fetchSystemStatus,
    updateSignalStatus
  }
})