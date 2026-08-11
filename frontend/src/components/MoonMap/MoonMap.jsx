import React, { useMemo } from 'react';
import { seededPos } from '../../utils/constants';

export default function MoonMap({ zones, base, orders, rovers, selectedOrderId, onSelectOrder }) {
  const craters = useMemo(
    () =>
      Array.from({ length: 14 }, (_, i) => ({
        cx: seededPos(i, 800),
        cy: seededPos(i + 50, 460),
        r: 3 + ((i * 7) % 10),
      })),
    []
  );

  const zonesById = useMemo(() => Object.fromEntries(zones.map((z) => [z.id, z])), [zones]);

  return (
    <svg id="moonmap" viewBox="0 0 800 460" xmlns="http://www.w3.org/2000/svg">
      {craters.map((c, i) => (
        <circle key={i} cx={c.cx} cy={c.cy} r={c.r} fill="#ffffff08" />
      ))}

      {zones.map((z) => (
        <g key={z.id}>
          <circle
            cx={z.cx} cy={z.cy} r={z.r}
            fill={z.color + '22'} stroke={z.color + '55'} strokeDasharray="4 4"
          />
          <text x={z.cx} y={z.cy - z.r - 8} textAnchor="middle" className="zone-label">
            {z.name}
          </text>
        </g>
      ))}

      <circle cx={base.x} cy={base.y} r={16} fill="#1a1f2b" stroke="var(--dust)" strokeWidth={2} />
      <circle cx={base.x} cy={base.y} r={5} fill="var(--dust)" />
      <text x={base.x} y={base.y + 30} textAnchor="middle" className="zone-label">База «Скол-9»</text>

      {orders.map((order) => {
        if (['completed', 'failed', 'expired'].includes(order.status)) {
          return (
            <circle
              key={order.id} cx={order.x} cy={order.y} r={5}
              fill={order.status === 'completed' ? '#6fd3b0' : '#e2617a'} opacity={0.5}
            />
          );
        }
        const zone = zonesById[order.zone_id];
        const r = 7 + Math.min(order.weight / 6, 6);
        const classNames = [
          'order-dot',
          order.status === 'pending' ? 'order-pulse' : '',
          selectedOrderId === order.id ? 'selected' : '',
        ].filter(Boolean).join(' ');
        return (
          <circle
            key={order.id}
            cx={order.x} cy={order.y} r={r}
            fill={order.status === 'in_transit' ? '#5a6070' : zone.color}
            className={classNames}
            onClick={() => order.status === 'pending' && onSelectOrder(order.id)}
          />
        );
      })}

      {rovers.map((rover, idx) => {
        let x = base.x, y = base.y - 26;
        if (rover.status === 'delivering' && rover.current_order_id) {
          const o = orders.find((o) => o.id === rover.current_order_id);
          if (o) { x = (o.x + base.x) / 2; y = (o.y + base.y) / 2; }
        }
        return (
          <circle
            key={rover.id}
            cx={x + idx * 14 - 14} cy={y} r={5}
            fill={rover.status === 'broken' ? '#e2617a' : '#e2a75a'}
            stroke="#000"
          />
        );
      })}
    </svg>
  );
}