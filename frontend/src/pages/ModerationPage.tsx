import { Button, Empty, Space, Spin, Table, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAuctions } from '../api/auctions';
import type { Auction } from '../api/types';

function kopecksToRubles(k: number) {
  return (k / 100).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });
}

export function ModerationPage() {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getAuctions({ status: 'review' })
      .then((res) => setAuctions(res.results))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const columns: ColumnsType<Auction> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: 'Заголовок',
      dataIndex: 'title',
      render: (title: string, record) => (
        <Link to={`/auctions/${record.id}`}>{title}</Link>
      ),
    },
    {
      title: 'Бюджет',
      dataIndex: 'budget_kopecks',
      render: (v: number) => kopecksToRubles(v),
      width: 140,
    },
    {
      title: 'Торги до',
      dataIndex: 'ends_at',
      render: (v: string) => new Date(v).toLocaleString('ru-RU'),
      width: 180,
    },
    {
      title: 'Действие',
      render: (_, record) => (
        <Link to={`/auctions/${record.id}`}>
          <Button size="small" type="primary">
            Рассмотреть
          </Button>
        </Link>
      ),
      width: 120,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          Очередь модерации
        </Typography.Title>
        <Button onClick={load} loading={loading}>
          Обновить
        </Button>
      </Space>

      {loading ? (
        <Spin style={{ display: 'block', margin: '64px auto' }} />
      ) : auctions.length === 0 ? (
        <Empty description="Очередь пуста" />
      ) : (
        <Table
          dataSource={auctions}
          columns={columns}
          rowKey="id"
          pagination={false}
        />
      )}
    </div>
  );
}
