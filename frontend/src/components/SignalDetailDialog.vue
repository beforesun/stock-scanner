<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`信号详情 - ${signal?.code} ${signal?.name}`"
    width="600px"
    @closed="handleClosed"
  >
    <template v-if="signal">
      <!-- 基本信息 -->
      <el-descriptions :column="2" border title="基本信息">
        <el-descriptions-item label="信号类型">
          <el-tag :type="signal.signal_type === 'BUY' ? 'success' : 'danger'">{{ signal.signal_type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="信号日期">{{ formatDate(signal.signal_date) }}</el-descriptions-item>
        <el-descriptions-item label="信号价格">
          <span class="price">¥{{ signal.signal_price }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="当前状态">
          <el-tag :type="getStatusType(signal.status)">{{ getStatusText(signal.status) }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 买入信号参数 -->
      <el-descriptions :column="2" border title="买入信号参数" class="mt-20"
        v-if="signal.signal_type === 'BUY'">
        <el-descriptions-item label="涨停日期">{{ formatDate(signal.limit_up_date) }}</el-descriptions-item>
        <el-descriptions-item label="回调天数">{{ signal.pullback_days }}天</el-descriptions-item>
        <el-descriptions-item label="放量倍数"><span class="highlight">{{ signal.volume_ratio }}倍</span></el-descriptions-item>
        <el-descriptions-item label="涨幅"><span class="highlight">{{ signal.price_change }}%</span></el-descriptions-item>
        <el-descriptions-item label="上影线占比">{{ signal.upper_shadow }}%</el-descriptions-item>
        <el-descriptions-item label="止损价格">
          <span class="stop-loss">¥{{ signal.stop_loss_price }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 信号理由 -->
      <el-descriptions :column="1" border title="信号理由" class="mt-20">
        <el-descriptions-item>
          {{ signal.reason }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 状态操作 -->
      <div v-if="signal.status === 'PENDING'" class="actions mt-20">
        <el-button
          type="success"
          size="large"
          @click="handleConfirm"
          :icon="Check"
        >
          确认买入
        </el-button>
        <el-button
          type="danger"
          size="large"
          @click="handleInvalidate"
          :icon="Close"
        >
          作废信号
        </el-button>
      </div>

      <!-- 状态更新历史 -->
      <el-descriptions :column="1" border title="状态更新" class="mt-20"
        v-if="signal.status !== 'PENDING'">
        <el-descriptions-item label="更新时间">{{ formatDateTime(signal.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新备注" v-if="signal.note">{{ signal.note }}</el-descriptions-item>
      </el-descriptions>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Check, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSignalDetail, updateSignalStatus } from '@/api/stock'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  signalId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'status-changed'])

// 信号详情
const signal = ref(null)
const loading = ref(false)

// 可见性计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 监听信号ID变化
watch(
  () => props.signalId,
  (newId) => {
    if (newId) {
      loadSignalDetail()
    }
  },
  { immediate: true }
)

// 加载信号详情
const loadSignalDetail = async () => {
  if (!props.signalId) return

  loading.value = true
  try {
    signal.value = await getSignalDetail(props.signalId)
  } catch (error) {
    ElMessage.error('加载信号详情失败')
    dialogVisible.value = false
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取状态样式
const getStatusType = (status) => {
  const typeMap = {
    'PENDING': 'warning',
    'CONFIRMED': 'success',
    'INVALID': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'PENDING': '待处理',
    'CONFIRMED': '已确认',
    'INVALID': '已作废'
  }
  return textMap[status] || status
}

// 处理确认
const handleConfirm = async () => {
  try {
    await ElMessageBox.confirm(
      '确认已买入该股票吗？',
      '确认买入',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await updateSignalStatus(signal.value.id, 'CONFIRMED', '已实际买入')

    ElMessage.success('信号已确认')
    emit('status-changed', signal.value.id, 'CONFIRMED')
    dialogVisible.value = false
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 处理作废
const handleInvalidate = async () => {
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

    await updateSignalStatus(signal.value.id, 'INVALID', reason)

    ElMessage.success('信号已作废')
    emit('status-changed', signal.value.id, 'INVALID')
    dialogVisible.value = false
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 处理弹窗关闭
const handleClosed = () => {
  signal.value = null
}
</script>

<style scoped>
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
  text-align: center;
}

.mt-20 {
  margin-top: 20px;
}

:deep(.el-descriptions__label) {
  width: 100px;
}
</style>