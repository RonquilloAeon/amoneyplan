'use client';

import { useCallback, useEffect } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

interface UseUrlPaginationProps {
  totalItems: number;
  pageSize: number;
  paramName?: string;
}

export function useUrlPagination({ 
  totalItems, 
  pageSize, 
  paramName = 'page' 
}: UseUrlPaginationProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  // Get current page from URL or default to 1
  const currentPage = Number(searchParams.get(paramName) || '1');
  const totalPages = Math.ceil(totalItems / pageSize);

  // Update URL with page number when currentPage changes
  useEffect(() => {
    // Create a new URLSearchParams instance to modify
    const params = new URLSearchParams(searchParams);
    
    // Only add page parameter if it's not page 1 (cleaner URLs)
    if (currentPage === 1) {
      params.delete(paramName);
    } else {
      params.set(paramName, currentPage.toString());
    }
    
    // Convert params to string, only adding '?' if we have parameters
    const queryString = params.toString();
    const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
    
    // Update the URL without a full page refresh
    router.replace(newUrl, { scroll: false });
  }, [currentPage, pathname, router, searchParams, paramName]);

  // Navigation functions
  const goToNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      const params = new URLSearchParams(searchParams);
      params.set(paramName, (currentPage + 1).toString());
      router.push(`${pathname}?${params.toString()}`);
    }
  }, [currentPage, totalPages, searchParams, paramName, pathname, router]);

  const goToPreviousPage = useCallback(() => {
    if (currentPage > 1) {
      const params = new URLSearchParams(searchParams);
      if (currentPage - 1 === 1) {
        params.delete(paramName);
      } else {
        params.set(paramName, (currentPage - 1).toString());
      }
      const queryString = params.toString();
      const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
      router.push(newUrl);
    }
  }, [currentPage, searchParams, paramName, pathname, router]);

  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= totalPages) {
      const params = new URLSearchParams(searchParams);
      if (page === 1) {
        params.delete(paramName);
      } else {
        params.set(paramName, page.toString());
      }
      const queryString = params.toString();
      const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
      router.push(newUrl);
    }
  }, [totalPages, searchParams, paramName, pathname, router]);

  // Calculate indices for slicing data
  const indexOfLastItem = currentPage * pageSize;
  const indexOfFirstItem = indexOfLastItem - pageSize;

  return {
    currentPage,
    totalPages,
    indexOfFirstItem,
    indexOfLastItem,
    goToNextPage,
    goToPreviousPage,
    goToPage
  };
} 