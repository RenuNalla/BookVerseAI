import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  dependencies: { database: string };
}

/**
 * Wraps the single GET /health call. Any component that needs to know
 * "is the backend up" injects this instead of calling HttpClient directly
 * — keeps the API URL and response shape in exactly one place.
 */
@Injectable({ providedIn: 'root' })
export class HealthService {
  constructor(private http: HttpClient) {}

  check(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${environment.apiBaseUrl}/health`);
  }
}