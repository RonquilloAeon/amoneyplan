import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          return null;
        }

        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_GRAPHQL_URL}`, {
            method: 'POST',
            body: JSON.stringify({
              query: `
                mutation Login($username: String!, $password: String!) {
                  auth {
                    login(username: $username, password: $password) {
                      success
                      error
                      token
                    }
                  }
                }
              `,
              variables: {
                username: credentials.username,
                password: credentials.password
              }
            }),
            headers: { "Content-Type": "application/json" }
          });
          
          const data = await res.json();
          console.log('Auth response:', data);
          
          if (res.ok && data.data?.auth?.login?.success) {
            return {
              id: '1',
              name: credentials.username,
              email: `${credentials.username}@example.com`,
              accessToken: data.data.auth.login.token
            };
          }
          
          if (data.data?.auth?.login?.error) {
            throw new Error(data.data.auth.login.error);
          }
          
          return null;
        } catch (error) {
          console.error('Auth error:', error);
          return null;
        }
      }
    })
  ],
  pages: {
    signIn: '/login',
    error: '/login',
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
      }
      return token;
    },
    async session({ session, token }) {
      if (token) {
        session.accessToken = token.accessToken;
      }
      return session;
    }
  },
  session: {
    strategy: 'jwt',
  },
  secret: process.env.NEXTAUTH_SECRET,
  debug: process.env.NODE_ENV === 'development',
});

export { handler as GET, handler as POST }; 