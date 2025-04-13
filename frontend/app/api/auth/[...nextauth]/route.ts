import NextAuth from "next-auth/next";
import CredentialsProvider from "next-auth/providers/credentials";
import { gql } from '@apollo/client';
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';

// Create a simple Apollo client for authentication
const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8001/graphql/',
});

const client = new ApolloClient({
  link: httpLink,
  cache: new InMemoryCache(),
});

// GraphQL mutations for auth
const LOGIN_MUTATION = gql`
  mutation Login($username: String!, $password: String!) {
    auth {
      login(username: $username, password: $password) {
        success
        token
        error
      }
    }
  }
`;

const ME_QUERY = gql`
  query Me {
    me {
      id
      username
      email
      firstName
      lastName
    }
  }
`;

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials.password) {
          return null;
        }

        try {
          // Call the GraphQL API to authenticate
          const { data } = await client.mutate({
            mutation: LOGIN_MUTATION,
            variables: {
              username: credentials.username,
              password: credentials.password,
            },
          });

          const authResult = data?.auth?.login;

          // Handle authentication failure
          if (!authResult?.success) {
            console.error("Auth failed:", authResult?.error);
            return null;
          }

          // Return a user object with the token
          return {
            id: "user-id", // will be filled in by the callback
            name: credentials.username,
            email: "",     // will be filled in by the callback
            token: authResult.token,
          };
        } catch (error) {
          console.error("Auth error:", error);
          return null;
        }
      }
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign in
      if (user) {
        token.authToken = user.token;
        
        try {
          // Use the token to fetch user details
          const { data } = await client.query({
            query: ME_QUERY,
            context: {
              headers: {
                authorization: `Bearer ${user.token}`
              }
            }
          });
          
          if (data?.me) {
            token.id = data.me.id;
            token.name = data.me.username;
            token.email = data.me.email;
            token.firstName = data.me.firstName;
            token.lastName = data.me.lastName;
          }
        } catch (error) {
          console.error("Error fetching user data:", error);
        }
      }
      return token;
    },
    async session({ session, token }) {
      if (token) {
        session.user = {
          id: token.id,
          name: token.name,
          email: token.email,
          firstName: token.firstName,
          lastName: token.lastName,
        };
        session.authToken = token.authToken;
      }
      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET || "your-default-secret-do-not-use-in-production",
});

export { handler as GET, handler as POST }; 