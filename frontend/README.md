# CORD-19 Search Engine - Frontend

Modern React + TypeScript frontend for the CORD-19 Search Engine.

## Features

- 🔍 **Search Interface**: Clean, intuitive search bar with autocomplete
- 📄 **Document Viewer**: Full document display with formatted sections and references
- 🎨 **Modern UI**: Beautiful pastel-themed design with Tailwind CSS
- ⚡ **Fast**: Built with Vite for optimal performance
- 🔄 **Real-time**: Live search results with loading states

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Lucide React** - Icons

## Prerequisites

- Node.js 16+ and npm
- Backend API server running on `http://localhost:8000`

## Installation

```bash
# Install dependencies
npm install
```

## Development

```bash
# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Build for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── SearchBar.tsx
│   │   ├── SearchResults.tsx
│   │   └── DocumentViewer.tsx
│   ├── services/         # API client
│   │   └── api.ts
│   ├── types.ts          # TypeScript interfaces
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── index.html            # HTML template
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── vite.config.ts        # Vite configuration
└── tailwind.config.js    # Tailwind CSS config
```

## Backend Integration

The frontend expects the backend API to be running on `http://localhost:8000` with the following endpoints:

- `POST /api/search` - Search endpoint
- `GET /api/autocomplete?prefix=...` - Autocomplete suggestions
- `GET /api/document/{doc_id}` - Get full document

The API proxy is configured in `vite.config.ts`.

## Configuration

### Change API URL

If your backend is running on a different URL, update `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // Change this
      changeOrigin: true,
    }
  }
}
```

## License

See main repository for license information.

