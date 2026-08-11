export const statusLabel = {
  idle: 'готов',
  delivering: 'в пути',
  broken: 'сломан',
};

export const batteryCost = (zone, weight) =>
  Math.round(zone.base_cost + weight * 1.6);

export const seededPos = (seed, max) =>
  (((Math.sin(seed * 999) * 10000) % 1 + 1) / 2) * max;