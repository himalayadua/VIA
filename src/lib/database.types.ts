export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      canvases: {
        Row: {
          id: string
          name: string
          description: string
          created_at: string
          updated_at: string
          user_id: string | null
        }
        Insert: {
          id?: string
          name: string
          description?: string
          created_at?: string
          updated_at?: string
          user_id?: string | null
        }
        Update: {
          id?: string
          name?: string
          description?: string
          created_at?: string
          updated_at?: string
          user_id?: string | null
        }
      }
      nodes: {
        Row: {
          id: string
          canvas_id: string
          parent_id: string | null
          content: string
          position_x: number
          position_y: number
          width: number
          height: number
          type: string
          style: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          canvas_id: string
          parent_id?: string | null
          content?: string
          position_x?: number
          position_y?: number
          width?: number
          height?: number
          type?: string
          style?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          canvas_id?: string
          parent_id?: string | null
          content?: string
          position_x?: number
          position_y?: number
          width?: number
          height?: number
          type?: string
          style?: Json
          created_at?: string
          updated_at?: string
        }
      }
      connections: {
        Row: {
          id: string
          canvas_id: string
          source_id: string
          target_id: string
          type: string
          animated: boolean
          style: Json
          created_at: string
        }
        Insert: {
          id?: string
          canvas_id: string
          source_id: string
          target_id: string
          type?: string
          animated?: boolean
          style?: Json
          created_at?: string
        }
        Update: {
          id?: string
          canvas_id?: string
          source_id?: string
          target_id?: string
          type?: string
          animated?: boolean
          style?: Json
          created_at?: string
        }
      }
      node_history: {
        Row: {
          id: string
          node_id: string
          canvas_id: string
          content: string | null
          position_x: number | null
          position_y: number | null
          action_type: string
          snapshot: Json
          created_at: string
        }
        Insert: {
          id?: string
          node_id: string
          canvas_id: string
          content?: string | null
          position_x?: number | null
          position_y?: number | null
          action_type: string
          snapshot?: Json
          created_at?: string
        }
        Update: {
          id?: string
          node_id?: string
          canvas_id?: string
          content?: string | null
          position_x?: number | null
          position_y?: number | null
          action_type?: string
          snapshot?: Json
          created_at?: string
        }
      }
    }
  }
}
