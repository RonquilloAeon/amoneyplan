import { createClient, cacheExchange, fetchExchange } from '@urql/vue';
import type { Exchange, Operation, OperationResult } from '@urql/vue';
import { pipe, tap } from 'wonka';
import logger from '../utils/logger';

// Create a debug exchange to log all operations
const debugExchange: Exchange = ({ forward }) => ops$ => {
  return pipe(
    ops$,
    tap((operation: Operation) => {
      logger.debug('GraphQL:Request', `Operation: ${operation.kind} - ${operation.query.definitions[0].kind === 'OperationDefinition' ? operation.query.definitions[0].operation : 'unknown'}`, {
        name: operation.query.definitions[0].kind === 'OperationDefinition' ? 
          operation.query.definitions[0].name?.value : 'unnamed',
        variables: operation.variables
      });
    }),
    forward,
    tap((result: OperationResult) => {
      if (result.error) {
        logger.error('GraphQL:Response', 'Error in operation', result.error);
      } else {
        logger.debug('GraphQL:Response', 'Operation result', {
          data: result.data,
          stale: result.stale,
          hasNext: result.hasNext
        });
      }
    })
  );
};

// Add this before the client creation
// Intercept all fetch calls to log headers
const originalFetch = window.fetch;
window.fetch = async function(input, init) {
  const url = typeof input === 'string' ? input : input.url;
  
  if (url.includes('graphql')) {
    logger.debug('NetworkInspector', 'Request URL', url);
    logger.debug('NetworkInspector', 'Request headers', init?.headers);
    logger.debug('NetworkInspector', 'Request method', init?.method || 'GET');
    
    const response = await originalFetch(input, init);
    
    // Clone the response to log it without consuming it
    const clonedResponse = response.clone();
    
    // Log response details
    logger.debug('NetworkInspector', 'Response status', {
      status: clonedResponse.status,
      statusText: clonedResponse.statusText
    });
    
    // Log response headers
    const responseHeaders: Record<string, string> = {};
    clonedResponse.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });
    logger.debug('NetworkInspector', 'Response headers', responseHeaders);
    
    return response;
  }
  
  return originalFetch(input, init);
};

// Modified client to include auth token from localStorage
export const client = createClient({
  url: import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:8001/graphql/',
  fetchOptions: () => {
    const token = localStorage.getItem('token');
    logger.debug('GlobalClient', 'Fetching with token', token ? `${token.substring(0, 10)}...` : 'No token');
    
    return {
      credentials: 'include', // This enables sending cookies with requests
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
    };
  },
  exchanges: [debugExchange, cacheExchange, fetchExchange],
});