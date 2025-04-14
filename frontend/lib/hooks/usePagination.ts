'use client';

import { useState } from 'react';

export type PageInfo = {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
};

export type Edge<T> = {
  node: T;
  cursor: string;
};

export type Connection<T> = {
  edges: Edge<T>[];
  pageInfo: PageInfo;
};

export type PaginationProps = {
  first?: number;
  after?: string;
  last?: number;
  before?: string;
};

export function usePagination<T>(itemsPerPage: number = 5) {
  const [currentCursor, setCurrentCursor] = useState<string | null>(null);
  const [pageInfo, setPageInfo] = useState<PageInfo>({
    hasNextPage: false,
    hasPreviousPage: false,
    startCursor: null,
    endCursor: null,
  });

  const handleNextPage = () => {
    if (pageInfo.hasNextPage && pageInfo.endCursor) {
      setCurrentCursor(pageInfo.endCursor);
    }
  };

  const handlePreviousPage = () => {
    if (pageInfo.hasPreviousPage && pageInfo.startCursor) {
      // In a real implementation, you'd need to track previous cursors.
      // This is a simplified version.
      setCurrentCursor(null);
    }
  };

  const updatePageInfo = (newPageInfo: PageInfo) => {
    setPageInfo(newPageInfo);
  };

  const variables = {
    first: itemsPerPage,
    after: currentCursor,
  };

  return {
    variables,
    pageInfo,
    updatePageInfo,
    handleNextPage,
    handlePreviousPage,
    currentCursor,
    setCurrentCursor,
  };
} 