import { authHandlers } from './authHandlers';
import { reviewHandlers } from './reviewHandlers';
import { userHandlers } from './userHandlers';
import { rankingHandlers } from './rankingHandlers';

export const handlers = [
  ...authHandlers,
  ...reviewHandlers,
  ...userHandlers,
  ...rankingHandlers,
];
