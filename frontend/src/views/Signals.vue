<template>
  <div class="signals">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>交易信号</span>
          <div class="header-actions">
            <el-select v-model="statusFilter" @change="handleStatusChange" style="width: 120px; margin-right: 10px;">
              <el-option label="待处理" value="PENDING" />
              <el-option label="已确认" value="CONFIRMED" />
              <el-option label="已作废" value="INVALID" />
              <el-option label="全部" value="" />
            </el-select>
            <el-button
              type="primary"
              @click="refreshSignals"
              :icon="Refresh"
              :loading="loading"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 信号说明 -->
      <el-alert
        title="买入信号说明"
        type="warning"
        :closable="false"
        class="signal-info"
      >
        <p>信号识别逻辑：涨停板后回调2-8天形成缩量旗形，今日放量中阳突破</p>
        <p>操作建议：建议尾盘或次日早盘买入，严格设置止损位</p>
      </el-alert>

      <!-- 无信号提示 -->
      <el-empty v-if="!loading && tradeSignals.signals.length === 0" description="暂无交易信号" />

      <!-- 信号卡片列表 -->
      <div v-loading="loading" class="signals-container">
        <el-card
          v-for="signal in pagedSignals"
          :key="signal.id"
          class="signal-card"
          :class="getSignalCardClass(signal)"
        >
          <template #header>
            <div class="signal-header">
              <span class="stock-info">{{ signal.code }} - {{ signal.name }}</span>
              <el-tag :type="getSignalTypeTag(signal.signal_type)" size="large">{{ signal.signal_type }}</el-tag>
            </div>
          </template>

          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="信号价格">
              <span class="price">¥{{ signal.signal_price }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="涨停日期">{{ formatDate(signal.limit_up_date) }}</el-descriptions-item>
            <el-descriptions-item label="回调天数">{{ signal.pullback_days }}天</el-descriptions-item>
            <el-descriptions-item label="放量倍数"><span class="highlight">{{ signal.volume_ratio }}倍</span></el-descriptions-item>
            <el-descriptions-item label="涨幅"><span class="highlight">{{ signal.price_change }}%</span></el-descriptions-item>
            <el-descriptions-item label="上影线">{{ signal.upper_shadow }}%</el-descriptions-item>
            <el-descriptions-item label="止损价" span="2">
              <span class="stop-loss">¥{{ signal.stop_loss_price }}</span>
              ({{ signal.stop_loss_reason }})
            </el-descriptions-item>
          </el-descriptions>

          <el-alert
            :title="signal.reason"
            :type="getReasonAlertType(signal)"
            style="margin-top: 15px"
            :closable="false"
          />

          <div class="actions">
            <el-button
              v-if="signal.status === 'PENDING'"
              type="success"
              @click="confirmSignal(signal.id)"
              :icon="Check"
            >
              确认买入
            </el-button>
            <el-button
              v-if="signal.status === 'PENDING'"
              type="danger"
              @click="invalidateSignal(signal.id)"
              :icon="Close"
            >
              作废
            </el-button>
            <el-button
              @click="viewKLine(signal.code)"
              :icon="TrendCharts"
            >
              查看K线
            </el-button>
            <el-button
              @click="viewDetail(signal)"
              :icon="InfoFilled"
            >
              详情
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 分页 -->
      <div v-if="tradeSignals.signals.length > 0" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20]"
          :total="tradeSignals.signals.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 信号详情弹窗 -->
    <SignalDetailDialog
      v-model:visible="detailVisible"
      :signal="currentSignal"
      @status-changed="handleStatusChanged"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStockStore } from '@/stores/stock'
import { Refresh, Check, Close, TrendCharts, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { updateSignalStatus } from '@/api/stock'
import SignalDetailDialog from '@/components/SignalDetailDialog.vue'

const route = useRoute()
const stockStore = useStockStore()

// 分页
const currentPage = ref(1)
const pageSize = ref(5)

// 状态过滤
const statusFilter = ref('PENDING')

// 弹窗状态
const detailVisible = ref(false)
const currentSignal = ref(null)

// 计算属性
const loading = computed(() => stockStore.loading)

const tradeSignals = computed(() => stockStore.tradeSignals)

// 分页数据
const pagedSignals = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return tradeSignals.value.signals.slice(start, end)
})

// 方法
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const getSignalCardClass = (signal) => {
  return {
    'signal-pending': signal.status === 'PENDING',
    'signal-confirmed': signal.status === 'CONFIRMED',
    'signal-invalid': signal.status === 'INVALID'
  }
}

const getSignalTypeTag = (type) => {
  return type === 'BUY' ? 'success' : 'danger'
}

const getReasonAlertType = (signal) => {
  switch (signal.status) {
    case 'CONFIRMED':
      return 'success'
    case 'INVALID':
      return 'error'
    default:
      return 'warning'
  }
}

const handleStatusChange = () => {
  currentPage.value = 1
  loadSignals()
}

const refreshSignals = async () => {
  await loadSignals()
}

const loadSignals = async () => {
  await stockStore.fetchSignals(statusFilter.value || undefined)
}

const confirmSignal = async (signalId) => {
  try {
    await ElMessageBox.confirm(
      '确认要买入该股票吗？请在实际交易后确认。',
      '确认买入',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await updateSignalStatus(signalId, 'CONFIRMED', '已实际买入')
    stockStore.updateSignalStatus(signalId, 'CONFIRMED')

    ElMessage.success('信号已确认')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败：' + error.message)
    }
  }
}

const invalidateSignal = async (signalId) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      '请输入作废原因：',
      '作废信号',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^\S{2,}$/,
        inputErrorMessage: '请输入至少2个字符'
      }
    )

    await updateSignalStatus(signalId, 'INVALID', reason)
    stockStore.updateSignalStatus(signalId, 'INVALID')

    ElMessage.success('信号已作废')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败：' + error.message)
    }
  }
}

const viewKLine = (code) => {
  // TODO: 打开K线图表弹窗
  ElMessage.info('K线功能开发中...')
}

const viewDetail = (signal) => {
  currentSignal.value = signal
  detailVisible.value = true
}

const handleStatusChanged = (signalId, newStatus) => {
  stockStore.updateSignalStatus(signalId, newStatus)
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 生命周期
onMounted(async () => {
  // 如果有路由参数，过滤特定股票
  if (route.query.code) {
    // TODO: 实现按股票代码过滤
  }

  if (!tradeSignals.value.signalDate) {
    await loadSignals()
  }
})
</script>

<style scoped>
.signals {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.signal-info {
  margin-bottom: 20px;
}

.signal-info p {
  margin: 5px 0;
}

.signals-container {
  margin-top: 20px;
}

.signal-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.signal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.signal-card.signal-pending {
  border-left: 4px solid #E6A23C;
}

.signal-card.signal-confirmed {
  border-left: 4px solid #67C23A;
}

.signal-card.signal-invalid {
  border-left: 4px solid #F56C6C;
  opacity: 0.8;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-info {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.price {
  font-size: 16px;
  font-weight: bold;
  color: #F56C6C;
}

.highlight {
  font-weight: bold;
  color: #409EFF;
}

.stop-loss {
  font-weight: bold;
  color: #E6A23C;
}

.actions {
  margin-top: 15px;
  text-align: center;
}

.actions .el-button {
  margin: 0 5px;
}

.pagination-container {
  margin-top: 20px;
  text-align: center;
}

@media (max-width: 768px) {
  .signal-card {
    margin-bottom: 15px;
  }

  .stock-info {
    font-size: 16px;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .actions .el-button {
    flex: 1;
    margin: 0;
  }
}
</style>