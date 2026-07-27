import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';

/**
 * Central place where every app-wide provider is registered.
 * Using Angular's standalone API (no NgModule) keeps bootstrapping
 * explicit and easy to extend: add withInterceptors() entries here
 * once the JWT auth interceptor is built in Phase 2.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
};