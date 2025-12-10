import { createRouter, createWebHistory } from 'vue-router'
import WeekendScan from '@/views/WeekendScan.vue'
import DailyPool from '@/views/DailyPool.vue'
import Signals from '@/views/Signals.vue'
import StockDetail from '@/views/StockDetail.vue'

const routes = [
  {
    path: '/',
    name: 'WeekendScan',
    component: WeekendScan,
    meta: {
      title: '周末扫描结果'
    }
  },
  {
    path: '/daily-pool',
    name: 'DailyPool',
    component: DailyPool,
    meta: {
      title: '日筛选池'
    }
  },
  {
    path: '/signals',
    name: 'Signals',
    component: Signals,
    meta: {
      title: '交易信号'
    }
  },
  {
    path: '/stock/:code',
    name: 'StockDetail',
    component: StockDetail,
    props: true,
    meta: {
      title: '个股详情'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title} - A股量化交易筛选系统`
  next()
})

export default router