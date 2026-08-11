import React from 'react';
import { batteryCost } from '../../utils/constants';

export default function OrderDetail({ order, zone, rovers, currentDay, selectedRoverId, onSelectRover, onSend, busy }) {
  if (!order || !zone) {
    return <div className="order-empty">Выберите точку заказа на карте, чтобы увидеть детали и отправить ровер.</div>;
  }

  const riskClass = zone.risk >= 0.25 ? 'risk-high' : zone.risk >= 0.12 ? 'risk-mid' : 'risk-low';
  const daysLeft = order.deadline_day - currentDay;
  const idleRovers = rovers.filter((r) => r.status === 'idle');
  const noneCanCarryWeight = idleRovers.length > 0 && idleRovers.every((r) => order.weight > r.cargo_capacity);

  return (
    <div>
      <div className="order-title">Заказ {order.id}</div>
      <div className="order-zone">Зона: {zone.name}</div>

      <div className="kv"><span>Вес груза</span><b>{order.weight} кг</b></div>
      <div className="kv"><span>Награда</span><b style={{ color: 'var(--dust)' }}>{order.reward} ₭</b></div>
      <div className="kv"><span>Риск маршрута</span><b className={riskClass}>{Math.round(zone.risk * 100)}%</b></div>
      <div className="kv"><span>Дедлайн</span><b>{daysLeft <= 1 ? 'сегодня!' : `через ${daysLeft} дн.`}</b></div>

      <select value={selectedRoverId || ''} onChange={(e) => onSelectRover(e.target.value || null)}>
        <option value="">— выбрать ровер —</option>
        {idleRovers.map((r) => {
          const cost = batteryCost(zone, order.weight);
          const ok = order.weight <= r.cargo_capacity && cost <= r.battery;
          const reason = ok ? `${cost}⚡ ok` : order.weight > r.cargo_capacity ? 'вес превышен' : 'не хватит заряда';
          return (
            <option key={r.id} value={r.id} disabled={!ok}>
              {r.name} — {reason}
            </option>
          );
        })}
      </select>

      <button className="send-btn" disabled={!selectedRoverId || busy} onClick={onSend}>
        Отправить ровер
      </button>

      {idleRovers.length === 0 && (
        <div className="warn-msg">Нет свободных роверов — все в пути или сломаны.</div>
      )}
      {noneCanCarryWeight && (
        <div className="warn-msg">Ни один ровер не поднимет такой вес. Заказ придётся пропустить.</div>
      )}
    </div>
  );
}