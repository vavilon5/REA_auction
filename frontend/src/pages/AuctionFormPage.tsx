import {
  Alert,
  Button,
  DatePicker,
  Form,
  Input,
  Select,
  Spin,
  Typography,
  message,
} from 'antd';
import dayjs from 'dayjs';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createAuction, getAuction, getCategories, patchAuction } from '../api/auctions';
import type { Category } from '../api/types';
import { KopecksInput } from '../components/KopecksInput';

interface FormValues {
  category: number;
  title: string;
  description: string;
  budget_kopecks: number;
  ends_at: dayjs.Dayjs;
  due_at: dayjs.Dayjs;
}

export function AuctionFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const auctionId = id ? Number(id) : null;
  const navigate = useNavigate();

  const [form] = Form.useForm<FormValues>();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    if (!auctionId) return;
    getAuction(auctionId)
      .then((a) => {
        form.setFieldsValue({
          category: a.category,
          title: a.title,
          description: a.description,
          budget_kopecks: a.budget_kopecks,
          ends_at: dayjs(a.ends_at),
          due_at: dayjs(a.due_at),
        });
      })
      .catch(() => setError('Не удалось загрузить аукцион'))
      .finally(() => setLoading(false));
  }, [auctionId]);

  const onFinish = async (values: FormValues) => {
    setSaving(true);
    setError('');
    const payload = {
      category: values.category,
      title: values.title,
      description: values.description,
      budget_kopecks: values.budget_kopecks,
      ends_at: values.ends_at.toISOString(),
      due_at: values.due_at.toISOString(),
    };
    try {
      const auction = isEdit && auctionId
        ? await patchAuction(auctionId, payload)
        : await createAuction(payload);
      message.success(isEdit ? 'Сохранено' : 'Задача создана');
      navigate(`/auctions/${auction.id}`);
    } catch (err: unknown) {
      const data = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      if (data) {
        const msgs = Object.entries(data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('\n');
        setError(msgs);
      } else {
        setError('Ошибка сохранения');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spin style={{ display: 'block', margin: '64px auto' }} />;

  return (
    <div style={{ maxWidth: 640 }}>
      <Button style={{ marginBottom: 16 }} onClick={() => navigate(-1)}>
        ← Назад
      </Button>
      <Typography.Title level={3}>
        {isEdit ? 'Редактировать задачу' : 'Новая задача'}
      </Typography.Title>

      {error && (
        <Alert
          type="error"
          message={<pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{error}</pre>}
          style={{ marginBottom: 16 }}
        />
      )}

      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item
          label="Категория"
          name="category"
          rules={[{ required: true, message: 'Выберите категорию' }]}
        >
          <Select
            placeholder="Категория"
            options={categories.map((c) => ({ value: c.id, label: c.name }))}
          />
        </Form.Item>

        <Form.Item
          label="Заголовок"
          name="title"
          rules={[
            { required: true, message: 'Введите заголовок' },
            { min: 5, message: 'Минимум 5 символов' },
            { max: 150, message: 'Максимум 150 символов' },
          ]}
        >
          <Input showCount maxLength={150} />
        </Form.Item>

        <Form.Item
          label="Описание"
          name="description"
          rules={[
            { required: true, message: 'Введите описание' },
            { min: 20, message: 'Минимум 20 символов' },
            { max: 5000, message: 'Максимум 5000 символов' },
          ]}
        >
          <Input.TextArea rows={6} showCount maxLength={5000} />
        </Form.Item>

        <Form.Item
          label="Бюджет"
          name="budget_kopecks"
          rules={[{ required: true, message: 'Укажите бюджет' }]}
        >
          <KopecksInput min={100} />
        </Form.Item>

        <Form.Item
          label="Торги до"
          name="ends_at"
          rules={[
            { required: true, message: 'Укажите срок торгов' },
            {
              validator: (_, value) =>
                value && value.isAfter(dayjs())
                  ? Promise.resolve()
                  : Promise.reject('Дата должна быть в будущем'),
            },
          ]}
        >
          <DatePicker
            showTime
            style={{ width: '100%' }}
            disabledDate={(d) => d.isBefore(dayjs(), 'day')}
          />
        </Form.Item>

        <Form.Item
          label="Срок выполнения"
          name="due_at"
          dependencies={['ends_at']}
          rules={[
            { required: true, message: 'Укажите срок выполнения' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                const endsAt = getFieldValue('ends_at');
                if (!value || !endsAt || value.isAfter(endsAt)) {
                  return Promise.resolve();
                }
                return Promise.reject('Срок выполнения должен быть позже окончания торгов');
              },
            }),
          ]}
        >
          <DatePicker
            showTime
            style={{ width: '100%' }}
            disabledDate={(d) => d.isBefore(dayjs(), 'day')}
          />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={saving}>
            {isEdit ? 'Сохранить' : 'Создать задачу'}
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
}
