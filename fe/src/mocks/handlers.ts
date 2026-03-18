import { authHandlers } from './authHandlers';
import { userHandlers } from './userHandlers';
import { rankingHandlers } from './rankingHandlers';

export const handlers = [
  ...authHandlers,
  ...userHandlers,
  ...rankingHandlers,
];
