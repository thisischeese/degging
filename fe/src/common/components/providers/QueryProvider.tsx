"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [query_client] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={query_client}>
      {children}
    </QueryClientProvider>
  );
}