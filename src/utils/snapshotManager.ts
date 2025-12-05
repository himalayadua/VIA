import { Node, Edge } from 'reactflow';
import { api } from '../lib/api';
import { CardType } from '../types/cardTypes';

export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

export interface SnapshotMetadata {
  nodeCount: number;
  edgeCount: number;
  cardTypeCounts: Record<CardType, number>;
  tags: string[];
}

export interface CanvasSnapshot {
  id?: string;
  canvasId: string;
  timestamp: string;
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;
  metadata: SnapshotMetadata;
}

export class SnapshotManager {
  private maxSnapshots = 5;

  /**
   * Create a snapshot from current canvas state
   */
  createSnapshot(
    canvasId: string,
    nodes: Node[],
    edges: Edge[],
    viewport: Viewport
  ): CanvasSnapshot {
    const metadata = this.calculateMetadata(nodes, edges);

    return {
      canvasId,
      timestamp: new Date().toISOString(),
      nodes: JSON.parse(JSON.stringify(nodes)), // Deep clone
      edges: JSON.parse(JSON.stringify(edges)), // Deep clone
      viewport: { ...viewport },
      metadata
    };
  }

  /**
   * Calculate metadata for snapshot
   */
  private calculateMetadata(nodes: Node[], edges: Edge[]): SnapshotMetadata {
    // Initialize card type counts
    const cardTypeCounts: Record<CardType, number> = {
      [CardType.RICH_TEXT]: 0,
      [CardType.TODO]: 0,
      [CardType.VIDEO]: 0,
      [CardType.LINK]: 0,
      [CardType.REMINDER]: 0
    };

    // Extract all unique tags
    const tagsSet = new Set<string>();

    // Count nodes by card type and collect tags
    nodes.forEach(node => {
      const cardType = (node.data?.cardType as CardType) || CardType.RICH_TEXT;
      if (cardType in cardTypeCounts) {
        cardTypeCounts[cardType]++;
      }

      // Collect tags
      const nodeTags = node.data?.tags as string[] | undefined;
      if (Array.isArray(nodeTags)) {
        nodeTags.forEach(tag => tagsSet.add(tag));
      }
    });

    return {
      nodeCount: nodes.length,
      edgeCount: edges.length,
      cardTypeCounts,
      tags: Array.from(tagsSet).sort()
    };
  }

  /**
   * Save snapshot to database via API
   */
  async saveToDatabase(snapshot: CanvasSnapshot): Promise<void> {
    try {
      await api.createSnapshot({
        canvas_id: snapshot.canvasId,
        snapshot_data: {
          nodes: snapshot.nodes,
          edges: snapshot.edges,
          viewport: snapshot.viewport,
          metadata: snapshot.metadata
        }
      });
    } catch (error) {
      console.error('Failed to save snapshot:', error);
      throw error;
    }
  }

  /**
   * Get snapshots from database via API
   */
  async getSnapshots(canvasId: string): Promise<CanvasSnapshot[]> {
    try {
      const snapshots = await api.getSnapshots(canvasId);
      
      return snapshots.map((snapshot: any) => ({
        id: snapshot.id,
        canvasId: snapshot.canvas_id,
        timestamp: snapshot.created_at,
        nodes: snapshot.snapshot_data.nodes || [],
        edges: snapshot.snapshot_data.edges || [],
        viewport: snapshot.snapshot_data.viewport || { x: 0, y: 0, zoom: 1 },
        metadata: snapshot.snapshot_data.metadata || {
          nodeCount: 0,
          edgeCount: 0,
          cardTypeCounts: {
            [CardType.RICH_TEXT]: 0,
            [CardType.TODO]: 0,
            [CardType.VIDEO]: 0,
            [CardType.LINK]: 0,
            [CardType.REMINDER]: 0
          },
          tags: []
        }
      }));
    } catch (error) {
      console.error('Failed to get snapshots:', error);
      return [];
    }
  }

  /**
   * Load snapshots from database
   * Alias for getSnapshots for consistency with design doc
   */
  async loadFromDatabase(canvasId: string): Promise<CanvasSnapshot[]> {
    return this.getSnapshots(canvasId);
  }

  /**
   * Prune old snapshots (keep only last N)
   * Note: This is handled automatically by database trigger,
   * but this method is provided for manual cleanup if needed
   */
  async pruneOldSnapshots(canvasId: string): Promise<void> {
    try {
      const snapshots = await this.getSnapshots(canvasId);
      
      // If more than maxSnapshots, delete oldest ones
      if (snapshots.length > this.maxSnapshots) {
        const snapshotsToDelete = snapshots
          .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .slice(this.maxSnapshots);

        for (const snapshot of snapshotsToDelete) {
          if (snapshot.id) {
            await api.deleteSnapshot(snapshot.id);
          }
        }
      }
    } catch (error) {
      console.error('Failed to prune old snapshots:', error);
    }
  }

  /**
   * Get max snapshots limit
   */
  getMaxSnapshots(): number {
    return this.maxSnapshots;
  }
}

// Export singleton instance
export const snapshotManager = new SnapshotManager();
export default snapshotManager;
