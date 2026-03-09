export interface BaseResponse<T> {
  status: string;
  code: string;
  message: string;
  data: T;
}

export interface ErrorResponse {
  status: string;
  code: string;
  message: string;
}