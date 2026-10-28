import { InputNumber } from 'antd';

interface Props {
  value?: number;
  onChange?: (v: number | null) => void;
  placeholder?: string;
  min?: number;
  max?: number;
  disabled?: boolean;
}

export function KopecksInput({ value, onChange, placeholder, min, max, disabled }: Props) {
  const rubles = value != null ? value / 100 : undefined;

  const handleChange = (val: number | null) => {
    if (onChange) {
      onChange(val != null ? Math.round(val * 100) : null);
    }
  };

  return (
    <InputNumber
      style={{ width: '100%' }}
      value={rubles}
      onChange={handleChange}
      placeholder={placeholder}
      min={min != null ? min / 100 : 1}
      max={max != null ? max / 100 : undefined}
      precision={2}
      addonAfter="₽"
      disabled={disabled}
    />
  );
}
