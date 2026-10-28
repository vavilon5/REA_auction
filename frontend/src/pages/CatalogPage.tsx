import {
  Card,
  Col,
  Input,
  Pagination,
  Row,
  Select,
  Spin,
  Typography,
  Empty,
  Space,
} from 'antd';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAuctions, getCategories } from '../api/auctions';
import type { Auction, AuctionFilters, AuctionStatus, Category } from '../api/types';
import { StatusBadge } from '../components/StatusBadge';

function kopecksToRubles(k: number) {
  return (k / 100).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });
}

function AuctionCardItem({ auction }: { auction: Auction }) {
  return (
    <Card
      hoverable
      size="small"
      title={
        <Space>
          <StatusBadge status={auction.status} />
          <Link to={`/auctions/${auction.id}`}>{auction.title}</Link>
        </Space>
      }
    >
      <Typography.Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 8 }}>
        {auction.description}
      </Typography.Paragraph>
      <Typography.Text strong>{kopecksToRubles(auction.budget_kopecks)}</Typography.Text>
      <Typography.Text type="secondary" style={{ marginLeft: 12 }}>
        до {new Date(auction.ends_at).toLocaleString('ru-RU')}
      </Typography.Text>
    </Card>
  );
}

const STATUS_OPTIONS: { value: AuctionStatus; label: string }[] = [
  { value: 'open', label: 'Открытые' },
  { value: 'closed', label: 'Закрытые' },
  { value: 'review', label: 'На модерации' },
  { value: 'draft', label: 'Черновики' },
  { value: 'rejected', label: 'Отклонённые' },
];

export function CatalogPage() {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<AuctionFilters>({ status: 'open' });
  const [search, setSearch] = useState('');

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    getAuctions(filters)
      .then((res) => {
        setAuctions(res.results);
        setTotal(res.count);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filters]);

  const handleSearch = () => {
    setFilters((f) => ({ ...f, search: search || undefined, page: 1 }));
  };

  return (
    <div>
      <Typography.Title level={3}>Каталог аукционов</Typography.Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="Поиск по названию..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onSearch={handleSearch}
          style={{ width: 280 }}
          allowClear
          onClear={() => setFilters((f) => ({ ...f, search: undefined, page: 1 }))}
        />
        <Select
          placeholder="Статус"
          allowClear
          value={filters.status}
          onChange={(v) => setFilters((f) => ({ ...f, status: v, page: 1 }))}
          style={{ width: 180 }}
          options={STATUS_OPTIONS}
        />
        <Select
          placeholder="Категория"
          allowClear
          value={filters.category}
          onChange={(v) => setFilters((f) => ({ ...f, category: v, page: 1 }))}
          style={{ width: 200 }}
          options={categories.map((c) => ({ value: c.id, label: c.name }))}
        />
      </Space>

      {loading ? (
        <Spin style={{ display: 'block', margin: '48px auto' }} />
      ) : auctions.length === 0 ? (
        <Empty description="Нет аукционов" />
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {auctions.map((a) => (
              <Col key={a.id} xs={24} sm={12} lg={8}>
                <AuctionCardItem auction={a} />
              </Col>
            ))}
          </Row>
          <Pagination
            style={{ marginTop: 24, textAlign: 'right' }}
            current={filters.page ?? 1}
            pageSize={20}
            total={total}
            onChange={(p) => setFilters((f) => ({ ...f, page: p }))}
            showTotal={(t) => `Всего: ${t}`}
          />
        </>
      )}
    </div>
  );
}
