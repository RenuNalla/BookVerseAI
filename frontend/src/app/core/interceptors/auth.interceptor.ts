import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Functional interceptor (Angular 15+ style, used via withInterceptors()
 * in app.config.ts). Two jobs:
 *   1. Attach "Authorization: Bearer <token>" to every outgoing request.
 *   2. On a 401, try ONE silent refresh; if that also fails, log the user
 *      out rather than looping forever.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.getAccessToken();

  const authedReq = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(authedReq).pipe(
    catchError((err: HttpErrorResponse) => {
      const isAuthEndpoint = req.url.includes('/auth/login') || req.url.includes('/auth/register');
      if (err.status === 401 && auth.getRefreshToken() && !isAuthEndpoint) {
        return auth.refreshAccessToken().pipe(
          switchMap(({ access_token }) => {
            const retried = req.clone({
              setHeaders: { Authorization: `Bearer ${access_token}` },
            });
            return next(retried);
          }),
          catchError((refreshErr) => {
            auth.logout();
            return throwError(() => refreshErr);
          })
        );
      }
      return throwError(() => err);
    })
  );
};
