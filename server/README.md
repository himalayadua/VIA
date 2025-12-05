# Via Canvas API Server

Backend REST API server for Via Canvas application built with Express.js and PostgreSQL.

## Structure

```
server/
├── src/
│   ├── index.ts           # Main Express server
│   ├── db.ts              # PostgreSQL connection pool
│   └── routes/
│       ├── canvases.ts    # Canvas CRUD operations
│       ├── nodes.ts       # Node CRUD operations
│       ├── connections.ts # Connection CRUD operations
│       └── snapshots.ts   # Canvas snapshot operations
├── package.json
└── tsconfig.json
```

## API Endpoints

### Health Check

#### GET /health
Check server and database connectivity.

**Response:**
```json
{
  "status": "ok",
  "database": "connected"
}
```

#### GET /
API information and version.

**Response:**
```json
{
  "name": "Via Canvas API",
  "version": "1.0.0"
}
```

---

### Canvases

#### GET /api/canvases
List all canvases ordered by last updated.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "My Canvas",
    "description": "Canvas description",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/canvases/:id
Get a single canvas by ID.

**Response:**
```json
{
  "id": "uuid",
  "name": "My Canvas",
  "description": "Canvas description",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Errors:**
- `404` - Canvas not found

#### POST /api/canvases
Create a new canvas.

**Request Body:**
```json
{
  "name": "My New Canvas",
  "description": "Optional description"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "My New Canvas",
  "description": "Optional description",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Errors:**
- `400` - Canvas name is required

#### PUT /api/canvases/:id
Update canvas name and/or description.

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Updated Name",
  "description": "Updated description",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Errors:**
- `400` - No fields to update
- `404` - Canvas not found

#### DELETE /api/canvases/:id
Delete a canvas and all associated nodes, connections, and snapshots (cascade delete).

**Response:**
```json
{
  "message": "Canvas deleted successfully",
  "canvas": { /* deleted canvas object */ }
}
```

**Errors:**
- `404` - Canvas not found

---

### Nodes

#### GET /api/nodes?canvas_id=:id
List all nodes for a specific canvas.

**Query Parameters:**
- `canvas_id` (required) - Canvas UUID

**Response:**
```json
[
  {
    "id": "uuid",
    "canvas_id": "uuid",
    "parent_id": "uuid or null",
    "content": "Node content",
    "title": "Node title",
    "card_type": "rich_text",
    "card_data": { /* type-specific data */ },
    "tags": ["tag1", "tag2"],
    "position_x": 100,
    "position_y": 200,
    "width": 300,
    "height": 200,
    "type": "richText",
    "style": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/nodes/:id
Get a single node by ID.

**Response:** Same as node object above

**Errors:**
- `404` - Node not found

#### POST /api/nodes
Create a new node.

**Request Body:**
```json
{
  "canvas_id": "uuid",
  "parent_id": "uuid or null",
  "content": "Node content",
  "title": "Node title",
  "card_type": "rich_text",
  "card_data": {},
  "tags": [],
  "position_x": 100,
  "position_y": 200,
  "type": "richText"
}
```

**Response:** `201 Created` - Returns created node object

**Errors:**
- `400` - Canvas ID is required

#### PUT /api/nodes/:id
Update a node.

**Request Body:** (all fields optional)
```json
{
  "content": "Updated content",
  "title": "Updated title",
  "card_type": "todo",
  "card_data": { "items": [] },
  "tags": ["new-tag"],
  "position_x": 150,
  "position_y": 250
}
```

**Response:** Returns updated node object

**Errors:**
- `400` - No fields to update
- `404` - Node not found

#### DELETE /api/nodes/:id
Delete a node.

**Response:**
```json
{
  "message": "Node deleted successfully",
  "node": { /* deleted node object */ }
}
```

**Errors:**
- `404` - Node not found

#### POST /api/nodes/batch
Batch update node positions (used for layout and parent-child movement).

**Request Body:**
```json
{
  "updates": [
    {
      "id": "uuid",
      "position_x": 100,
      "position_y": 200
    }
  ]
}
```

**Response:**
```json
{
  "message": "Batch update successful",
  "updated": 5
}
```

---

### Connections

#### GET /api/connections?canvas_id=:id
List all connections (edges) for a specific canvas.

**Query Parameters:**
- `canvas_id` (required) - Canvas UUID

**Response:**
```json
[
  {
    "id": "uuid",
    "canvas_id": "uuid",
    "source_id": "uuid",
    "target_id": "uuid",
    "type": "default",
    "animated": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /api/connections
Create a new connection between nodes.

**Request Body:**
```json
{
  "canvas_id": "uuid",
  "source_id": "uuid",
  "target_id": "uuid",
  "type": "default",
  "animated": true
}
```

**Response:** `201 Created` - Returns created connection object

**Errors:**
- `400` - Canvas ID, source ID, and target ID are required

#### DELETE /api/connections/:id
Delete a connection.

**Response:**
```json
{
  "message": "Connection deleted successfully",
  "connection": { /* deleted connection object */ }
}
```

**Errors:**
- `404` - Connection not found

---

### Snapshots

#### GET /api/snapshots?canvas_id=:id
Get the last 5 snapshots for a canvas.

**Query Parameters:**
- `canvas_id` (required) - Canvas UUID

**Response:**
```json
[
  {
    "id": "uuid",
    "canvas_id": "uuid",
    "snapshot_data": {
      "nodes": [ /* array of nodes */ ],
      "edges": [ /* array of edges */ ],
      "viewport": { "x": 0, "y": 0, "zoom": 1 },
      "metadata": {
        "nodeCount": 10,
        "edgeCount": 5,
        "cardTypeCounts": { "rich_text": 5, "todo": 3 },
        "tags": ["tag1", "tag2"]
      }
    },
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /api/snapshots
Create a new canvas snapshot.

**Request Body:**
```json
{
  "canvas_id": "uuid",
  "snapshot_data": {
    "nodes": [],
    "edges": [],
    "viewport": { "x": 0, "y": 0, "zoom": 1 },
    "metadata": {}
  }
}
```

**Response:** `201 Created` - Returns created snapshot object

**Note:** Automatically keeps only the last 5 snapshots per canvas.

**Errors:**
- `400` - Canvas ID and snapshot data are required

#### DELETE /api/snapshots/:id
Delete a specific snapshot.

**Response:**
```json
{
  "message": "Snapshot deleted successfully"
}
```

**Errors:**
- `404` - Snapshot not found

## Development

### Start Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

### Start Production Server
```bash
npm start
```

## Environment Variables

See `../.env` for configuration:
- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `PORT` - API server port (default: 3000)

---

## Card Types

Valid `card_type` values and their data structures:

### rich_text
```json
{
  "card_type": "rich_text",
  "title": "Note Title",
  "card_data": {
    "content": "Markdown content here"
  },
  "tags": ["tag1", "tag2"]
}
```

### todo
```json
{
  "card_type": "todo",
  "title": "Todo List",
  "card_data": {
    "items": [
      { "id": "uuid", "text": "Task 1", "completed": false },
      { "id": "uuid", "text": "Task 2", "completed": true }
    ],
    "progress": 50
  },
  "tags": []
}
```

### video
```json
{
  "card_type": "video",
  "title": "Video Title",
  "card_data": {
    "videoUrl": "https://youtube.com/watch?v=...",
    "videoId": "video_id",
    "thumbnail": "thumbnail_url"
  },
  "tags": []
}
```

### link
```json
{
  "card_type": "link",
  "title": "Link Title",
  "card_data": {
    "url": "https://example.com",
    "description": "Link description",
    "favicon": "favicon_url"
  },
  "tags": []
}
```

### reminder
```json
{
  "card_type": "reminder",
  "title": "Reminder Title",
  "card_data": {
    "reminderDate": "2024-01-01",
    "reminderTime": "14:30",
    "description": "Reminder description"
  },
  "tags": []
}
```

---

## Error Handling

All endpoints return consistent error responses:

**Success Response:**
```json
{
  "data": { /* response data */ }
}
```

**Error Response:**
```json
{
  "error": "Error description",
  "message": "Detailed error message (development only)"
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200` | OK | Successful GET, PUT, DELETE |
| `201` | Created | Successful POST |
| `400` | Bad Request | Invalid request body or parameters |
| `404` | Not Found | Resource doesn't exist |
| `500` | Internal Server Error | Database or server error |

---

## Database Schema

### Tables

#### canvases
```sql
CREATE TABLE canvases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### nodes
```sql
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canvas_id UUID REFERENCES canvases(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
    content TEXT DEFAULT '',
    title TEXT,
    card_type TEXT DEFAULT 'rich_text',
    card_data JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    width FLOAT DEFAULT 300,
    height FLOAT DEFAULT 200,
    type TEXT DEFAULT 'custom',
    style JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### connections
```sql
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canvas_id UUID REFERENCES canvases(id) ON DELETE CASCADE,
    source_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    target_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    type TEXT DEFAULT 'default',
    animated BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### canvas_snapshots
```sql
CREATE TABLE canvas_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canvas_id UUID REFERENCES canvases(id) ON DELETE CASCADE,
    snapshot_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes

- `idx_nodes_canvas_id` - Fast node lookups by canvas
- `idx_nodes_card_type` - Filter nodes by type
- `idx_nodes_tags` - GIN index for tag searches
- `idx_nodes_card_data` - GIN index for JSONB queries
- `idx_nodes_title` - Text search on titles
- `idx_connections_canvas_id` - Fast connection lookups
- `idx_snapshots_canvas_id` - Fast snapshot lookups
- `idx_snapshots_created_at` - Ordered snapshot retrieval
