import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_verified: boolean;
  created_at: string;
}

interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

const ACCESS_KEY = 'bp_access_token';
const REFRESH_KEY = 'bp_refresh_token';

/**
 * Single source of truth for auth state on the frontend. Tokens are kept
 * in localStorage (simplest option for Phase 2); the `currentUser` signal
 * lets any component reactively show/hide UI based on login state without
 * each one re-fetching /me itself.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  currentUser = signal<User | null>(null);

  constructor(private http: HttpClient) {}

  register(payload: { email: string; full_name: string; password: string }): Observable<User> {
    return this.http.post<User>(`${environment.apiBaseUrl}/auth/register`, payload);
  }

  login(payload: { email: string; password: string }): Observable<TokenPair> {
    return this.http.post<TokenPair>(`${environment.apiBaseUrl}/auth/login`, payload).pipe(
      tap((tokens) => this.storeTokens(tokens))
    );
  }

  fetchCurrentUser(): Observable<User> {
    return this.http.get<User>(`${environment.apiBaseUrl}/auth/me`).pipe(
      tap((user) => this.currentUser.set(user))
    );
  }

  refreshAccessToken(): Observable<{ access_token: string }> {
    return this.http
      .post<{ access_token: string }>(`${environment.apiBaseUrl}/auth/refresh`, {
        refresh_token: this.getRefreshToken(),
      })
      .pipe(tap((res) => localStorage.setItem(ACCESS_KEY, res.access_token)));
  }

  logout(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    this.currentUser.set(null);
  }

  isLoggedIn(): boolean {
    return !!this.getAccessToken();
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  private storeTokens(tokens: TokenPair): void {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  }
}