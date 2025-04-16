interface ExecuteGraphQLOptions {
  query: string;
  variables?: Record<string, any>;
  token?: string; // Optional token for authenticated requests
}

/**
 * Executes a GraphQL query or mutation against the backend API.
 * Handles sending the request and basic error handling.
 */
export async function executeGraphQL<T = any>(
  { query, variables, token }: ExecuteGraphQLOptions
): Promise<{ data?: T; errors?: any[] }> {
  const graphqlEndpoint = process.env.NEXT_PUBLIC_GRAPHQL_URL;

  if (!graphqlEndpoint) {
    console.error('GraphQL endpoint URL is not configured. Set NEXT_PUBLIC_GRAPHQL_URL.');
    return { errors: [{ message: 'GraphQL endpoint not configured' }] };
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(graphqlEndpoint, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ query, variables }),
      // cache: 'no-store' // Use this to prevent caching if necessary, especially for mutations
    });

    const result = await response.json();

    if (!response.ok || result.errors) {
      console.error('GraphQL Request Error:', result.errors || `HTTP status ${response.status}`);
      return { errors: result.errors || [{ message: `Request failed with status ${response.status}` }] };
    }

    return { data: result.data };

  } catch (error) {
    console.error('Failed to execute GraphQL request:', error);
    const message = error instanceof Error ? error.message : 'Unknown error during GraphQL request';
    return { errors: [{ message }] };
  }
} 