import { Badge, Col, Empty, Row, Space, Spin, Tabs, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAuctions } from '../api/auctions';
import type { Auction, AuctionStatus } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';

function kopecksToRubles(k: number) {
  return (k / 100).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });
}

const CABINET_STATUSES: AuctionStatus[] = ['draft', 'rejected', 'review', 'open', 'closed', 'paused'];

function AuctionRow({ auction }: { auction: Auction }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '8px 0',
        borderBottom: '1px solid #f0f0f0',
      }}
    >
      <StatusBadge status={auction.status} />
      <Link to={`/auctions/${auction.id}`} style={{ flex: 1 }}>
        {auction.title}
      </Link>
      <Typography.Text type="secondary">{kopecksToRubles(auction.budget_kopecks)}</Typography.Text>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        до {new Date(auction.ends_at).toLocaleDateString('ru-RU')}
      </Typography.Text>
    </div>
  );
}

export function CabinetPage() {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAuctions({ mine: true })
      .then((res) => setAuctions(res.results))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin style={{ display: 'block', margin: '64px auto' }} />;

  const grouped = CABINET_STATUSES.reduce<Record<AuctionStatus, Auction[]>>(
    (acc, s) => {
      acc[s] = auctions.filter((a) => a.status === s);
      return acc;
    },
    {} as Record<AuctionStatus, Auction[]>,
  );

  const statusLabels: Record<AuctionStatus, string> = {
    draft: 'Черновики',
    rejected: 'Отклонённые',
    review: 'На модерации',
    open: 'Открытые',
    closed: 'Закрытые',
    paused: 'Приостановлены',
  };

  const tabItems = CABINET_STATUSES.filter((s) => grouped[s].length > 0).map((s) => ({
    key: s,
    label: (
      <Space>
        {statusLabels[s]}
        <Badge count={grouped[s].length} style={{ backgroundColor: '#1677ff' }} />
      </Space>
    ),
    children:
      grouped[s].length === 0 ? (
        <Empty description="Нет задач" />
      ) : (
        grouped[s].map((a) => <AuctionRow key={a.id} auction={a} />)
      ),
  }));

  return (
    <div>
      <Typography.Title level={3}>Мой кабинет</Typography.Title>
      <Row gutter={24}>
        <Col xs={24}>
          {tabItems.length === 0 ? (
            <Empty description="У вас пока нет задач" />
          ) : (
            <Tabs items={tabItems} />
          )}
        </Col>
      </Row>
    </div>
  );
}
