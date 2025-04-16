import { NextResponse } from 'next/server';
import { executeGraphQL } from '@/lib/graphqlClient'; // Assuming you have a GraphQL client utility

// Define the GraphQL mutation string
const REGISTER_MUTATION = `
  mutation Register(
    $username: String!,
    $email: String!,
    $password: String!,
    $firstName: String,
    $lastName: String
  ) {
    auth {
      register(
        username: $username,
        email: $email,
        password: $password,
        firstName: $firstName,
        lastName: $lastName
      ) {
        success
        error
        token # Optional: Decide if you want the token back here or during login
      }
    }
  }
`;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { username, email, password, firstName, lastName } = body;

    if (!username || !email || !password) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    // Execute the GraphQL mutation
    const { data, errors } = await executeGraphQL({
      query: REGISTER_MUTATION,
      variables: { username, email, password, firstName, lastName },
      // No authorization header needed for registration
    });

    if (errors || !data?.auth?.register?.success) {
      // Extract specific error message if available
      const errorMessage = data?.auth?.register?.error || errors?.[0]?.message || 'Registration failed on backend';
      return NextResponse.json({ error: errorMessage }, { status: 400 });
    }

    // Registration successful
    // Optionally return the token if your mutation provides it and you want to use it immediately
    // For now, we just return success and let the AuthContext handle login
    return NextResponse.json({ success: true });

  } catch (error) {
    console.error('Registration API Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
} 