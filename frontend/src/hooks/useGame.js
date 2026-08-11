import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

export function useGame() {
  const [state, setState] = useState(null);

  const refresh = useCallback(async () => {
    const data = await api.getState();
    setState(data);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { state, setState, refresh };
}