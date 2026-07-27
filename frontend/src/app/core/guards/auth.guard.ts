import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Functional route guard. Used on routes like /library that should
 * redirect to /login if there's no token. Kept intentionally simple —
 * it only checks token *presence*, not validity; an invalid/expired
 * token still hits the API and gets handled by the interceptor's
 * refresh-or-logout logic.
 */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isLoggedIn()) {
    return true;
  }
  router.navigate(['/login']);
  return false;
};
