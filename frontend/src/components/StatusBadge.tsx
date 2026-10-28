import { Tag } from 'antd';
import type { AuctionStatus } from '../api/types';

const config: Record<AuctionStatus, { color: string; label: string }> = {
  draft: { color: 'default', label: 'Черновик' },
  review: { color: 'processing', label: 'На модерации' },
  rejected: { color: 'error', label: 'Отклонён' },
  open: { color: 'success', label: 'Открыт' },
  closed: { color: 'default', label: 'Закрыт' },
  paused: { color: 'warning', label: 'Приостановлен' },
};

export function StatusBadge({ status }: { status: AuctionStatus }) {
  const { color, label } = config[status] ?? { color: 'default', label: status };
  return <Tag color={color}>{label}</Tag>;
}
