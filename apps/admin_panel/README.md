# NutriMatch Admin Panel

A standalone admin dashboard for managing the NutriMatch platform.

## Features

- 🔐 Admin authentication with JWT
- 📊 Dashboard with platform statistics
- 👩‍⚕️ Nutritionist verification management
- 👥 User management (placeholder)
- 📅 Booking management (placeholder)
- ⚙️ Platform settings (placeholder)

## Tech Stack

- **React 18** + TypeScript
- **Vite** for build tooling
- **TailwindCSS** for styling
- **React Router** for navigation
- **TanStack Query** for data fetching
- **Zustand** for state management
- **Axios** for HTTP requests

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The admin panel will be available at `http://localhost:5174/admin`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

### Environment Variables

The admin panel uses the backend API for authentication and data. Configure the API endpoint in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000', // Backend URL
      changeOrigin: true,
    },
  },
},
```

### Admin Credentials

Default admin credentials are configured via environment variables in the backend:

- `ADMIN_EMAIL`: Admin email (default: `admin@nutrimatch.io`)
- `ADMIN_PASSWORD`: Admin password (default: `admin123`)

⚠️ **Important**: Change these credentials in production!

## Project Structure

```
apps/admin_panel/
├── src/
│   ├── components/     # Reusable UI components
│   ├── lib/            # API client and utilities
│   ├── pages/          # Page components
│   ├── store/          # Zustand stores
│   ├── types/          # TypeScript types
│   ├── App.tsx         # Main app with routing
│   ├── main.tsx        # Entry point
│   └── index.css       # Global styles
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.ts      # Vite configuration
├── tailwind.config.js  # Tailwind configuration
└── tsconfig.json       # TypeScript configuration
```

## API Endpoints

The admin panel communicates with these backend endpoints:

### Authentication
- `POST /api/admin/auth/login` - Admin login
- `GET /api/admin/auth/me` - Get current admin user
- `POST /api/admin/auth/logout` - Logout

### Nutritionists
- `GET /api/admin/nutritionists` - List nutritionists
- `GET /api/admin/nutritionists/:id` - Get nutritionist details
- `POST /api/admin/nutritionists/:id/approve` - Approve nutritionist
- `POST /api/admin/nutritionists/:id/reject` - Reject nutritionist
- `POST /api/admin/nutritionists/:id/request-update` - Request updates

### Documents
- `POST /api/admin/documents/:id/review` - Review document

## Independence

This admin panel is completely independent from the client Mini App:

- Separate codebase in `/apps/admin_panel`
- No shared state with client
- Communicates with backend via HTTP only
- Can be removed without affecting other parts of the system

## License

Private - NutriMatch

