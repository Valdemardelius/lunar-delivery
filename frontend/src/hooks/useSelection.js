import { useState } from 'react';

export function useSelection() {
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [selectedRoverId, setSelectedRoverId] = useState(null);

  const clearSelection = () => {
    setSelectedOrderId(null);
    setSelectedRoverId(null);
  };

  const selectOrder = (id) => {
    setSelectedOrderId(id);
    setSelectedRoverId(null);
  };

  return {
    selectedOrderId,
    selectedRoverId,
    setSelectedRoverId,
    selectOrder,
    clearSelection,
  };
}