# AMoneyPlan Frontend

A modern financial planning application built with Next.js, TypeScript, React, and Apollo GraphQL.

## Features

- User authentication with NextAuth.js
- Create and manage financial plans
- Add and track multiple accounts
- Real-time updates with Apollo GraphQL
- Responsive design with Tailwind CSS
- Type-safe development with TypeScript

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── (auth)/            # Authentication routes
│   ├── (dashboard)/       # Protected dashboard routes
│   ├── api/               # API routes
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── accounts/          # Account-related components
│   ├── auth/              # Authentication components
│   ├── common/            # Shared components
│   ├── layout/            # Layout components
│   └── plans/             # Plan-related components
├── lib/                   # Utility functions and hooks
│   ├── apollo/            # Apollo Client configuration
│   ├── auth/              # Authentication utilities
│   ├── graphql/           # GraphQL operations and types
│   ├── hooks/             # Custom React hooks
│   └── utils/             # Utility functions
└── middleware.ts          # Next.js middleware for auth
```

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create a `.env.local` file with the following variables:
   ```
   NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8000/graphql/
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=your-secret-key
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Development

- `npm run dev` - Start the development server
- `npm run build` - Build the production application
- `npm run start` - Start the production server
- `npm run lint` - Run ESLint

## Technologies Used

- [Next.js](https://nextjs.org/) - React framework
- [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript
- [Apollo Client](https://www.apollographql.com/docs/react/) - GraphQL client
- [NextAuth.js](https://next-auth.js.org/) - Authentication
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [React Hook Form](https://react-hook-form.com/) - Form handling
- [Zod](https://zod.dev/) - Schema validation 