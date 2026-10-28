import client from './client';
import type {
  Auction,
  AuctionCreatePayload,
  AuctionFilters,
  AuctionPatchPayload,
  Bid,
  Category,
  PaginatedResponse,
} from './types';

export async function getCategories(): Promise<Category[]> {
  const { data } = await client.get<Category[]>('/categories/');
  return data;
}

export async function getAuctions(
  filters: AuctionFilters = {},
): Promise<PaginatedResponse<Auction>> {
  const params: Record<string, string> = {};
  if (filters.mine) params.mine = '1';
  if (filters.status) params.status = filters.status;
  if (filters.category) params.category = String(filters.category);
  if (filters.search) params.search = filters.search;
  if (filters.page && filters.page > 1) params.page = String(filters.page);
  const { data } = await client.get<PaginatedResponse<Auction>>('/auctions/', { params });
  return data;
}

export async function getAuction(id: number): Promise<Auction> {
  const { data } = await client.get<Auction>(`/auctions/${id}/`);
  return data;
}

export async function createAuction(payload: AuctionCreatePayload): Promise<Auction> {
  const { data } = await client.post<Auction>('/auctions/', payload);
  return data;
}

export async function patchAuction(id: number, payload: AuctionPatchPayload): Promise<Auction> {
  const { data } = await client.patch<Auction>(`/auctions/${id}/`, payload);
  return data;
}

export async function submitAuction(id: number): Promise<Auction> {
  const { data } = await client.post<Auction>(`/auctions/${id}/submit/`, {});
  return data;
}

export async function approveAuction(id: number, reason: string): Promise<Auction> {
  const { data } = await client.post<Auction>(`/auctions/${id}/approve/`, { reason });
  return data;
}

export async function rejectAuction(id: number, reason: string): Promise<Auction> {
  const { data } = await client.post<Auction>(`/auctions/${id}/reject/`, { reason });
  return data;
}

export async function getMyBids(auctionId: number): Promise<Bid[]> {
  const { data } = await client.get<Bid[]>(`/auctions/${auctionId}/bids/`);
  return data;
}

export async function placeBid(
  auctionId: number,
  amount_kopecks: number,
  idempotencyKey: string,
): Promise<Bid> {
  const { data } = await client.post<Bid>(
    `/auctions/${auctionId}/bids/`,
    { amount_kopecks },
    { headers: { 'Idempotency-Key': idempotencyKey } },
  );
  return data;
}
