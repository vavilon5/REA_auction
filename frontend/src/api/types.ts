export type AuctionStatus =
  | 'draft'
  | 'review'
  | 'rejected'
  | 'open'
  | 'closed'
  | 'paused';

export interface User {
  id: number;
  username: string;
  can_moderate: boolean;
}

export interface Category {
  id: number;
  name: string;
}

export interface Auction {
  id: number;
  owner_id: number;
  category: number;
  title: string;
  description: string;
  budget_kopecks: number;
  ends_at: string;
  due_at: string;
  status: AuctionStatus;
  moderation_reason: string;
  winner_id: number | null;
  payment_kopecks: number | null;
  closed_at: string | null;
}

export interface Bid {
  id: number;
  auction_id: number;
  amount_kopecks: number;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AuctionFilters {
  mine?: boolean;
  status?: AuctionStatus;
  category?: number;
  search?: string;
  page?: number;
}

export interface AuctionCreatePayload {
  category: number;
  title: string;
  description: string;
  budget_kopecks: number;
  ends_at: string;
  due_at: string;
}

export type AuctionPatchPayload = Partial<AuctionCreatePayload>;
